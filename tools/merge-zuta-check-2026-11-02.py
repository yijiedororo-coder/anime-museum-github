"""Merge fresh November source facts and explicit retailer/official distinctions."""
import copy,csv,hashlib,json,re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-02';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
assert all(not x['new'] and not x['changed'] and not x['removed'] for x in probe['csvChanges'].values())
def doc(u):return html.fromstring((CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_bytes())
def textbody(s):
    d=html.fromstring(s or '<p/>')
    for x in d.xpath('.//script|.//style'):x.drop_tree()
    return re.sub(r'\s+',' ',d.text_content()).strip()
def direct(u):
    for k in ['a8ejpredirect','vc_url','pc','goods_url','url','lsurl']:
        u=parse_qs(urlparse(u).query).get(k,[u])[0]
    return u
path=ROOT/'data/gakumas-data.js';data=json.loads(path.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];old=w['merch'][:];newids=[];changed=[]
oldurls={c['url'] for g in old for c in g['channels']}
def append(g):
    assert all(x['id']!=g['id'] for x in w['merch']);w['merch'].append(g);newids.append(g['id'])
links=json.loads((CACHE/'fumo-links.json').read_text(encoding='utf-8'));official=json.loads((CACHE/'fumo-official.json').read_text(encoding='utf-8'))
assert len(links)==12 and len(official)==6
names=['游戏鼠标','迷你亚克力立牌 BOX','迷你亚克力块 BOX','橡胶理线夹（销售单位待确认）','游戏鼠标垫 CXL','游戏鼠标垫 2XL'];prices=['19,980円','12,870円','12,870円','12,870円','6,480円','7,480円'];categories=['生活 / 应援','立牌','海报 / 摆件','生活 / 应援','生活 / 应援','生活 / 应援']
for i,o in enumerate(official):
    j=o.get('product');u=o['url'];assert u not in oldurls
    desc=textbody(j.get('description')) if j else ''
    if j:assert o['prices'][0].replace(',','')==str(j['price']//100)
    size=(desc.split('商品の仕様',1)[1].split('版権情報',1)[0].strip() if '商品の仕様' in desc else '官方规格未核实：该页返回HTTP 429，本次不继续请求')
    order='2026-10-30至2026-12-04 23:59初回受注（日本时间）；发售/交付月份尚未核实' if j else '来源广告称12月4日截止；该单品受注与交付日待店内确认'
    g={'id':'zuta-fumo2-'+u.split('/')[-1],'name':'学园偶像大师 × ふもコレ第2弹 · '+names[i],'kind':'merch','category':categories[i],'originalName':j['title'] if j else 'ラバーコードクリップ（原文名称；销售单位待核）','originalType':'ふもコレ,第2弾,'+names[i],'characters':'系列多角色 / 初星学园主题；具体图样见商品页','manufacturer':'Fumo Collection（品牌；各品制造方见规格）','productBrand':'ふもコレ / Fumo Collection','price':'ふもコレ：'+prices[i]+'；Animate来源报价：'+('11,440円' if i in [1,2,3] else prices[i])+'（2026-11-02快照，销售单位分别核对）','releaseDate':order,'size':size,'description':'联名第2弹的六类商品分别归档；官方明确BOX销售的款式不按单个立牌或亚克力块报价。理线夹单页访问受限，不推断单个/套装数量。','specifications':['官方规格摘录：'+size,'官方已核对的五款说明：初回受注期每商品赠一张随机特绘贴纸，可能重复；理线夹该项规则尚未独立核实。' if j else '该单品官方页本次返回HTTP 429；名称、图片和报价仅按被追踪文章，BOX规格和特典待确认。','1BOX集齐，官方网店仅按BOX销售。' if j and '1BOX' in desc else '销售数量、包装单位请以对应店内资料为准。'],'image':links[i]['image'],'images':[],'sourceUrl':'https://zutapoke.com/28932/','sourceName':'学マスまとめ · ふもコレ第2弹','checkedAt':DATE,'channels':[{'name':'ふもコレ公式ストア','url':u,'originalUrl':links[i]['url'],'linkType':'官方商品页（规格与标价已核对）' if j else '官方商品入口（本次访问受限）','sourceNote':'官方公开资料快照；不代表实时库存。' if j else 'HTTP 429，尊重来源限流；未核实该单品规格与库存。'},{'name':'Animate','url':links[i+6]['url'],'linkType':'商品页（来源同图对应；店内规格未独立核实）','sourceNote':'来源报价与官方不同，保留两店记录；需核对BOX单位和实际结算价。'}],'availability':'资料快照，不代表现货或预约仍可受理。'}
    if j:
        g['verificationUrl']=u;g['images']=list(dict.fromkeys(('https:'+v if v.startswith('//') else v) for v in j.get('images',[])[:4]));g['sourceObservations']=[{'sourceName':'ふもコレ官方商品页','sourceUrl':u,'price':o['prices'][0]+'円','releaseDate':order,'size':size,'checkedAt':DATE}]
    append(g)
if not any(c['name']=='ふもコレ公式ストア' for c in w['channelSummary']):w['channelSummary'].append({'name':'ふもコレ公式ストア','description':'联名官方商品页；BOX、单品及受注期分别确认；一款页访问限流未核规格。','examples':['生活 / 应援','立牌','海报 / 摆件'],'sourceUrl':'https://www.fumo-collection.com/'})

starlight=json.loads((CACHE/'starlight-official.json').read_text(encoding='utf-8'));assert len(starlight)==6
for s in starlight:
    u=s['url'];assert u not in oldurls
    title=s['title'];t=textbody(html.tostring(doc(u),encoding='unicode'));assert all(x in t for x in ['2027年2月26日','2026年11月9日'])
    role=next(x for x in ['花海咲季','月村手毬','藤田ことね'] if x in title);dumpling='251562' in u
    price='2,200円' if dumpling else '3,600円';size='约W140×H100×D55mm' if dumpling else '约W130×H150×D70mm'
    g={'id':'zuta-starlight-'+u.split('/')[-1],'name':'Starlight Dining · '+('饺子造型毛绒' if dumpling else '官方中式女仆服毛绒')+' · '+role,'originalName':title,'kind':'merch','category':'娃娃 / 毛绒','originalType':'Starlight Dining,ポップアップストア2026,公式ぬいぐるみ','characters':role,'manufacturer':'来源未另列制造商；ASOBI STORE官方商品','releaseDate':'2027年2月26日发售；2026年11月9日23:59前为受注生产，此后数量限定销售（官方记录）','price':price+'（含税 / 个；2026-11-02官方资料）','size':size,'description':'2026年Starlight Dining主题毛绒；服装款与饺子造型款、不同角色分别建档。来源官方说明的线下快闪已经结束，后续网店受注不等于线下仍开放。','specifications':['规格：'+size,'官方列示2027年2月26日发售；混单可能等所有商品到齐再出货。','11月9日23:59为受注生产分界，之后数量限定，不表示届时仍有库存。'],'image':s['image'][0],'images':[s['image'][0]],'sourceUrl':'https://zutapoke.com/14433/','sourceName':'学マスまとめ · 毛绒汇总 / ASOBI官方核对','verificationUrl':u,'checkedAt':DATE,'channels':[{'name':'ASOBI STORE','url':u,'linkType':'官方商品页（角色、规格和日程已核对）','sourceNote':'2026-11-02核对该角色标题及规格；不代表实时库存或结算价。'}],'availability':'官方资料快照；请在单品页确认受理状态。'};append(g)

bandai='https://www.bandai.co.jp/candy/products/2026/4570117932168000.html';bd=doc(bandai);bt=textbody(html.tostring(bd,encoding='unicode'));assert all(t in bt for t in ['2026年11月2日','176円','全29種'])
append({'id':'zuta-wafer4-4570117932168','name':'学园偶像大师 威化饼第4弹 · 全29种卡片系列','originalName':'学園アイドルマスター ウエハース4','kind':'merch','category':'卡片 / 文具','originalType':'ウエハース4,食玩,卡片','characters':'系列多角色；随机卡片','manufacturer':'BANDAI','releaseDate':'2026年11月2日（官方发售日；各店上架可能不同）','price':'官方建议零售价176円 / 包（含税）；来源文章列BOX参考3,520円，数量和店内单位需另核','size':'每包金属质感塑料卡1张、香草奶油味威化饼1枚；卡片全29种','description':'官方食玩第4弹，卡片按系列归档，不将全29种视为单盒保证集齐。','specifications':['官方建议单包176円；来源汇总的3,520円为另一销售单位，不能当作单包售价。','新绘图并非此商品专用限定插画。'],'image':bd.xpath('//meta[@property="og:image"]/@content')[0],'sourceUrl':'https://zutapoke.com/28955/','sourceName':'学マスまとめ · 第48号 / Bandai官方核对','verificationUrl':bandai,'checkedAt':DATE,'channels':[{'name':'官方商品资料','url':bandai,'linkType':'厂商资料页（不是店铺搜索结果）','sourceNote':'2026-11-02核对176円、全29种、11月2日；不表示各店实时库存。'}],'availability':'按官方发售资料记录；店铺上架与库存另行确认。'})

# New weekly report supplies the book's date, but retailer bundle fulfillment can differ.
for g in old:
    if g['id'].startswith('zuta-article-28827-book8-animate-'):
        g.setdefault('sourceObservations',[]).append({'sourceName':'学マスまとめ · 第48号','sourceUrl':'https://zutapoke.com/28955/','releaseDate':'第8卷2026年11月6日发售；店铺附加组合的实际交付待商店核实','price':g['price'],'checkedAt':DATE});g['releaseDate']='原书第8卷2026年11月6日发售（周报记录）；各附加销售组合交付日待店内确认';g['checkedAt']=DATE;changed.append(g['id'])

# An existing series gains character-specific search links; retain original official/store links.
plushdoc=doc('https://zutapoke.com/14433/');card=next(c for c in plushdoc.xpath('//article[contains(@class,"gpl-card")]') if c.xpath('string(.//h3)').strip()=='いっしょに暮らすぬい')
g=next(g for g in old if g['id']=='zuta-plush-2e022919fce1');known={c['url'] for c in g['channels']};addedSearch=0
for shop in card.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," gpl-affiliate-shop ")]'):
    label=shop.xpath('string(.//p[contains(@class,"gpl-shop-label")])').replace('▼','').strip();name={'楽天市場':'乐天市场','駿河屋':'骏河屋','メルカリ':'Mercari（二手）','Amazon':'Amazon'}[label]
    for a in shop.xpath('.//a'):
        u=direct(a.get('href'));assert u.startswith('https://')
        if u not in known:g['channels'].append({'name':name,'url':u,'originalUrl':a.get('href'),'linkType':'角色搜索页（'+a.text_content().strip()+'；并非单品页）','sourceNote':DATE+'来源角色按钮对应，搜索结果可能混入不同版本或二手；不代表现货。'});known.add(u);addedSearch+=1
