import json, re, urllib.request, hashlib
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from html import unescape

root=Path(__file__).resolve().parent.parent
pages={n:json.loads((root/'tools'/f'{n}-source.json').read_text(encoding='utf-8')) for n in ['station','seven','plush','kotone','cd']}
channels={'animate-onlineshop.jp':('Animate','动漫商品与手办'), 'anime-store.jp':('AnimeStore','动漫商品'), 'colleize.com':('Colleize','角色周边'), 'eeo.today':('eeo Store','角色周边'), '7net.omni7.jp':('Seven Net','便利店联名周边'), 'neowing.co.jp':('NeoWing','手办、毛绒与音乐'), 'suruga-ya.jp':('骏河屋','毛绒与角色商品'), 'rakuten.co.jp':('乐天市场','多店铺商品检索'), 'dmm.com':('DMM','手办'), 'gamers.co.jp':('Gamers','音乐与店铺特典'), 'asobistore.jp':('ASOBI STORE','官方音乐与周边'), 'amazon':('Amazon','音乐与店铺特典')}
def canonical(url):
    for _ in range(4):
        q=parse_qs(urlparse(unescape(url)).query)
        nxt=next((q[k][0] for k in ['vc_url','a8ejpredirect','lsurl','pc','lurl','goods_url'] if k in q),None)
        if not nxt: break
        url=nxt
    return url
def shop(url):
    host=urlparse(url).hostname or ''
    return next((v[0] for k,v in channels.items() if k in host),None)
def image(n,filename):
    return next(i['src'] for i in pages[n]['images'] if i['src'] and i['src'].split('/')[-1]==filename)
def links_for(n,src):
    urls=[i['link'] for i in pages[n]['images'] if i['src']==src and i['link']]
    if not urls:
        raw=(root/'tools'/f'{n}-source.html').read_text(encoding='utf-8')
        tail=raw[raw.index(src)+len(src):]
        match=re.search(r'<a\b[^>]*href=["\']([^"\']+)',tail)
        if match: urls=[unescape(match[1])]
    result=[]
    for url in urls:
        url=canonical(url); name=shop(url)
        if name and not any(c['name']==name for c in result): result.append({'name':name,'url':url})
    return result
def cache(url):
    ext=Path(urlparse(url).path).suffix or '.png'
    name=hashlib.sha256(url.encode()).hexdigest()[:20]+ext
    local='assets/gakumas/'+name; target=root/local
    target.parent.mkdir(exist_ok=True,parents=True)
    if not target.exists(): target.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read())
    return local

specs=[
('station','image-100.png','站务员服装 · 亚克力立牌','立牌','¥1,925 / 单款','系列示例图；具体角色请在渠道页面选择。'),
('station','image-139.png','站务员服装 · 迷你亚克力立牌套装','立牌','¥12,155 / 全套','随机系列，全套价格。'),
('station','image-140.png','站务员服装 · 等身徽章套装','徽章','¥7,150 / 全套','随机系列，全套价格。'),
('station','image-141.png','站务员服装 · Q版徽章套装','徽章','¥7,150 / 全套','随机系列，全套价格。'),
('station','image-142.png','站务员服装 · 配件亚克力挂件套装','挂件','¥12,870 / 全套','随机系列，全套价格。'),
('station','image-143.png','站务员服装 · 亚克力钥匙扣套装','挂件','¥11,440 / 全套','随机系列，全套价格。'),
('station','image-144.png','站务员服装 · 亚克力卡片套装','文具','¥8,580 / 全套','随机系列，全套价格。'),
('station','image-113.png','站务员服装 · 模切贴纸','文具','¥550 / 单款','系列示例图；具体角色请在渠道页面选择。'),
('station','image-126.png','站务员服装 · A3透明海报','文具','¥550 / 单款','系列示例图；具体角色请在渠道页面选择。'),
('seven','image-60.png','Seven Net联名 · 亚克力立牌','立牌','¥1,760 / 单款','系列示例图；具体角色请在渠道页面选择。'),
('seven','image-73.png','Seven Net联名 · BIG亚克力立牌','立牌','¥3,850 / 单款','系列示例图；具体角色请在渠道页面选择。'),
('seven','image-86.png','Seven Net联名 · 极光亚克力面板','立牌','¥4,950','联名系列面板。'),
('seven','image-89.png','Seven Net联名 · 透明文件夹3枚组','文具','¥1,320 / 3枚组','联名系列文件夹。'),
('seven','image-87.png','Seven Net联名 · 随机亚克力钥匙扣','挂件','¥770 / 单个','13种；整套参考价 ¥10,010。'),
('seven','image-88.png','Seven Net联名 · 随机徽章','徽章','¥605 / 单个','13种；整套参考价 ¥7,865。'),
('plush','image-93.png','杯子蛋糕たぴぬい Vol.1','毛绒','¥6,600 / 6种整盒','Vol.1 全6种；商店折扣和配送费用另行确认。'),
('plush','image-92.png','杯子蛋糕たぴぬい Vol.2','毛绒','¥7,700 / 7种整盒','Vol.2 全7种；商店折扣和配送费用另行确认。'),
('kotone','image.png','藤田琴音 · 雨后鸢尾 特训前Ver.','手办','¥22,000 / 标价','来源文章列有 Animate、DMM、NeoWing 的折扣报价，实时价格请查看渠道。'),
]
goods=[]
for n,filename,name,category,price,description in specs:
    src=image(n,filename)
    goods.append({'id':'gakumas-'+str(len(goods)+1),'name':name,'kind':'merch','category':category,'price':price,'description':description,'image':cache(src),'imageSource':src,'sourceUrl':pages[n]['url'],'sourceName':'学マスまとめ 攻略','checkedAt':'2026-10-06','channels':links_for(n,src),'availability':'库存与预约状态请查看渠道页面'})

