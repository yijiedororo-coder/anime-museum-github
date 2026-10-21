"""Read-only source check. Fresh responses are kept apart from the publication baseline."""
import csv, io, json, re, hashlib, urllib.request, concurrent.futures, difflib, sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from lxml import html

ROOT=Path(__file__).resolve().parent.parent
NOW=datetime.now(ZoneInfo('Asia/Tokyo'));DATE=NOW.date().isoformat()
OUT=ROOT/'tools/zuta-monitor'/DATE;OUT.mkdir(parents=True,exist_ok=True)
BASE=ROOT/'tools/zuta-archive'
work=json.loads((ROOT/'data/gakumas-data.js').read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))['items'][0]
known={a['url']:a for a in work['articleIndex']};errors=[];responses={}
def clean(t):return re.sub(r'\s+',' ',t).strip()
def path(u):return OUT/(hashlib.sha256(u.encode()).hexdigest()+'.html')
def fetch(u):
    try:
        if '--cached' in sys.argv:
            text=path(u).read_text(encoding='utf-8')
            responses[u]={'cacheReanalysis':True,'sha256':hashlib.sha256(text.encode()).hexdigest()}
            return u,text
        req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'})
        with urllib.request.urlopen(req,timeout=35) as r:
            raw=r.read();responses[u]={'status':r.status,'lastModified':r.headers.get('Last-Modified'),'sha256':hashlib.sha256(raw).hexdigest()}
        text=raw.decode('utf-8-sig');path(u).write_text(text,encoding='utf-8');return u,text
    except Exception as e:errors.append({'url':u,'reason':str(e)});return u,None
def parallel(urls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:yield from pool.map(fetch,sorted(set(urls)))

sourceurls=['https://zutapoke.com/goodsdb/','https://zutapoke.com/wp-content/uploads/goodsdbcsv/goodsdb.csv','https://zutapoke.com/wp-content/uploads/goodsdbcsv/shopset.csv','https://zutapoke.com/category/merchandise/']
initial=dict(parallel(sourceurls))
csvChanges={};freshRows=[]
for name,key in [('goodsdb','No'),('shopset','shop')]:
    u=f'https://zutapoke.com/wp-content/uploads/goodsdbcsv/{name}.csv';text=initial.get(u)
    if text is None:continue
    (OUT/(name+'.csv')).write_text(text,encoding='utf-8-sig')
    current=list(csv.DictReader(io.StringIO(text)));old=list(csv.DictReader((ROOT/'tools'/(name+'.csv')).open(encoding='utf-8-sig')))
    previous={r[key]:r for r in old};latest={r[key]:r for r in current};changed=[];cosmetic=[]
    if name=='goodsdb':freshRows=current
    for number,row in latest.items():
        if number not in previous:continue
        changes={k:{'old':previous[number].get(k,''),'new':v} for k,v in row.items() if v.strip()!=previous[number].get(k,'').strip()}
        meaningful={k:v for k,v in changes.items() if not k.endswith('_pick') and k!='pick_flag'}
        if meaningful:changed.append({'id':number,'name':row.get('name'),'fields':meaningful})
        elif changes:cosmetic.append({'id':number,'fields':changes})
    csvChanges[name]={'rows':len(current),'new':[latest[n] for n in latest if n not in previous],'removed':[n for n in previous if n not in latest],'changed':changed,'promotionalOnly':cosmetic,'sameBytes':(OUT/(name+'.csv')).read_bytes()==(ROOT/'tools'/(name+'.csv')).read_bytes()}
print(json.dumps({'csv':{k:{'rows':v['rows'],'new':len(v['new']),'changed':len(v['changed']),'removed':len(v['removed']),'promotionalOnly':len(v['promotionalOnly'])} for k,v in csvChanges.items()}},ensure_ascii=False),flush=True)

pageurls=set();articleTitles={}
first=initial.get('https://zutapoke.com/category/merchandise/')
if first:
    d=html.fromstring(first);pageurls={'https://zutapoke.com/category/merchandise/'}
    last=max([int(re.search(r'/page/(\d+)/',u)[1]) for u in d.xpath('//a/@href') if re.search(r'/category/merchandise/page/\d+/',u)] or [1])
    pageurls.update(f'https://zutapoke.com/category/merchandise/page/{n}/' for n in range(2,last+1))
    for u,text in [('https://zutapoke.com/category/merchandise/',first),*parallel(pageurls-{'https://zutapoke.com/category/merchandise/'})]:
        if text is None:continue
        d=html.fromstring(text)
        for a in d.xpath('//a[contains(@class,"p-postList__link")]'):
            url=a.get('href');ts=a.xpath('.//*[contains(@class,"p-postList__title")]')
            if url and re.match(r'https://zutapoke.com/\d+/$',url):articleTitles[url]=clean(ts[0].text_content() if ts else a.text_content())

def content(raw):
    d=html.fromstring(raw);body=d.xpath('//main/article/*[contains(concat(" ",normalize-space(@class)," ")," post_content ")]')
    if len(body)!=1:raise ValueError('Expected exactly one main article body')
    b=body[0]
    for x in b.xpath('.//script|.//style|.//ins'):x.drop_tree()
    text=clean(b.text_content());links=list(dict.fromkeys(b.xpath('.//a/@href')));images=list(dict.fromkeys(b.xpath('.//img/@data-src|.//img/@src')))
    return {'text':text,'links':links,'images':images,'headings':[clean(x.text_content()) for x in b.xpath('.//h2|.//h3|.//h4')]}
changes=[];missingBaseline=[];newArticles=[u for u in articleTitles if u not in known]
for u,text in parallel(set(articleTitles)|set(known)):
    if text is None:continue
    previous=BASE/(hashlib.sha256(u.encode()).hexdigest()+'.html');current=content(text)
    if not previous.exists():missingBaseline.append(u);continue
    old=content(previous.read_text(encoding='utf-8'))
    if current!=old:
        tdiff=list(difflib.unified_diff(old['text'].split(' '),current['text'].split(' '),n=4))
        changes.append({'url':u,'title':articleTitles.get(u,known.get(u,{}).get('title','')),'textChanged':current['text']!=old['text'],'headingsChanged':current['headings']!=old['headings'],'linksAdded':[v for v in current['links'] if v not in old['links']],'linksRemoved':[v for v in old['links'] if v not in current['links']],'imagesAdded':[v for v in current['images'] if v not in old['images']],'textDiff':tdiff[:350]})

sourceIds={r['No'] for r in freshRows};museumIds={n for g in work['merch'] for n in g.get('sourceRecordIds',[])}
report={'checkedAt':NOW.isoformat(timespec='seconds'),'freshResponses':len(responses),'archivePages':len(pageurls),'articlesChecked':len(set(articleTitles)|set(known)),'categoryArticles':len(articleTitles),'newArticles':newArticles,'missingBaseline':missingBaseline,'csvChanges':csvChanges,'articleChanges':changes,'sourceRowsNotInMuseum':sorted(sourceIds-museumIds),'museumRowsAbsentFromSource':sorted(museumIds-sourceIds),'errors':errors,'responses':responses}
(OUT/'probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['responses','csvChanges','articleChanges']}|{'articleChanges':[{'url':x['url'],'title':x['title']} for x in changes],'changedCSV':{k:len(v['changed']) for k,v in csvChanges.items()}},ensure_ascii=False),flush=True)
