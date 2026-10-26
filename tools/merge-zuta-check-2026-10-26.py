"""Merge dated source observations; preserve the published catalog and existing routes."""
import copy, csv, hashlib, json, re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from lxml import html

ROOT=Path(__file__).resolve().parent.parent
DATE='2026-10-26'
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
CACHE=ROOT/'tools/zuta-monitor'/DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'))
assert probe['checkedAt'].startswith(DATE) and not probe['errors']
assert all(not v['new'] and not v['changed'] and not v['removed'] for v in probe['csvChanges'].values())
def doc(u):return html.fromstring((CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
path=ROOT/'data/gakumas-data.js'
data=json.loads(path.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
before=copy.deepcopy(data); w=data['items'][0]; changed=[]; newids=[]
byid={g['id']:g for g in w['merch']}
for gid,date in [('zuta-figure-13353-6f87df574942','2026年11月12日'),('zuta-figure-13353-3b3f4c074c89','2026年11月27日')]:
    g=byid[gid];old=g['releaseDate']
    assert date in doc('https://zutapoke.com/12413/').text_content()
    assert date in doc('https://zutapoke.com/13353/').text_content()
    g.setdefault('sourceObservations',[]).extend([
        {'sourceName':'学マスまとめ · 旧日期记录（已被来源修订）','sourceUrl':g['sourceUrl'],'releaseDate':old,'price':g['price'],'checkedAt':g['checkedAt']},
        {'sourceName':'学マスまとめ · 景品日程与手办汇总','sourceUrl':'https://zutapoke.com/12413/','releaseDate':date+'登场（来源预定日；本次未获厂商独立确认）','price':'娃娃机景品，无统一零售定价','checkedAt':DATE}])
    g['releaseDate']=date+'（来源预定登场日；厂商独立确认待核）'
    g['specifications'].append(DATE+'来源将旧日程'+old+'修订为'+date+'；旧资料保存在其他来源记录，不代表延期或提前原因已获确认。')
    for c in g['channels']:
        if 'amazon.co.jp/s?' in c['url']:
            c['linkType']='搜索页（需自行确认款式与价格）'
    g['checkedAt']=DATE;changed.append(gid)

official='https://bushiroad-store.com/products/2000292134702'
officialtext=re.sub(r'\s+',' ',doc(official).text_content())
assert all(s in officialtext for s in ['2026年10月30日','6,600','6パック','90 mm'])
g=byid['zuta-figure-13353-921b343e94d5']
g.setdefault('sourceObservations',[]).extend([
    {'sourceName':'学マスまとめ · 历史汇总日期（与官方不符）','sourceUrl':g['sourceUrl'],'releaseDate':g['releaseDate'],'price':g['price'],'checkedAt':g['checkedAt']},
    {'sourceName':'ブシロード官方商店 · BOX规格','sourceUrl':official,'releaseDate':'2026年10月30日发售；该店同日以后交付','price':'6,600円 / BOX（含税，6包）；2026-10-26快照','size':'全高约90mm；全6种，官方标注1BOX集齐','checkedAt':DATE}])
g.update({'releaseDate':'2026年10月30日（官方发售日；旧汇总12月12日记录保留）','price':'官方BOX：6,600円（含税，6包；2026-10-26快照）','size':'全高约90mm；6包 / BOX，全6种','characters':'紫雲清夏、篠澤広、十王星南、秦谷美鈴、花海佑芽、姫崎莉波','manufacturer':'ブシロードクリエイティブ','checkedAt':DATE})
g['specifications'].append('官方商品页明确为vol.2 BOX：6包、全6种，标注1BOX集齐；历史来源日期存在差异，当前采用官方2026年10月30日。')
g['channels'].append({'name':'ブシロード公式ストア','url':official,'linkType':'官方商品页（vol.2 BOX规格已核对）','sourceNote':'2026-10-26核对价格6,600円、全6种、6包、约90mm及10月30日发售；不代表实时库存。'})
changed.append(g['id'])
if not any(c['name']=='ブシロード公式ストア' for c in w['channelSummary']):
    w['channelSummary'].append({'name':'ブシロード公式ストア','description':'发行方官方商品页；PACK与BOX分别确认，不把报价当实时库存。','examples':['手办'],'sourceUrl':official})
# The old import reused the vol.2 DMM link on vol.1 records: keep the URL and clearly warn visitors.
for g in w['merch']:
    if 'palverse' in g['name'].lower() and 'vol.1' in g['name']:
        cs=[c for c in g['channels'] if '/cid=c260500983/' in c['url']]
        if cs:
            for c in cs:
                c['linkType']='历史误配链接（实际为vol.2，不适用于本vol.1款式）'
                c['sourceNote']+=' 2026-10-26按新周报对应图样确认此链接属于vol.2；保留历史URL，购买本款请核对其他渠道。'
            g['checkedAt']=DATE;changed.append(g['id'])

source='https://zutapoke.com/28827/'
records=json.loads((CACHE/'book8.json').read_text(encoding='utf-8'))
assert len(records)==8
oldurls={c['url'] for g in w['merch'] for c in g['channels']}
for r in records:
    gid='zuta-article-28827-book8-animate-'+r['id']
    assert gid not in byid and r['url'] not in oldurls
    specs=['来源周报表格列出该销售组合、价格及对应Animate商品编号；店内页面规格、发售日与库存尚未独立核实。','本条使用作品标识占位图，尚未取得可核对的本卷封面，不作为第8卷封面展示。']
    if 'シリアル' in r['name']:specs.append('ビッグアクスタ購入用シリアル是购买用序列号；不等同于套餐直接附送大型立牌，是否需额外付款、期限及适用规则待店内核实。')
    w['merch'].append({'id':gid,'kind':'merch','name':'学園アイドルマスター GOLD RUSH 8 · '+r['name'],'originalName':'学園アイドルマスター GOLD RUSH 第8巻 · '+r['name'],'category':'书籍','originalType':'GOLD RUSH,第8巻,Animate销售组合','characters':'来源未逐一标注；见销售组合','manufacturer':'来源未标注','releaseDate':'本次周报未标注发售日期；待商店及出版社核实','price':r['price']+'（来源周报销售组合报价；2026-10-26记录）','size':'来源未标注','description':'GOLD RUSH第8卷的通常版、特装版及店铺附加挂件、购买用序列号组合分别建档；各组合不可视为相同附赠内容。','specifications':specs,'image':w.get('localPoster') or w['poster'],'imagePlaceholder':True,'sourceUrl':source,'sourceName':'学マスまとめ · 週刊通信47号','checkedAt':DATE,'channels':[{'name':'Animate','url':r['url'],'originalUrl':r['originalUrl'],'linkType':'商品页（原文表格编号对应；店内资料未独立核实）','sourceNote':'按周报表格的完整销售组合标签对应，价格为来源快照。'}],'availability':'来源记录，不代表实时库存或仍在受理预约。'})
    newids.append(gid)

sections={
 '12413':['2026-10-26来源更新：篠澤広ESPRESTO预定11月12日，倉本千奈预定11月27日；来源删去的9、10月历史景品仍保留在馆藏。'],
 '13353':['2026-10-26：两款11月景品日期修订；PalVerse vol.2旧12月12日记录与官方不符，已采用官方10月30日，保留原记录。'],
 '24251':['2026-10-26正文不再展示AmiAmi面板；历史渠道保留，不推断售罄、停售或报价失效。PalVerse vol.2官方BOX 6,600円、6包、约90mm、10月30日发售。'],
 '25317':['2026-10-26正文不再展示Premium Bandai面板；保留原渠道资料，不将面板移除推断为售罄或停售。']}
for number,notes in sections.items():
    a=next(a for a in w['articleIndex'] if a['url']=='https://zutapoke.com/'+number+'/');a.setdefault('sections',[]).extend(notes);a['checkedAt']=DATE
assert not any(a['url']==source for a in w['articleIndex'])
w['articleIndex'].append({'title':doc(source).xpath('string(//h1)'),'url':source,'checkedAt':DATE,'sections':['GOLD RUSH第8卷：Animate 8种销售组合，通常版880円、特装版2,200円；挂件、购买用序列号组合价格单独保留。','Gamers文字介绍限定通常版2,640円、限定特装版3,960円；目前仅汇总入口，尚未独立核对单品页，保留为文章情报。','PalVerse vol.2预定10月30日；ESPRESTO広11月12日、千奈11月27日。','ECLIPSE LIGHT前半截至10月30日、后半自10月31日起，现有活动档案已收录；3rd Single纪念商品也已收录，不重复新增。'],'prices':['880円','2,200円','2,640円','3,960円','1,870円','3,190円','8,580円','9,570円','9,900円','10,890円'],'dates':['2026-10-30','2026-10-31','2026-11-12','2026-11-27']})
assert len(set(changed))==len(changed)
report=w['collectionReport'];report.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':len(newids),'changedProducts':len(changed),'newArticles':1,'changedArticles':4}});w['retrievedAt']=DATE
old=before['items'][0]
assert [g['id'] for g in old['merch']]==[g['id'] for g in w['merch'][:len(old['merch'])]]
assert old['events']==w['events']
for prev,now in zip(old['merch'],w['merch']):
    assert [c['url'] for c in prev['channels']]==[c['url'] for c in now['channels'][:len(prev['channels'])]]
    if prev['id'] not in changed:assert prev==now
path.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',report)]:
    (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    writer=csv.writer(fp);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
    for g in w['merch']:
        vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')]
        writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProductIds':newids,'changedProductIds':changed,'newProducts':len(newids),'changedProducts':len(changed),'newArticles':1,'changedArticles':4,'sourceErrors':probe['errors'],'officialVerification':official,'limitations':['两款ESPRESTO具体日期来自被追踪站两篇文章，尚未获厂商独立确认。','周报部分折扣百分比与数字不一致，未采用百分比；历史面板移除不等于售罄。','第8卷无已核对封面，使用明确标注的作品占位图；发售日期和店内附赠细则待核。']}
(ROOT/'data/gakumas-monitor-2026-10-26.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