cdurl='https://shop.asobistore.jp/products/detail/250711-00-00-00'
cdlinks=[canonical(l) for l in pages['cd']['links'] if l and ('asobistore' in l or 'gamers' in canonical(l) or 'amazon' in l or 'animate' in canonical(l))]
goods.append({'id':'gakumas-19','name':'Gravure Solo Collection Vol.2「Agitato」','kind':'merch','category':'音乐','price':'¥3,500 / 官方标价','description':'官方商店标注预计 2027年1月20日发行，预约至 2026年11月8日。汇总站将预约截止日写为发行日，本站采用官方商店日期。店铺特典以各渠道页面为准。','image':cache(image('cd','image-152-1024x576.png')),'imageSource':image('cd','image-152-1024x576.png'),'sourceUrl':pages['cd']['url'],'verificationUrl':cdurl,'sourceName':'学マスまとめ 攻略 / ASOBI STORE','checkedAt':'2026-10-06','channels':[{'name':shop(l),'url':l} for l in dict.fromkeys(cdlinks) if shop(l)],'availability':'预计发行 / 预约详情见渠道'})
cover='https://gakuen.idolmaster-official.jp/assets/img/ogp.png?date=0516'
work={'id':'gakuen-idolmaster','name':'学园偶像大师','aliases':'学園アイドルマスター 学マス 学马仕 Gakuen Idolmaster','region':'日本','year':'2024','mediaType':'偶像养成游戏','status':'2024年5月16日上线 · 周边档案','cast':'请查看官方角色介绍','score':'','summary':'初星学园的偶像养成作品。','poster':cover,'localPoster':cache(cover),'sourceUrl':'https://gakuen.idolmaster-official.jp/','retrievedAt':'2026-10-06','merch':goods}
allchannels={c['name']:c for g in goods for c in g['channels']}
work['channelSummary']=[{'name':name,'description':next(v[1] for v in channels.values() if v[0]==name),'examples':list(dict.fromkeys(g['category'] for g in goods if any(c['name']==name for c in g['channels']))),'sourceUrl':next(g['sourceUrl'] for g in goods if any(c['name']==name for c in g['channels']))} for name in allchannels]
(root/'data/gakumas-data.js').write_text('window.MUSEUM_ADDITIONS = '+json.dumps({'items':[work],'checkedAt':'2026-10-06','sourceUrl':'https://zutapoke.com/'},ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
print(json.dumps({'works':1,'merch':len(goods),'channels':list(allchannels),'images':len(list((root/'assets/gakumas').glob('*')))},ensure_ascii=True))
