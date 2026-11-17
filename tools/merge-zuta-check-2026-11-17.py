"""Import six November 17 product records with explicit shirt-size variants."""
import copy,csv,hashlib,json,re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-17';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
assert all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
def doc(u):return html.fromstring((CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];ids=[]
source='https://zutapoke.com/14433/';card=next(c for c in doc(source).xpath('//article[contains(@class,"gpl-card")]') if '氷渡香名江' in c.xpath('string(.//h3)'));t=card.text_content();assert all(k in t for k in ['4,950','2026年11月16日','2027年5月'])
gid='zuta-kanae-chibi-pouch-202611';assert not any(g['id']==gid for g in w['merch']);w['merch'].append({'id':gid,'kind':'merch','name':'ちびぐるみ＆收纳包套装 · 氷渡香名江','originalName':'ちびぐるみ＆ポーチセット 氷渡香名江','category':'毛绒 / 娃娃','originalType':'ちびぐるみ,ポーチセット','characters':'氷渡香名江','price':'4,950円含税（来源）','releaseDate':'2027年5月予定；来源受注开始2026年11月16日','size':'尺寸及各部件规格来源未列，待确认','description':'毛绒与收纳包套装，来源列受注销售；截止日期、厂商及直接购买链接未列，不能当作娃娃机景品或推定现货。','image':card.xpath('.//img/@data-src')[0],'sourceUrl':source,'sourceName':'学マスまとめ · 毛绒汇总','checkedAt':DATE,'channels':[],'sourceRecordIds':[],'variants':[],'availability':'受注/发货信息为来源记录，直接购买渠道与实时受理状态待确认。'});ids.append(gid)
checks=json.loads((CACHE/'shirt-check.json').read_text(encoding='utf-8'));assert len(checks)==20 and all('text' in x for x in checks);groups={}
for x in checks:
 m=re.search(r'学園アイドルマスター (.+?) フルカラーTシャツ ブラック / (S|M|L|XL)',x['title']);assert m
 role,size=m.groups();assert '4950円' in x['text'] and '2027年02月' in x['text'];groups.setdefault(role,[]).append((size,x))
assert len(groups)==5
for role,variants in groups.items():
 assert {s for s,_ in variants}=={'S','M','L','XL'}
 gid='zuta-sponsor-shirt-'+variants[0][1]['url'].split('-')[-1];assert not any(g['id']==gid for g in w['merch'])
 d=doc(variants[0][1]['url']);imgs=d.xpath('//meta[@property="og:image"]/@content');img=imgs[0] if imgs and imgs[0].startswith('https://') else w['poster']
 g={'id':gid,'kind':'merch','name':'標FINAL协赞 · '+role+' 全彩T恤（黑色）','originalName':'学園アイドルマスター '+role+' フルカラーTシャツ ブラック','category':'服饰 / 生活周边','originalType':'フルカラーTシャツ','characters':role,'manufacturer':'コスパ（NeoWing页面销售标注）','price':'各尺码4,950円（来源与NeoWing核查一致）','releaseDate':'2027年2月（NeoWing）；该店预约截止2026-12-01，不推定其他商店同日截止','size':'S/M/L/XL；綿100%。S约衣长65×身宽49×袖长19cm；M 69×52×20；L 73×55×22；XL 77×58×24（NeoWing）','description':'同一角色的4种尺码集中保存；不是S/M/L/XL四件套，不能与REVERS应援法被混淆。','image':img,'imagePlaceholder':img==w['poster'],'sourceUrl':'https://zutapoke.com/29382/','sourceName':'学マスまとめ / NeoWing逐尺码核对','checkedAt':DATE,'channels':[],'variants':[],'sourceRecordIds':[],'availability':'核查时店铺资料，不代表实时库存；实际结算、运费及交付另核。'}
 for size,x in variants:
  jan=re.search(r'JAN/ISBN\s*(\d{13})',x['text']);assert jan
  g['variants'].append({'size':size,'jan':jan[1],'url':x['url'],'price':'4,950円','releaseDate':'2027年2月','checkedAt':DATE})
  g['channels'].append({'name':'NeoWing','url':x['url'],'linkType':'商品页（'+role+' / '+size+'）','sourceNote':'已核对本尺码标题、JAN、4,950円及2027年2月标注；T恤不可用邮件便，来源称单件送料589円起、满5,000円免运费，地区/附加条件以店内为准。'})
 w['merch'].append(g);ids.append(gid)
for url,note in [('https://zutapoke.com/14433/','2026-11-17新增氷渡香名江ちびぐるみ＆收纳包套装：4,950円，来源列11月16日受注开始、2027年5月交付予定。直接购买页及截止日未提供，已注明。'),('https://zutapoke.com/29382/','2026-11-17补全5角色全彩黑色T恤，各4,950円，NeoWing共20条S/M/L/XL单品逐页核对并保留各JAN；2027年2月予定，店内12月1日截止。AmiAmi尺寸入口未逐项核实，不与应援法被乱配。')]:
 a=next(a for a in w['articleIndex'] if a['url']==url);a.setdefault('sections',[]).append(note);a['checkedAt']=DATE
url='https://zutapoke.com/16525/';assert url in probe['newArticles'] and not any(a['url']==url for a in w['articleIndex'])
w['articleIndex'].append({'title':doc(url).xpath('string(//h1)'),'url':url,'checkedAt':DATE,'sections':['游戏内技能卡插画角色差分汇总，按R、SR、SSR和传奇卡分类，补入香名江/老师等比较。','这是游戏资料与作者解读，不是实体卡片销售清单；不据此新增实体周边或认定解释为官方设定。'],'prices':[],'dates':[]})
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':6,'changedProducts':0,'newArticles':1,'changedArticles':2,'newEvents':0,'newChannelLinks':20}});w['retrievedAt']=DATE
assert len(ids)==6 and w['merch'][:-6]==before['items'][0]['merch'] and w['events']==before['items'][0]['events']
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
 for g in w['merch']:
  vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')];writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProducts':6,'newProductIds':ids,'changedProducts':0,'newArticles':[url],'changedArticles':['https://zutapoke.com/14433/','https://zutapoke.com/29382/'],'newEvents':0,'newChannelLinks':20,'verifiedShirtSizes':20,'sourceErrors':[],'limitations':['香名江毛绒截止日、尺寸与直接购买页未列，仅记录来源情报。','游戏卡图差分只作资料索引，不当实体周边。','T恤AmiAmi尺码链接未逐页核对；NeoWing20条已核对，不混入法被。']}
(ROOT/'data/gakumas-monitor-2026-11-17.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(audit,ensure_ascii=False))
