"""Append the confirmed new Curtain Tamashii article and its 51 matched products."""
import copy, csv, hashlib, json, re
from collections import Counter
from pathlib import Path
from lxml import html

ROOT=Path(__file__).resolve().parent.parent
DATE='2026-10-15';CACHE=ROOT/'tools/zuta-monitor'/DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'))
research=json.loads((CACHE/'curtain-products.json').read_text(encoding='utf-8'))
assert not probe['errors'] and probe['newArticles']==[research['article']]
assert all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
assert len(research['products'])==len({r['product']['url'] for r in research['products']})==51
assert all(r['imageMatch']['score']<25 and r['imageMatch']['nextScore']-r['imageMatch']['score']>3 for r in research['products'])
backup=CACHE/'before-update';backup.mkdir(exist_ok=True)
for name in ['gakumas-data.js','gakumas-products.csv','gakumas-article-index.json','gakumas-collection-report.json']:
    p=backup/name
    if not p.exists():p.write_bytes((ROOT/'data'/name).read_bytes())
path=ROOT/'data/gakumas-data.js'
data=json.loads(path.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
before=copy.deepcopy(data);work=data['items'][0]
assert not any(a['url']==research['article'] for a in work['articleIndex'])
new=[]
for r in research['products']:
    p=r['product'];name=p['name'];character=re.sub(r'\s+','',re.search(r'（([^／）]+)',name)[1])
    group=r['group'].split('（')[0]
    category={'グラフィックTシャツ':'服饰','特大アクリルスタンド':'立牌','B2タペストリー':'海报 / 摆件','クッションカバー':'生活 / 应援'}[group]
    raw_type={'グラフィックTシャツ':'Tシャツ','特大アクリルスタンド':'アクリルスタンド','B2タペストリー':'タペストリー','クッションカバー':'その他'}[group]
    channels=[]
    for u in p['buyUrls']:
        assert re.sub(r'\s+','',p['name']) in re.sub(r'\s+','',p['verifiedShopTitles'][u])
        size=re.search(r'\(([^)]+)サイズ\)',p['buyLabels'][u])
        channels.append({'name':'カーテン魂','url':u,'linkType':'商品页（官方直营'+('；'+size[1]+'尺码' if size else '')+'）','sourceNote':DATE+'核对页面商品名与角色款；不代表实时库存。'})
    channels.append({'name':'カーテン魂','url':p['url'],'linkType':'官方商品资料（含规格、图片与分批发货安排）'})
    specs=[k+'：'+v for k,v in p['specifications'].items()]
    specs += ['受注批次 '+order+' → 预计发货 '+shipping for order,shipping in p['shippingSchedule']]
    specs += ['运费（来源）：本州、北海道、四国、九州750日元；冲绳及其他离岛2,000日元。','销售开始时间（厂商标注，日本时间）：'+p['saleStart'],'不同发货批次合并下单时，按较晚批次发货；销售与批次安排以官方页面为准。']
    g={'id':'zuta-article-28183-'+p['slug'],'kind':'merch','name':'カーテン魂 · '+name,'originalName':name,'category':category,'originalType':raw_type+',カーテン魂','characters':character,'manufacturer':'カーテン魂','productBrand':'カーテン魂','variant':name,'releaseDate':p['saleStart']+'起售；按受注批次发货','price':p['price']+'（含税；来源文章与厂商标价）','size':p['specifications'].get('サイズ','来源未标注'),'description':'从2026年10月14日发布的カーテン魂新周边文章收录；角色、具体款式与购买入口已核对厂商公开商品页。'+('T恤按角色款收录，M、L、XL保留各自购买链接；不把尺码重复计算为独立商品。' if group=='グラフィックTシャツ' else '')+'销售开始日与按订单批次发货的日期分别保留；报价不代表实时库存或结算价。','image':r['image'],'imageSource':r['image'],'images':p['images'],'sourceUrl':research['article'],'sourceName':'学マスまとめ · カーテン魂新グッズ / 厂商官网核对','verificationUrl':p['url'],'originalSourceLink':r['affiliateUrl'],'checkedAt':DATE,'specifications':specs,'shippingSchedule':p['shippingSchedule'],'channels':channels,'availability':'本次核对了官方公开商品页面及相应角色、尺码链接。库存与订单受付状态可能改变，请在商店确认。'}
    new.append(g)
assert len({g['id'] for g in new})==51
assert not {g['id'] for g in new}&{g['id'] for g in work['merch']}
work['merch'].extend(new)
articleRaw=(CACHE/(hashlib.sha256(research['article'].encode()).hexdigest()+'.html')).read_text(encoding='utf-8')
d=html.fromstring(articleRaw)
sections=['グラフィックTシャツ：13角色款，7,700日元；M / L / XL分别保留商品链接。','特大アクリルスタンド：13款训练服造型，4,400日元。','B2タペストリー：12款キミとセミブルー图案，4,400日元。','クッションカバー：13角色款，2,970日元。','厂商标注2026年10月14日12:00（日本时间）起售；按订单批次发货，详细日期见各商品。']
work['articleIndex'].append({'title':' '.join(d.xpath('//h1')[0].text_content().split()),'url':research['article'],'sections':sections,'prices':['7,700円','4,400円','2,970円'],'dates':['2026年10月14日12:00'],'image':d.xpath('//meta[@property="og:image"]/@content')[0],'publishedAt':'2026-10-14','checkedAt':DATE,'products':len(new),'verificationUrls':[p['product']['url'] for p in research['products']]})
work['channelSummary'].append({'name':'カーテン魂','description':'官方直营商品页与厂商资料；T恤区分M、L、XL尺码，受注批次及运费见详情。','examples':['服饰','立牌','海报 / 摆件','生活 / 应援'],'sourceUrl':research['article']})
report=work['collectionReport'];report.update({'checkedAt':DATE,'articlesRead':len(work['articleIndex']),'products':len(work['merch']),'categories':dict(Counter(g['category'] for g in work['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':51,'changedProducts':0,'newArticles':1,'changedArticles':0}})
work['retrievedAt']=DATE
assert work['merch'][:len(before['items'][0]['merch'])]==before['items'][0]['merch']
assert work['articleIndex'][:-1]==before['items'][0]['articleIndex']
path.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
(ROOT/'data/gakumas-article-index.json').write_text(json.dumps(work['articleIndex'],ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'data/gakumas-collection-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    writer=csv.writer(fp);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
    for g in work['merch']:
        values=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g['price'],g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g['checkedAt']]
        writer.writerow(["'"+v if str(v).startswith(('=','+','-','@')) else v for v in values])
audit={'checkedAt':probe['checkedAt'],'databaseRows':5271,'freshResponses':probe['freshResponses'],'articlesChecked':282,'archivePages':16,'newArticles':[research['article']],'confirmedNewProducts':51,'substantiveChangedProducts':0,'substantiveChangedArticles':0,'productGroups':dict(Counter(r['group'] for r in research['products'])),'officialProductPagesChecked':51,'officialShopPagesChecked':77,'ignoredArticleChanges':19,'ignoredChanges':'18篇仅乐天积分推广标语变化，1篇仅YouTube嵌入卡片文案变化；商品数据、价格、日期和链接均未改变。','sourceAnomalies':[research['promotionLinkIssue']],'errors':[],'publication':'pending','preservedExistingProducts':5272}
(ROOT/'tools/monitor-check-2026-10-15.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'newProducts':len(new),'products':len(work['merch']),'articles':len(work['articleIndex']),'channels':len(work['channelSummary']),'firstIndex':len(before['items'][0]['merch'])},ensure_ascii=False))
