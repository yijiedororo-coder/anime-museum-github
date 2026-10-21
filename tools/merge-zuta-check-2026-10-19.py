"""Merge researched changes; retain all original records, ordering and quoted facts."""
import copy,csv,hashlib,json,re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse,parse_qs,urlencode
from lxml import html

ROOT=Path(__file__).resolve().parent.parent;DATE='2026-10-19';CACHE=ROOT/'tools/zuta-monitor'/DATE
research=json.loads((CACHE/'research.json').read_text(encoding='utf-8'));probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'))
assert not probe['errors'] and all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
backup=CACHE/'before-update';backup.mkdir(exist_ok=True)
for name in ['gakumas-data.js','gakumas-products.csv','gakumas-article-index.json','gakumas-collection-report.json']:
    if not (backup/name).exists():(backup/name).write_bytes((ROOT/'data'/name).read_bytes())
path=ROOT/'data/gakumas-data.js';data=json.loads(path.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
before=copy.deepcopy(data);w=data['items'][0];old=before['items'][0];byid={g['id']:g for g in w['merch']}
assert w['collectionReport']['checkedAt']=='2026-10-15'
changed=set();newids=[];anomalies=[];unverified=[]
def clean(t):return re.sub(r'\s+',' ',t).strip()
def norm(t):return re.sub(r'\s+','',t).lower()
def doc(u):return html.fromstring((CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
def history(g):
    if g['id'] in changed:return
    g.setdefault('history',[]).append({k:copy.deepcopy(g.get(k)) for k in ['checkedAt','price','releaseDate','image','images','channels','description','availability','manufacturer','specifications']})
    changed.add(g['id']);g['checkedAt']=DATE
def ident(u):
    p=urlparse(u);q=parse_qs(p.query)
    if any(v in u.lower() for v in ['/search','/mall/','/shopbrand/']):return u
    return p.netloc+p.path.rstrip('/')+('?' + urlencode({k:v for k,v in q.items() if k in ['product_id','goods_id']},doseq=True) if any(k in q for k in ['product_id','goods_id']) else '')
def channel(c):
    u=c['url'];host=urlparse(u).netloc
    if not u.startswith('https://'):return None
    source=c['label'].replace('で見る','').strip()
    names={'ネオウィング':'NeoWing','アニメイト':'Animate','駿河屋':'骏河屋','楽天市場':'乐天市场'}
    name=names.get(source,source) or '来源销售链接'
    if 'books.rakuten.co.jp' in host:name='楽天ブックス'
    if 'dmm.com' in host:
        if name=='NeoWing':
            anomalies.append('汇总页把NeoWing按钮指向DMM，保留原始记录并排除错误的购买渠道归属。');return None
        name='DMM'
    if any(x in u.lower() for x in ['/search','/mall/','search_word=','keywords=','searchword=']):kind='搜索页（本系列共用，需确认具体款式）'
    elif not urlparse(u).path.strip('/'):kind='商店入口'
    elif any(x in host for x in ['bsp-prize','1kuji','goodsmile','idolmaster-official','bushiroad-creative','bandaispirits','bandai-hobby']):kind='官方商品资料 / 发布信息';name='官方商品资料'
    elif 'x.com' in host or 'twitter.com' in host:kind='官方资料 / 发布信息'
    else:kind='商品页（来源列出；未逐一核对店内规格）'
    return {'name':name,'url':u,'linkType':kind,'originalUrl':c.get('originalUrl',u),'sourceNote':DATE+'按来源汇总页面记录；不代表实时库存。'}
def appendchannels(g,values):
    seen={ident(c['url']) for c in g['channels']}
    for c in values:
        if c and ident(c['url']) not in seen:g['channels'].append(c);seen.add(ident(c['url']))

# Two new shops are mapped through the exact retained per-character article photos.
prices={'服饰':'7,084円','立牌':'4,048円','海报 / 摆件':'4,048円','生活 / 应援':'2,732円'}
for g in [g for g in w['merch'] if g['id'].startswith('zuta-article-28183-')]:
    history(g);entries=[c for c in research['curtainLinks'] if c['id']==g['id']]
    neo=next(c for c in entries if c['shop']=='NeoWing');assert neo['valid']
    page=html.fromstring((CACHE/'details'/(hashlib.sha256(neo['url'].encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
    dates=page.xpath('//*[@itemprop="releaseDate"]//text()');release=clean(' '.join(dates)) or '来源未标注'
    g['price'] += '；'+DATE+'来源新增NeoWing报价：'+prices[g['category']]
    g['releaseDate'] += '；NeoWing本次标注：'+release
    g.setdefault('sourceObservations',[]).append({'sourceName':'NeoWing商品页','sourceUrl':neo['url'],'releaseDate':release,'price':prices[g['category']]+'（原文章列价；不代表实时库存）','size':g.get('size','来源未标注'),'checkedAt':DATE})
    for c in entries:
        size=c['size']
        if 'fulltshirt' in g['id'] and not size:size='Mサイズ'
        if c['shop']=='Animate':
            kind='商品页（来源图示对应'+('；'+size if size else '')+'；店内核查受限）'
            note='按来源图片映射角色及尺码；自动访问出现跳转循环或动态空页，未确认店内规格和库存。'
            unverified.append(c['url'])
        else:
            kind='商品页（已核对角色'+('；M尺码' if 'fulltshirt' in g['id'] else '')+'）';note='已核对NeoWing页面商品名；报价及发售月份为本次来源快照。'
        appendchannels(g,[{'name':c['shop'],'url':c['url'],'linkType':kind,'sourceNote':DATE+' '+note,'originalUrl':c['originalUrl']}])
    g['description']+=' '+DATE+'新增NeoWing与Animate购买渠道；NeoWing标注'+release+'，与此前厂商直营的起售日、受注批次分别记录。Animate链接保留原文章的角色与尺码对应关系，但店内页面核查受限。'
    g['availability']='厂商直营规格与链接保留2026-10-15核查记录；2026-10-19已核对NeoWing，Animate店内页面核对受限。库存与订单状态请在商店确认。'

# A manually reviewed identity map distinguishes editions, scale and lottery parts.
manual={11:'zuta-db-3369',14:'zuta-db-114',24:'zuta-db-121',25:'zuta-db-120',40:'zuta-db-125',55:'zuta-db-136',81:'zuta-db-145',82:'zuta-db-144',84:'zuta-db-3368'}
series={86:list(range(146,152)),88:list(range(160,166)),89:list(range(166,172)),90:list(range(152,156)),91:list(range(156,160))}
knownchars=['花海咲季','月村手毬','藤田ことね','雨夜燕','有村麻央','葛城リーリヤ','倉本千奈','紫雲清夏','篠澤広','十王星南','秦谷美鈴','花海佑芽','姫崎莉波']
figuremap=[]
for i,f in enumerate(research['figures']):
    if i in manual:targets=[manual[i]]
    elif i in series:targets=['zuta-db-'+str(n) for n in series[i]]
    else:targets=[m['id'] for m in f['museumMatches']]
    assert len(targets)<=1 or i in series
    date=' / '.join(p.split('：',1)[1] for p in f['facts'] if p.startswith('発売日：')) or '来源未公开发售日期'
    maker=f['maker'];status='来源分组（'+DATE+'快照）：'+f['status']+'；不代表实时库存或可预约状态。'
    values=[channel(c) for c in f['links']]
    specs=f['facts']+([f['notes']] if f['notes'] else [])+[status]
    if targets:
        for id in targets:
            g=byid[id];history(g)
            g['releaseDate']=g.get('releaseDate','来源未标注')+'；'+DATE+'系列汇总标注：'+date
            g.setdefault('sourceObservations',[]).append({'sourceName':'学マスまとめ · 手办汇总（系列记录）','sourceUrl':'https://zutapoke.com/13353/','releaseDate':date,'price':'本次汇总未列单品报价；旧报价保留在主档案','size':g.get('size','本页未列尺寸'),'checkedAt':DATE,'name':f['name'],'sourceStatus':f['status']})
            g['images']=list(dict.fromkeys([*g.get('images',[]),*f['images']]))
            g.setdefault('specifications',[]).extend(specs)
            if maker!='来源未标注' and not g.get('manufacturer'):g['manufacturer']=maker
            g['description']+=' '+DATE+'对照更新后的手办汇总补充日期、厂商和渠道。来源系列名：'+f['name']+'。系列合照仅供参照，原单品图片和报价保留。'
            appendchannels(g,values)
    else:
        id='zuta-figure-13353-'+hashlib.sha256(norm(f['name']).encode()).hexdigest()[:12]
        assert id not in byid
        chars=','.join(c for c in knownchars if c in norm(f['name'])) or '来源未逐一标注角色；见系列商品图'
        g={'id':id,'kind':'merch','name':f['name'],'originalName':f['name'],'category':'手办','originalType':'フィギュア'+(',ESPRESTO' if 'ESPRESTO' in f['name'] else ''),'characters':chars,'manufacturer':maker,'releaseDate':date,'price':'来源未标价；以渠道页面的具体规格与报价为准','description':'根据本次重整的手办汇总补充入库，包含已发行、预告与历史款。日期、厂商及来源分组如实保留；来源的“発売中”“予約受付中”等分类不代表实时库存。未公开的价格与尺寸不作推测。','image':f['images'][0],'imageSource':f['images'][0],'images':f['images'],'sourceUrl':'https://zutapoke.com/13353/','sourceName':'学マスまとめ · 手办汇总','checkedAt':DATE,'specifications':specs,'channels':[],'availability':status}
        appendchannels(g,values);w['merch'].append(g);byid[id]=g;newids.append(id);targets=[id]
    figuremap.append({'sourceName':f['name'],'productIds':targets,'seriesReference':i in series})
    if i==85:
        # BOX and capsule versions have different dates, prices and pack sizes.
        g=byid[targets[0]];g.update({'name':'むぎゅみにコレクションフィギュア vol.1 · 6个装BOX','manufacturer':'ブシロードクリエイティブ','productBrand':'BUSHIROAD THE BOX','releaseDate':'DMM：2027年3月末前预计；汇总文章：2027年3月26日','price':'6个装BOX定价3,960円；来源报价：DMM 2,970円、NeoWing 3,049円（购买链接待确认）、楽天ブックス与Animate 3,960円','size':'约50mm','sourceUrl':'https://zutapoke.com/28368/','sourceName':'学マスまとめ / DMM商品资料','verificationUrl':'https://www.dmm.com/mono/hobby/-/detail/=/cid=c261002216/','image':'https://zutapoke.com/wp-content/uploads/2026/10/image-74.png','imageSource':'https://zutapoke.com/wp-content/uploads/2026/10/image-74.png'})
        g['specifications']+=['DMM商品标题：全5种，1BOX含6个。','材质：本体PVC、底座ABS；JAN 4570194429957。','本档案为BOX销售版本；同名胶囊单抽版本不合并计算。','NeoWing栏的原链接实际指向DMM；仅保留原报价，不将错误跳转列为NeoWing购买入口。']
        g['description']+=' DMM公开商品页已核对BOX数量、尺寸、材质及发售月份；不同来源日期并列保留。'

def intel(u,sections=None):
    d=doc(u);b=d.xpath('//main/article/div[@class="post_content"]')[0]
    return {'title':clean(d.xpath('//h1')[0].text_content()),'url':u,'sections':sections if sections is not None else [clean(h.text_content()) for h in b.xpath('.//h2|.//h3|.//h4')],'prices':list(dict.fromkeys(re.findall(r'[\d,]+円',clean(b.text_content())))),'dates':list(dict.fromkeys(re.findall(r'\d{4}年\d{1,2}月(?:\d{1,2}日)?',clean(b.text_content())))),'image':next(iter(d.xpath('//meta[@property="og:image"]/@content')),''),'checkedAt':DATE}
for u in ['https://zutapoke.com/13353/','https://zutapoke.com/28183/']:
    a=next(a for a in w['articleIndex'] if a['url']==u);a.setdefault('history',[]).append({k:copy.deepcopy(v) for k,v in a.items() if k!='history'})
    fresh=intel(u);manualnotes=[s for s in a['sections'] if re.match(r'20\d\d-\d\d-\d\d',s)]
    for k in ['title','prices','dates','image','checkedAt']:a[k]=fresh[k]
    a['sections']=fresh['sections']+manualnotes
    if u.endswith('/28183/'):
        a['sections']+=['新增NeoWing报价：T恤7,084日元、立牌及B2挂画4,048日元、靠垫套2,732日元。','51款新增NeoWing及Animate渠道；T恤保留不同尺码入口。NeoWing页面标注2027年2月发售，与厂商直营批次分开记录。','Animate页面自动核查受限，来源图示角色与尺码链接已保留并明确标注。']
    else:a['sections']+=['本次整理95条手办与系列记录；已与馆内商品核对合并，保留历史报价和编号。']
for u in ['https://zutapoke.com/28368/','https://zutapoke.com/28471/']:
    assert not any(a['url']==u for a in w['articleIndex'])
    a=intel(u)
    if u.endswith('/28368/'):a['sections']+=['BOX版本全5种、1BOX含6个；定价3,960日元。DMM来源报价2,970日元，NeoWing原文报价3,049日元。','NeoWing按钮误链到DMM，正确购买入口尚未确认；不把不同规格或胶囊版并为同一报价。']
    else:a['sections']=['2026年10月18日周报；与周边相关的新情报：むぎゅみにBOX、GOLD RUSH 8卷店铺特典、カーテン魂新周边及手办汇总更新。','周报中的预约、活动和发售提示为来源当期记录，具体费用与状态以各原始商品页为准。']
    w['articleIndex'].append(a)
names={c['name'] for c in w['channelSummary']}
for g in w['merch']:
    for c in g['channels']:
        if c['name'] not in names:
            w['channelSummary'].append({'name':c['name'],'description':'来源列出的购买或资料渠道；商品页、搜索入口及核查限制见单品标注。','examples':list(dict.fromkeys(x['category'] for x in w['merch'] if any(v['name']==c['name'] for v in x['channels'])))[:6],'sourceUrl':'https://zutapoke.com/13353/'});names.add(c['name'])
report=w['collectionReport'];report.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':len(newids),'changedProducts':len(changed),'newArticles':2,'changedArticles':2}});w['retrievedAt']=DATE
assert [g['id'] for g in w['merch'][:len(old['merch'])]]==[g['id'] for g in old['merch']]
for prev,now in zip(old['merch'],w['merch']):
    for key in ['id','name','image','sourceUrl']:assert now[key]==prev[key],(prev['id'],key)
    assert now['channels'][:len(prev['channels'])]==prev['channels']
    if prev['id'] not in changed:assert now==prev
    else:
        assert prev['price'] in now['price'] and prev.get('releaseDate','') in now.get('releaseDate','')
path.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
(ROOT/'data/gakumas-article-index.json').write_text(json.dumps(w['articleIndex'],ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'data/gakumas-collection-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    wr=csv.writer(fp);wr.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
    for g in w['merch']:
        vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g['price'],g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g['checkedAt']]
        wr.writerow(["'"+v if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'databaseRows':5271,'freshResponses':probe['freshResponses'],'articlesChecked':285,'archivePages':16,'newArticles':['https://zutapoke.com/28368/','https://zutapoke.com/28471/'],'confirmedNewProducts':len(newids),'substantiveChangedProducts':len(changed),'substantiveChangedArticles':2,'figureSourceRecords':95,'figureMapping':figuremap,'curtainNewChannels':128,'neowingVerifiedProductPages':51,'animateLinksWithVerificationLimit':len(set(unverified)),'sourceAnomalies':list(dict.fromkeys(anomalies))+['Animate商品页出现重定向循环或动态空页，链接按原文章角色图示保留并注明核查受限。'],'ignoredChanges':'68篇仅推荐商品、积分推广或嵌入摘要变化；PLv及ガシャ攻略属于游戏信息，不计为周边更新。','errors':[],'publication':'pending','newProductIds':newids,'changedProductIds':sorted(changed)}
(ROOT/'tools/monitor-check-2026-10-19.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'newProducts':len(newids),'changedProducts':len(changed),'products':len(w['merch']),'articles':len(w['articleIndex']),'figureMappings':len(figuremap),'newProductRoutes':[(i,g['name']) for i,g in enumerate(w['merch']) if g['id'] in newids][:3],'mugyuRoute':next(i for i,g in enumerate(w['merch']) if '6个装BOX' in g['name'])},ensure_ascii=False))