if addedSearch:g['checkedAt']=DATE;changed.append(g['id'])

for u,sections in [('https://zutapoke.com/28932/',['第2弹6类商品：鼠标19,980円；立牌与亚克力块官方为BOX各12,870円，Animate列11,440円；理线夹销售单位待确认。','鼠标垫CXL 6,480円、2XL 7,480円。官方5款规格已核对，理线夹页HTTP 429，不推断该页规格或库存。','官方已核对页面列初回受注2026年10月30日至12月4日23:59，随机贴纸特典规则见单品。']),('https://zutapoke.com/28955/',['第48号：ふもコレ第2弹、威化饼4于11月2日发售、GOLD RUSH第8卷11月6日发售。','修楽旅行CD周报列11月4日，各店特典不同；保留为周报情报，未独立核对厂商。','GOLD RUSH第8卷纪念活动周报列11月6日至12月6日；具体规则仍需店铺公告核实。'])]:
    assert not any(a['url']==u for a in w['articleIndex']);w['articleIndex'].append({'title':doc(u).xpath('string(//h1)'),'url':u,'checkedAt':DATE,'sections':sections,'prices':[],'dates':[]})
for number,note in [('14433','2026-11-02补充Starlight Dining服装款和饺子款各3角色，共6个官方已核对单品；更新いっしょに暮らすぬい角色搜索入口。'),('13353','2026-11-02来源移除部分已发售手办展示面板；历史馆藏、原商品链接及日期保留，不推断停产或售罄。')]:
    a=next(a for a in w['articleIndex'] if a['url']=='https://zutapoke.com/'+number+'/');a.setdefault('sections',[]).append(note);a['checkedAt']=DATE

