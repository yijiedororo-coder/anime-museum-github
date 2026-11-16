"""Merge November 16 sourced products, edition-specific CDs and weekly leads."""
import copy,csv,hashlib,json,re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-16';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
assert all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
def doc(u):return html.fromstring((CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
def body(u):return doc(u).xpath('//main/article/*[contains(@class,"post_content")]')[0]
def direct(u):
 for _ in range(4):
  q=parse_qs(urlparse(u).query);v=next((q[k][0] for k in ['a8ejpredirect','lsurl','pc'] if k in q),None)
  if not v:break
  u=v
 return u
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];ids=[];changed=[];newlinks=[]
def add(g):
 assert not any(x['id']==g['id'] for x in w['merch']);w['merch'].append(g);ids.append(g['id']);return g
def base(gid,name,category,source,image):return {'id':gid,'kind':'merch','name':name,'originalType':name,'category':category,'characters':'详见来源；未逐项核实','price':'来源未列，待确认','releaseDate':'来源未列，待确认','size':'来源未列，待确认','description':'来源公开资料快照，不代表实时库存。','image':image,'sourceUrl':source,'sourceName':'学マスまとめ · 本次核查','checkedAt':DATE,'channels':[],'sourceRecordIds':[],'variants':[]}
def link(g,u,name,kind,note,raw=None):
 if any(c['url']==u for c in g['channels']):return
 g['channels'].append({'name':name,'url':u,'originalUrl':raw or u,'linkType':kind,'sourceNote':note});newlinks.append(u)
# Kanae stand styles are kept together until exact per-style retailer data can be confirmed.
s='https://zutapoke.com/29481/';a=body(s);images=list(dict.fromkeys(a.xpath('.//img/@data-src')));g=add(base('zuta-kanae-stand-202611','氷渡香名江 · 官方亚克力立牌系列','亚克力立牌',s,images[0]));g.update({'images':images,'characters':'氷渡香名江','price':'各1,500円（来源）','description':'来源提供2个款式图片及对应Animate商品页；作为系列保存，不猜测A/B款式或交付日期。'})
for raw in dict.fromkeys(a.xpath('.//a/@href')):link(g,direct(raw),'Animate','商品页（系列内不同款式）','按来源图片对应，店内规格、日期和库存未独立确认。',raw)
# Explicitly separate the normal and special editions; prices from different shops stay attributed.
checks=json.loads((CACHE/'retail-check.json').read_text(encoding='utf-8'));checkmap={x['url']:x for x in checks};assert all('text' in x for x in checks)
for s,kind in [('https://zutapoke.com/29472/','kaigou'),('https://zutapoke.com/29471/','kanae')]:
 a=body(s);links=list(dict.fromkeys(a.xpath('.//a/@href')));promo=a.xpath('.//img/@data-src')[0]
 for edition in (['normal','special'] if kind=='kaigou' else ['normal']):
  name=('乖轟 1st Single「アンバランス」' if kind=='kaigou' else '氷渡香名江 1st Single「メタモルフォーゼ」')+(' · 特装盘' if edition=='special' else ' · 通常盘')
  g=add(base('zuta-'+kind+'-cd-'+edition+'-202611',name,'音乐 / 影像',s,promo));g.update({'imagePlaceholder':True,'characters':'雨夜燕 / 有村麻央' if kind=='kaigou' else '氷渡香名江','releaseDate':'2027年4月7日予定（ASOBI/Gamers）' if kind=='kaigou' else '2027年3月3日予定（ASOBI/Gamers）','price':'6,500円含税（ASOBI特装盘）' if edition=='special' else 'Gamers 1,999円含税；ASOBI关联商品标注2,000円，保留店铺差异' if kind=='kaigou' else '2,500円含税（ASOBI/Gamers）','description':'不同版本分别入库；来源预约宣传图只作参考，未确认为最终CD封面。','specifications':['特典依店铺、版本和库存；不表示所有渠道同时附赠。']})
  if edition=='special':g['specifications'].append('ASOBI特装盘含乖轟特制肩包，不能把6,500円当作通常盘售价。')
  for raw in links:
   u=direct(raw)
   if 'gamers' in u:
    if edition=='special':continue
    v=checkmap[u];assert ('2027/04/07' if kind=='kaigou' else '2027/03/03') in v['text'];link(g,u,'Gamers','商品页（通常盘）','已核标题、价格、发售日；特典为56mm徽章2种套装（乖轟）/56mm徽章（香名江），送完为止。',raw)
   elif 'shop.asobistore.jp' in u:
    if kind=='kaigou' and edition=='normal':continue
    v=checkmap[u];assert ('6,500' if edition=='special' else '2,500') in v['text'];link(g,u,'ASOBI STORE','商品页（特装盘）' if edition=='special' else '商品页','已核价格、日期和版本；香名江贴纸 / 乖轟换装封面特典条件以店内最新说明为准。',raw)
   else:
    shop='Amazon' if 'amazon' in u else 'Animate';link(g,u,shop,'搜索页（须选择正确版本）' if shop=='Amazon' else '商品选择入口（版本适用待确认）','来源称Amazon大封面；Animate乖轟长照片2张套装、香名江A3透明海报及活动申请序列号。版本、期限、抽选参加资格未独立确认。',raw)
# Five sponsor products are paired across stores by identical source images.
s='https://zutapoke.com/29382/';plan=json.loads((CACHE/'sponsor-plan.json').read_text(encoding='utf-8'));verified=json.loads((CACHE/'sponsor-check.json').read_text(encoding='utf-8'))
for v in verified:
 assert 'title' in v and 'text' in v
 image=next(x['image'] for x in plan if x['url']==v['url']);name=v['title'].split(' | ')[0];price=re.search(r'\d,\d{3}円\(税込\)',v['text'])[0];dates=re.findall(r'\d{4}/\d{2}/\d{2}|\d{4}年\d{2}月',v['text'])
 g=add(base('zuta-sponsor-'+v['url'].strip('/').split('/')[-1],name,'服饰 / 生活周边' if '法被' in name else '海报 / 挂画',s,image));g.update({'originalName':name,'price':price+'（Gamers）','releaseDate':dates[0]+'（Gamers页面标注，交付需店内确认）' if dates else '来源未列完整发售日期，待确认','characters':'紫雲清夏' if '紫雲清夏' in name else '葛城リーリヤ' if '葛城リーリヤ' in name else '角色/款式见来源','description':'標FINAL协赞社周边；按来源相同图片合并商店链接。衣服尺寸入口未逐一确认款式，不乱配为本条商品。'})
 for x in plan:
  if x['image']==image:link(g,x['url'],'Gamers' if 'gamers' in x['url'] else 'Animate','商品页（来源同图对应）','Gamers核对标题和价格；其他渠道按来源对应，实际运费、尺寸和库存待店内。',x['raw'])
# Secondary weekly leads are labelled as such; no invented product inventory.
s='https://zutapoke.com/29434/';a=body(s);promo=w['poster']
g=add(base('zuta-lawson-other-lineup-202611','罗森11月联名 · 其他周边商品分类档案','其他周边',s,promo));g.update({'imagePlaceholder':True,'price':'桌垫3,850円；大挂画9,900円；担当偶像确定徽章5件组3,300円；偶像套装3,850円；立牌1,870円；随机镜面挂件1,320円；随机闪粉徽章660円（周报）','description':'补充迷你毛绒之外的商品分类，非一个组合包。具体角色、单位与购买链接需转往周报/官方商品目录确认；本次未逐个店页核实。','specifications':['镜面挂件A完整组7,920円/B完整组9,240円；徽章A完整组3,960円/B完整组4,620円（周报报价），与随机单件区分。','周报称担当偶像徽章5件组内1枚带签名，是否印刷、适用款式等细则待官方，不表示亲笔签名。']})
link(g,'https://www.lawson.co.jp/campaign/lop_gakuen_idolmaster_2611_goods/','官方商品资料','官方系列目录（本次仅记录入口，未重核单品）','不能视为一个套餐或全部同时在售。')
g=add(base('zuta-mugyumi-vol2-preview-202611','むぎゅみに收藏手办 vol.2 · 周报预告','手办 / 模型',s,promo));g.update({'imagePlaceholder':True,'releaseDate':'2027年5月28日（周报预告；厂商待核）','description':'来源预告第2弹，价格、款数、角色、尺寸、正式购买渠道待公布；不与第1弹合并。'})
# Add newly announced Rakuten benefit to the existing three CD entries.
c=next(c for c in probe['articleChanges'] if c['url']=='https://zutapoke.com/29288/');assert len(c['linksAdded'])==1;raw=c['linksAdded'][0];u=direct(raw)
for g in w['merch']:
 if g['id'].startswith('zuta-duet2-'):
  link(g,u,'楽天ブックス','系列搜索/选择入口（需核对本张标题和版本）','来源新增5cm亚克力钥匙扣特典；适用版本、是否需选特典版及余量未独立确认。',raw);g['checkedAt']=DATE;changed.append(g['id'])
# All six articles retained, with speculation separated from product records.
sections={
'https://zutapoke.com/29481/':['氷渡香名江官方立牌2个Animate款式入口，来源各1,500円；具体版本和交付待店内核实。'],
'https://zutapoke.com/29472/':['乖轟「アンバランス」通常盘与特装盘分开：2027年4月7日予定。Gamers通常盘1,999円，ASOBI关联标价2,000円；ASOBI特装盘6,500円含肩包。','店铺特典分别记录：Amazon大封面、Animate长照片2张、Gamers56mm徽章2种、ASOBI换装封面。条件及特装盘适用待各店。'],
'https://zutapoke.com/29471/':['氷渡香名江「メタモルフォーゼ」2,500円、2027年3月3日予定，官方店及Gamers已核对。','Animate来源列发售纪念活动申请序列号；具体活动日、抽选规则及资格待核，不创建确定活动。'],
'https://zutapoke.com/29382/':['標FINAL协赞社B2挂画清夏/莉莉娅各3,850円、A3透明海报各1,100円、REVERS应援法被7,700円；5条Gamers单品标题与价格核对，按相同图片合并Animate入口。','文章另有AmiAmi服饰S/M/L/XL尺寸链接；具体款式未逐项核对，不强行对应到法被。原文保留所有尺寸入口。'],
'https://zutapoke.com/29317/':['作者依旧角色经历估算香名江未来抽卡/周边开销的模拟器；是预测，不是新商品清单或已确认价格。','不把预测的Gift毛绒、初期商品、画家主题、抽卡节奏等建为确定商品或发售计划。'],
'https://zutapoke.com/29434/':['第50号：香名江立牌、首张单曲、乖轟首张单曲及標FINAL协赞商品等来源汇总。','Duet第2弹新增乐天Books 5cm亚克力钥匙扣特典线索；实际适用版本待店内。','The 3rd Period直播/演出情报：周报列2027年6月12日至13日，场地票务待官方核实。','11月10日起罗森/Ministop打印周边，使用支援卡插画；具体图案、单价、截止日待官方。','罗森HMV商品价格、随机件与完整组区别见新分类档案；不是同一套组合商品。','むぎゅみに第2弹周报列2027年5月28日，预约、角色、价格待确认。']}
for url,notes in sections.items():
 assert not any(x['url']==url for x in w['articleIndex']);w['articleIndex'].append({'title':doc(url).xpath('string(//h1)'),'url':url,'checkedAt':DATE,'sections':notes,'prices':[],'dates':[]})
a=next(a for a in w['articleIndex'] if a['url']=='https://zutapoke.com/29288/');a.setdefault('sections',[]).append('2026-11-16来源补入乐天Books 5cm亚克力钥匙扣特典渠道，适用版本与当前余量未独立核实。');a['checkedAt']=DATE
key='zuta-week50';w['eventSources'][key]=['学マスまとめ · 第50号（官方待核）',s];eids=[]
for slug,name,start,end,summary in [('third-period','The 3rd Period · 周报演出预告','2027-06-12','2027-06-13','日期来自周报，场地、出演、票务与实际开放时间待官方；不表示开票。'),('print','罗森 / Ministop支援卡插画打印 · 周报线索','2026-11-10','','来源列11月10日启动打印周边，单价、图案及截止日待官方资料。')]:
 eid='gk-week50-'+slug;assert not any(e['id']==eid for e in w['events']);eids.append(eid);w['events'].append({'id':eid,'kind':'event','name':name,'category':'周报线索 / 待官方复核','start':start,'end':end,'endLabel':'结束时间待确认' if not end else '周报日期，官方待核','summary':summary,'reward':'具体内容待官方确认。','cost':'待确认','regions':['日本'],'sourceUrl':s,'sources':[key],'checkedAt':DATE,'activeDates':['按日本时间记录，具体营业或演出时刻未核。'],'steps':['先核对官方后续公告与参与规则。'],'places':[],'notes':['来源线索，不是已核实的售票或实时库存信息。'],'pending':['官方详细公告、费用及参加规则'],'media':{'images':[],'verifiedFacts':[],'resources':[],'sources':[]}})
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':len(ids),'changedProducts':len(changed),'newArticles':6,'changedArticles':1,'newEvents':2,'newChannelLinks':len(newlinks)}});w['retrievedAt']=DATE
assert len(ids)==11
for old,now in zip(before['items'][0]['merch'],w['merch']):
 assert old['id']==now['id'] and now['channels'][:len(old['channels'])]==old['channels']
 if old['id'] not in changed:assert old==now
assert w['events'][:-2]==before['items'][0]['events']
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
 for g in w['merch']:
  vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')];writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProducts':len(ids),'newProductIds':ids,'changedProducts':len(changed),'changedProductIds':changed,'newArticles':list(sections),'changedArticles':['https://zutapoke.com/29288/'],'newEvents':eids,'newChannelLinks':len(newlinks),'sourceErrors':[],'verifiedPages':[x['url'] for x in checks]+[x['url'] for x in verified],'limitations':['预测文章不转成真实商品；週报演出/打印及第2弹手办为待官方核实线索。','乖轟通常盘Gamers1,999円与ASOBI关联2,000円分别保留，不统一改价。','协赞服饰AmiAmi尺寸链接未逐项核款，不冒充已对应商品。'],'ignoredChanges':'其他旧文章仅嵌入游戏活动下次日期更新，不是新增商品。'}
(ROOT/'data/gakumas-monitor-2026-11-16.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k not in ['newProductIds','verifiedPages']},ensure_ascii=False))
