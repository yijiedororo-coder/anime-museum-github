"""Fresh November 5 additions; preserve prior records and purchase-link order."""
import copy,csv,hashlib,json
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-05';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert probe['checkedAt'].startswith(DATE) and not probe['errors']
assert all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
def doc(u):return html.fromstring((CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
def direct(u):
 for _ in range(3):
  q=parse_qs(urlparse(u).query);v=next((q[k][0] for k in ['a8ejpredirect','lsurl','goods_url'] if k in q),None)
  if not v:break
  u=v
 return u
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];changed=[];added=[]
def addchannel(g,u,name,original,note):
 assert u.startswith('https://') and all(c['url']!=u for c in g['channels'])
 g['channels'].append({'name':name,'url':u,'originalUrl':original,'linkType':'商品页（按来源角色按钮或同款图片对应）','sourceNote':note});g['checkedAt']=DATE;changed.append(g['id']);added.append(u)
# Explicit character-labelled buttons in source cards avoid relying on visual ordering.
plush='https://zutapoke.com/14433/'
for card in doc(plush).xpath('//article[contains(@class,"gpl-card")]'):
 title=card.xpath('string(.//h3)')
 if 'Starlight Dining' not in title:continue
 prefix='zuta-starlight-251562' if '餃子' in title else 'zuta-starlight-251553'
 for a in card.xpath('.//a'):
  label=a.text_content();suffix='07' if '咲季' in label else '08' if '手毬' in label else '09' if 'ことね' in label else None
  assert suffix
  g=next(g for g in w['merch'] if g['id']==prefix+'-i_sd_'+suffix+'-00-00')
  addchannel(g,direct(a.get('href')),'Animate',a.get('href'),'2026-11-05来源角色按钮对应；来源列服装款3,600円、饺子款2,200円。商店返回空标题页面，未独立核对店内规格、交付、运费及库存；原ASOBI官方单品与已核实日期保留。')
source='https://zutapoke.com/28932/'
for a in doc(source).xpath('//main/article//*[contains(@class,"post_content")]//a[.//img]'):
 raw=a.get('href','')
 if 'affiliate.suruga-ya.jp' not in raw:continue
 images=a.xpath('.//img/@data-src|.//img/@src');image=next(i for i in images if i.startswith('https://zutapoke.com/'))
 g=next(g for g in w['merch'] if g['id'].startswith('zuta-fumo2-') and g['image']==image)
 addchannel(g,direct(raw),'骏河屋',raw,'2026-11-05来源同款图片新增渠道：鼠标19,980円、CXL鼠标垫6,480円、2XL鼠标垫7,480円。来源称1,300円以上免运费，地区及附加条件未独立核实，不代表实时库存。')
assert len(changed)==len(set(changed))==9 and len(added)==9
# This is a new mini-keyholder family, distinct from the older full-size plush.
card=next(c for c in doc(plush).xpath('//article[contains(@class,"gpl-card")]') if c.xpath('string(.//h3)').strip()=='なりきる!?からあげクン ミニぬいキーホルダー')
text=card.text_content();assert all(s in text for s in ['2026年11月10日','2027年1月12日','2027年6月17日'])
official='https://www.lawson.co.jp/campaign/lop_gakuen_idolmaster_2611_goods/'
od=doc(official);hmv='https://www.hmv.co.jp/product/summary/18172/#no1';assert hmv in od.xpath('//a/@href')
gid='zuta-lawson-mini-karage-202611';assert not any(g['id']==gid for g in w['merch'])
g={'id':gid,'kind':'merch','name':'罗森 × 学园偶像大师 · からあげクン迷你毛绒钥匙扣（全13种）','originalName':'なりきる!?からあげクン ミニぬいキーホルダー','category':'毛绒 / 娃娃','originalType':'ミニぬいキーホルダー,ローソン,からあげクン','characters':card.xpath('string(.//p[contains(@class,"gpl-idols")])').strip(),'manufacturer':'销售：ローソン / @Loppi・HMV；生产厂商未标注','price':'各2,420円（含税；官方商品图）','releaseDate':'2027年6月17日交付；预约2026年11月10日10:00至2027年1月12日23:30（日本时间）','size':'约H130mm；聚酯纤维（官方商品图）','description':'官方列全13种，以旧款からあげクン毛绒缩小为迷你挂件；作为一个系列归档，不与2026年9月交付的旧大款合并，不表示13种套装。','specifications':['各2,420円；全13种不等于一套13只。','预约可能在期限内提前结束；HMV入口销售开始前可能跳转首页。','受取窗口为指定交付日起7日；各店适用范围与实际安排请以官方为准。'],'image':'https://zutapoke.com/wp-content/uploads/2026/11/image-73.png','images':[official+'img/block_img01.png'],'sourceUrl':plush,'sourceName':'学マスまとめ毛绒汇总 / 罗森官方商品图核对','verificationUrl':official,'checkedAt':DATE,'channels':[{'name':'官方商品资料','url':official,'linkType':'官方活动商品资料页','sourceNote':'官方商品图已核对13种、各2,420円、H130mm、聚酯纤维及预约交付时间。'},{'name':'HMV&BOOKS online','url':hmv,'linkType':'系列商品入口（非单一角色页）','sourceNote':'官方迷你毛绒购买按钮对应；开售前可能跳转首页，不能据此判断库存。'}],'availability':'预约尚未开始；不代表现货。','sourceRecordIds':[],'variants':[]}
w['merch'].append(g)
if not any(c['name']=='HMV&BOOKS online' for c in w['channelSummary']):w['channelSummary'].append({'name':'HMV&BOOKS online','url':hmv,'note':'官方所链接系列商品入口；开售前可能跳转首页。'})
article='https://zutapoke.com/29101/';assert article in probe['newArticles']
w['articleIndex'].append({'title':doc(article).xpath('string(//h1)'),'url':article,'checkedAt':DATE,'sections':['Starlight Dining中式女仆主题毛绒：服装款各3,600円，饺子款各2,200円；各有咲季、手毬、ことね3角色。','追加6个Animate角色商品页，原ASOBI官方链接及已核实发售日保留；店铺规格、受理状态、运费尚未独立确认。'],'prices':['3,600円','2,200円'],'dates':[]})
for u,note in [(plush,'2026-11-05新增からあげクン迷你钥匙扣系列，全13种；官方核对各2,420円、约H130mm，11月10日10:00至次年1月12日23:30预约，2027年6月17日交付。Starlight Dining追加6个Animate角色链接，旧ASOBI渠道保留。'),(source,'2026-11-05新增骏河屋鼠标、CXL与2XL鼠标垫3个商品入口；来源价19,980円 / 6,480円 / 7,480円，不代表现货。')]:
 a=next(a for a in w['articleIndex'] if a['url']==u);a.setdefault('sections',[]).append(note);a['checkedAt']=DATE
key='lawson-202611-official';w['eventSources'][key]=['罗森官方 · 2026年11月Loppi/HMV商品',official]
eid='gk-lawson-mini-order-202611';assert not any(e['id']==eid for e in w['events'])
w['events'].append({'id':eid,'kind':'event','name':'罗森からあげクン迷你毛绒 · 预约','category':'周边受注 / 销售提醒','start':'2026-11-10T10:00','end':'2027-01-12T23:30','endLabel':'预约截止（可能提前结束）','summary':'@Loppi・HMV限定，迷你毛绒钥匙扣全13种、各2,420円；官方安排2027年6月17日交付。','reward':'购买商品；不属于免费赠品或整套保证。','cost':'每只2,420円含税，运费和受取条件依渠道确认。','regions':['日本'],'sourceUrl':official,'sources':[key],'checkedAt':DATE,'activeDates':['日本时间；交付日2027-06-17，与预约开始日区分。'],'steps':['开售后查看HMV对应系列入口或适用店铺Loppi。','核对角色、数量、费用与取货店，完成个人购买前再次确认规则。'],'places':[],'notes':['可能在预约期内提前结束。','HMV入口开售前可能跳转首页；不作现货判断。'],'pending':['各角色实时受理状态、实际配送与运费'],'media':{'images':[],'verifiedFacts':['官方图片列预约11月10日10:00至1月12日23:30、交付6月17日。'],'resources':[{'label':'HMV系列入口','url':hmv}],'sources':[]}})
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':1,'changedProducts':9,'newChannelLinks':9,'newArticles':1,'changedArticles':2,'newEvents':1}});w['retrievedAt']=DATE
assert [g['id'] for g in w['merch'][:-1]]==[g['id'] for g in before['items'][0]['merch']]
for old,now in zip(before['items'][0]['merch'],w['merch']):
 assert now['channels'][:len(old['channels'])]==old['channels']
 if old['id'] not in changed:assert old==now
assert w['events'][:-1]==before['items'][0]['events']
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
 for g in w['merch']:
  vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')]
  writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProducts':1,'newProductIds':[gid],'changedProducts':9,'changedProductIds':changed,'newChannelLinks':9,'addedLinks':added,'newArticles':[article],'changedArticles':[plush,source],'newEvents':[eid],'sourceErrors':[],'limitations':['Animate六页返回无商品标题的空壳内容，链接按来源角色按钮对应，未声称独立核实店内规格或库存。','骏河屋按来源同款图片对应，店内条件未独立核实。','其余文章变化为乐天促销横幅、推荐摘要或排版，未当作商品价格更新。'],'officialVerification':{'url':official,'images':[official+'img/03.png',official+'img/block_img01.png'],'facts':['全13种；各2,420円；约H130mm；聚酯纤维','2026-11-10 10:00至2027-01-12 23:30预约；2027-06-17交付']}}
(ROOT/'data/gakumas-monitor-2026-11-05.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k not in ['addedLinks','changedProductIds']},ensure_ascii=False))
