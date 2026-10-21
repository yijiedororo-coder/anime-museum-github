"""Research the current public article updates without changing museum records."""
import concurrent.futures, hashlib, json, re, urllib.request
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse, urlunparse, urlencode
from lxml import html

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'tools/zuta-monitor/2026-10-19';DETAILS=OUT/'details';DETAILS.mkdir(exist_ok=True)
work=json.loads((ROOT/'data/gakumas-data.js').read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))['items'][0]
def clean(t):return re.sub(r'\s+',' ',t).strip()
def norm(t):return re.sub(r'[\s\[\]【】〖〗（）()・·‐‑–—-]','',t).lower()
def canon(u):
    for _ in range(6):
        q=parse_qs(urlparse(u).query);target=next((q[k][0] for k in ['a8ejpredirect','lsurl','lurl','pc','vc_url','goods_url'] if k in q),None)
        if not target:break
        u=target
    if 'neowing.co.jp/aff/click.cgi/' in u:
        suffix=unquote(urlparse(u).path.split('/')[-1])
        if suffix.startswith(('product/','guide/')):u='https://www.neowing.co.jp/'+suffix
    return u.replace('http://','https://')
def identity(u):
    u=canon(u);p=urlparse(u)
    if any(s in u.lower() for s in ['/search','/mall/','/shopbrand/','/item/tag/']):return None
    if len(p.path.strip('/'))<5:return None
    if 'amazon.' in p.netloc:
        m=re.search(r'/dp/([A-Z0-9]+)',p.path)
        return p.netloc+'/dp/'+m[1] if m else None
    return p.netloc+p.path.rstrip('/')+('?' + urlencode({k:v for k,v in parse_qs(p.query).items() if k in ['product_id','goods_id']},doseq=True) if any(k in parse_qs(p.query) for k in ['product_id','goods_id']) else '')
def imagekey(u):return re.sub(r'-\d+x\d+(?=\.[a-zA-Z]+$)','',u).replace('http://','https://')
def doc(u):return html.fromstring((OUT/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
def body(u):return doc(u).xpath('//main/article/div[@class="post_content"]')[0]
def tabnodes(u):return body(u).xpath('./div[contains(@class,"swell-block-tab")]/div[contains(@class,"c-tabBody")]/div[contains(@class,"c-tabBody__item")]')

# Existing source photos give an exact per-character mapping for the two new shops.
byimage={g['image']:g for g in work['merch'] if g['id'].startswith('zuta-article-28183-')}
curtain=[]
for shop,t in zip(['NeoWing','カーテン魂','Animate'],tabnodes('https://zutapoke.com/28183/')):
    if shop=='カーテン魂':continue
    current=None
    for a in t.xpath('.//a[@href]'):
        images=a.xpath('.//img/@data-src')
        if images:
            assert images[0] in byimage
            current=byimage[images[0]]
        if current is None:continue
        u=canon(a.get('href'))
        if any(c['id']==current['id'] and c['shop']==shop and c['url']==u for c in curtain):continue
        size=clean(a.text_content())
        curtain.append({'id':current['id'],'shop':shop,'url':u,'originalUrl':a.get('href'),'size':size,'expectedName':current['originalName'],'character':current['characters']})
assert len({c['id'] for c in curtain if c['shop']=='NeoWing'})==51
assert len({c['id'] for c in curtain if c['shop']=='Animate'})==51

figures=[]
for c in body('https://zutapoke.com/13353/').xpath('.//article[contains(@class,"gakumas-figure-card")]'):
    name=clean(c.xpath('.//h3')[0].text_content())
    parent=c.getparent();section=parent.getparent();heads=section.xpath('./h2')
    if not heads:heads=c.xpath('preceding::h2[1]')
    status=clean(heads[0].text_content()) if heads else ''
    ps=[clean(p.text_content()) for p in c.xpath('./p')]
    links=[{'label':clean(a.text_content()),'url':canon(a.get('href')),'originalUrl':a.get('href')} for a in c.xpath('.//a[@href]')]
    images=list(dict.fromkeys(c.xpath('.//img/@data-src')))
    maker=next((p.split('：',1)[1] for p in ps if p.startswith('メーカー：')),'来源未标注')
    dates=[p for p in ps if p.startswith(('発売日：','登場日：','発売予定：','予約開始：'))]
    note=clean(' '.join(c.xpath('.//*[contains(@class,"__notes")]//text()')))
    figures.append({'name':name,'status':status,'maker':maker,'facts':ps,'dates':dates,'images':images,'links':links,'notes':note})
assert len(figures)==95
for f in figures:
    ik={imagekey(u) for u in f['images']};lk={identity(v['url']) for v in f['links']}-{None}
    strong=[]
    for i,g in enumerate(work['merch']):
        gi={imagekey(u) for u in [g.get('image',''),g.get('imageSource',''),*g.get('images',[])]}
        gl={identity(c['url']) for c in g['channels']}-{None}
        reasons=[]
        if ik&gi:reasons.append('same source image')
        if lk&gl:reasons.append('same product URL')
        if norm(f['name'])==norm(g['name']) or norm(f['name'])==norm(g.get('originalName','')):reasons.append('same name')
        if reasons:strong.append({'index':i,'id':g['id'],'name':g['name'],'reasons':reasons})
    f['museumMatches']=strong

def fetch(u):
    file=DETAILS/(hashlib.sha256(u.encode()).hexdigest()+'.html')
    if file.exists():return file.read_text(encoding='utf-8')
    with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'}),timeout=35) as r:
        text=r.read().decode(r.headers.get_content_charset() or 'utf-8',errors='replace')
    file.write_text(text,encoding='utf-8');return text
def check(c):
    c=dict(c)
    try:
        d=html.fromstring(fetch(c['url']));title=clean(' '.join(d.xpath('//title/text()')))
        # A source typo must never become a different character's buying link.
        valid=norm(c['character']) in norm(title) and ('学園' in title or '学マス' in title)
        c.update({'title':title,'valid':valid})
        if c['size'] in ['Mサイズ','Lサイズ','XLサイズ'] and c['size'] not in title:c['valid']=False
    except Exception as e:c.update({'valid':False,'error':str(e)})
    return c
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:curtain=list(pool.map(check,curtain))
result={'checkedAt':'2026-10-19','curtainLinks':curtain,'figures':figures}
(OUT/'research.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'curtainLinks':len(curtain),'verified':sum(c['valid'] for c in curtain),'invalid':[c for c in curtain if not c['valid']],'figureRecords':len(figures),'figureMatches':sum(bool(f['museumMatches']) for f in figures),'multipleMatches':sum(len(f['museumMatches'])>1 for f in figures),'unmatched':[f['name'] for f in figures if not f['museumMatches']]},ensure_ascii=False))