def event(eid,name,end,summary,url,start='',reward=''):
    assert not any(e['id']==eid for e in w['events'])
    w['events'].append({'id':eid,'kind':'event','name':name,'category':'周边受注 / 销售提醒','start':start,'end':end,'endLabel':'','summary':summary,'reward':reward,'cost':'依各商品和店铺结算；运费、购买门槛及特典条件见原始资料。','regions':['日本'],'sourceUrl':url,'sources':['zuta-nov02'],'checkedAt':DATE,'activeDates':['截止时间按日本时间记录。'],'steps':['打开对应官方单品页，确认受注、交付日及购买单位。'],'places':[],'notes':['资料快照，不代表实时库存。'],'pending':['未独立确认的单品受理状态、配额及实际发货安排'],'media':{'images':[],'verifiedFacts':[],'resources':[],'sources':[]}})
w['eventSources']['zuta-nov02']=['学マスまとめ · 新增周边资料','https://zutapoke.com/28932/']
event('gk-fumo2-order-202610','ふもコレ联名第2弹 · 初回受注','2026-12-04T23:59','已核对的官方页面列初回受注10月30日至12月4日23:59；理线夹页限流，具体规则未独立确认。',official[0]['url'],'2026-10-30','已核对页面列每商品随机特绘贴纸1张，可能重复；适用期与单位以各单品为准。')
event('gk-starlight-plush-order-202611','Starlight Dining毛绒 · 受注生产分界','2026-11-09T23:59','六个官方毛绒单品列11月9日23:59前受注生产，此后数量限定销售；发售日为2027年2月26日。线下快闪已结束，勿与网店受注混淆。',starlight[0]['url'])
report=w['collectionReport'];report.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':len(newids),'changedProducts':len(changed),'newArticles':2,'changedArticles':2,'newEvents':2,'newCharacterSearchLinks':addedSearch}});w['retrievedAt']=DATE
assert len(newids)==13 and len(changed)==9
assert [g['id'] for g in before['items'][0]['merch']]==[g['id'] for g in w['merch'][:len(old)]]
for prev,now in zip(before['items'][0]['merch'],w['merch']):
    assert now['channels'][:len(prev['channels'])]==prev['channels']
    if prev['id'] not in changed:assert prev==now
assert w['events'][:-2]==before['items'][0]['events']
path.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',report)]:
    (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
    for g in w['merch']:
        vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')]
        writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProducts':len(newids),'changedProducts':len(changed),'newProductIds':newids,'changedProductIds':changed,'newEvents':2,'newArticles':2,'changedArticles':2,'newCharacterSearchLinks':addedSearch,'sourceErrors':probe['errors'],'sourceLimitations':['ふもコレ理线夹页HTTP 429；尊重限流，未核实该页规格和受理状态。','来源13608首次IncompleteRead，独立重取完整193292字节成功。','批量文章变化主要是推荐广告替换；未复制广告中互相矛盾的折扣或新增重复商品。'],'officialVerified':'ふもコレ5款、Starlight Dining 6单品、Bandai威化饼4。'}
(ROOT/'data/gakumas-monitor-2026-11-02.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k not in ['newProductIds','changedProductIds']},ensure_ascii=False))
