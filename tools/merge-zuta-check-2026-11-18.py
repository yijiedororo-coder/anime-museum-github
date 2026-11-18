"""Merge fresh November 18 Gearbeat categories and image/size-matched shirt channels."""
import copy,csv,hashlib,json,re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-18';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
assert all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
def doc(u):return html.fromstring((CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
def direct(u):
 for _ in range(4):
  q=parse_qs(urlparse(u).query);v=next((q[k][0] for k in ['a8ejpredirect','lsurl'] if k in q),None)
  if not v:break
  u=v
 return u
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];changed=set();ids=[];added=[]
def link(g,u,name,kind,note,raw):
 if any(c['url']==u for c in g['channels']):return
 g['channels'].append({'name':name,'url':u,'originalUrl':raw,'linkType':kind,'sourceNote':note});g['checkedAt']=DATE;added.append(u)
 if g['id'] not in ids:changed.add(g['id'])
# Shirt role comes from the same source picture in the already verified NeoWing block.
s='https://zutapoke.com/29382/';d=doc(s);shirts=[g for g in w['merch'] if g['id'].startswith('zuta-sponsor-shirt-')];imageRole={}
for a in d.xpath('//a'):
 raw=a.get('href','');u=direct(raw)
 if not u.startswith('https://www.neowing.co.jp/'):continue
 match=[g for g in shirts if any(c['url'] in u or c['url'].split('/')[-1] in u for c in g['channels'])]
 if not match:continue
 col=a.xpath('ancestor::div[contains(concat(" ",normalize-space(@class)," ")," swell-block-column ")][1]')[0];im=col.xpath('preceding-sibling::div[1]//img/@data-src');assert im
 imageRole[im[0]]=match[0]
change=next(c for c in probe['articleChanges'] if c['url']==s);assert len(change['linksAdded'])==20
for a in d.xpath('//a'):
 raw=a.get('href','')
 if raw not in change['linksAdded']:continue
 col=a.xpath('ancestor::div[contains(concat(" ",normalize-space(@class)," ")," swell-block-column ")][1]')[0];image=col.xpath('preceding-sibling::div[1]//img/@data-src')[0];g=imageRole[image];size=a.text_content().strip();assert size in {'S','M','L','XL'}
 link(g,direct(raw),'Colleize','商品页（'+g['characters']+' / '+size+'；来源同图同尺码）',DATE+'来源各4,950円；按与NeoWing区相同图片及按钮尺码匹配。店内规格、JAN与库存未独立核实，原NeoWing已核资料保留。',raw)
# Group merchandise by source price labels; preserve every linked image/product pairing.
s='https://zutapoke.com/29552/';a=doc(s).xpath('//main/article/*[contains(@class,"post_content")]')[0];groups={};current=None
for x in a.iter():
 if x.tag=='p':
  t=re.sub(r'\s+',' ',x.text_content()).strip()
  if (t.startswith('公式') or t.startswith('トレーディング')) and '円' in t:current=t;groups.setdefault(t,[])
 if x.tag=='a' and current and x.get('href','').startswith('https://px.a8.net/'):
  raw=x.get('href');u=direct(raw);assert 'animate-onlineshop.jp/products/detail.php?' in u
  imgs=[i for i in x.xpath('.//img/@data-src|.//img/@src') if i.startswith('https://')];groups[current].append({'url':u,'raw':raw,'label':x.text_content().strip(),'image':imgs[0] if imgs else ''})
assert len(groups)==12 and all(groups.values())
official='https://idolmaster-official.jp/news/01_20322';assert '2027年3月26日' in doc(official).text_content()
for index,(title,entries) in enumerate(groups.items()):
 if title.startswith('公式ぬいぐるみ'):
  g=next(g for g in w['merch'] if g['id']=='zuta-gearbeat-plush-2026')
 else:
  gid='zuta-gearbeat-category-'+str(index)+'-202611';assert not any(g['id']==gid for g in w['merch']);ids.append(gid)
  imgs=list(dict.fromkeys(x['image'] for x in entries if x['image']));price=re.search(r'[\d,]+円',title)[0];random='トレーディング' in title
  g={'id':gid,'kind':'merch','name':'Gearbeat Concerto · '+title.split('（')[0].split('【')[0],'originalName':title,'category':'卡片 / 文具' if 'カード' in title else '徽章' if '缶バッジ' in title else '亚克力立牌' if 'スタンド' in title else '服饰 / 生活周边' if any(k in title for k in ['スカーフ','Tシャツ']) else '其他周边','originalType':title,'characters':'系列款式，具体角色见来源各图片；未按排列顺序猜测角色','price':price+'（来源单件/单包参考，Animate仅BOX购买；BOX总价与数量未独立确认）' if random else '各'+price+'（来源报价；不同款式/尺码单件，非整套）','releaseDate':'系列官方整体发售2027年3月26日予定；本店各单品交付未独立核对','size':'M/L/XL（来源按钮；具体尺寸未列）' if 'Tシャツ' in title else '来源未列完整规格，待确认','description':'按来源品类归档，每张图保留对应购买入口；不同角色、图案、尺码不是一个组合包。Animate抽查返回空详情，店内规格与受理状态未独立确认。','image':imgs[0] if imgs else w['poster'],'images':imgs,'imagePlaceholder':not bool(imgs),'sourceUrl':s,'sourceName':'学マスまとめ · Gearbeat通販汇总','verificationUrl':official,'checkedAt':DATE,'channels':[],'sourceRecordIds':[],'variants':[],'availability':'不代表实时库存，随机商品不保证BOX集齐。','specifications':['官方整体时间：12月24日快闪先行，2027年3月26日正式发售予定；ASOBI受注条件不能自动套用Animate。']}
  if random:g['specifications'].append('来源单价不是BOX售价；全13种徽章/全26种卡片不等于单盒保证全套。')
  w['merch'].append(g)
 for x in entries:
  if 'Tシャツ' in title and not x['label']:
   x['label']=next((v['label'] for v in entries if v['url']==x['url'] and v['label']), '')
  note=DATE+'来源图片对应：'+x['image'] if x['image'] else DATE+'来源按钮：'+x['label']
  link(g,x['url'],'Animate','商品页（BOX；BOX总额/数量待核）' if 'トレーディング' in title else '商品页（'+x['label']+'尺码）' if 'Tシャツ' in title else '系列内商品页（角色/款式见对应图片）',note+'；单品规格、版本和库存未独立确认。',x['raw'])
 if g['id']=='zuta-gearbeat-plush-2026':
  g['images']=list(dict.fromkeys(g.get('images',[])+[x['image'] for x in entries if x['image']]))
  g.setdefault('sourceObservations',[]).append({'sourceName':'学マスまとめ · 新增Animate毛绒渠道','sourceUrl':s,'price':'各3,600円（来源）','description':'13张新来源图及13个商品页，原ASOBI链接保留；未把ASOBI特典及受注截止套用到Animate。','checkedAt':DATE})
assert len(ids)==11
for url,note in [('https://zutapoke.com/29382/','2026-11-18新增Colleize全彩T恤20个尺寸入口，按来源与NeoWing相同图片及S/M/L/XL匹配；保留已核JAN与原购买链接，未独立核店内详情。')]:
 ar=next(ar for ar in w['articleIndex'] if ar['url']==url);ar.setdefault('sections',[]).append(note);ar['checkedAt']=DATE
assert not any(ar['url']==s for ar in w['articleIndex'])
w['articleIndex'].append({'title':doc(s).xpath('string(//h1)'),'url':s,'checkedAt':DATE,'sections':['Gearbeat完整Animate品类：毛绒3,600円、立牌2,500円、亚克力挂件1,100円、Q版PU挂件1,300円、亚克力画板3,999円。','精细画19,800円、怀表风挂件6,800円、PU卡套1,870円、丝巾1,999円、长袖T恤6,800円（M/L/XL）。','随机胸针风徽章全13种单价1,100円、收藏卡全26种单价599円；入口仅BOX，单价不能当BOX总价，不推定齐套。','Animate单品详情未独立核实，ASOBI的12月7日受注条件和特典不能自动套用到此渠道。'],'prices':[],'dates':[]})
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':len(ids),'changedProducts':len(changed),'newArticles':1,'changedArticles':1,'newEvents':0,'newChannelLinks':len(added)}});w['retrievedAt']=DATE
for old,now in zip(before['items'][0]['merch'],w['merch']):
 assert old['id']==now['id'] and now['channels'][:len(old['channels'])]==old['channels']
 if old['id'] not in changed:assert old==now
assert w['events']==before['items'][0]['events']
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
 for g in w['merch']:
  vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')];writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProducts':len(ids),'newProductIds':ids,'changedProducts':len(changed),'changedProductIds':sorted(changed),'newArticles':[s],'changedArticles':['https://zutapoke.com/29382/'],'newEvents':0,'newChannelLinks':len(added),'sourceErrors':[],'limitations':['Animate抽查无单品详情，商品按来源图片匹配；BOX数量总额、单品交付与特典均待核。','Colleize按同图同尺寸匹配，店内独立规格/JAN待核。'],'ignoredChanges':'28955仅关联文章制作团队称谓变更，无商品或活动事实变化。'}
(ROOT/'data/gakumas-monitor-2026-11-18.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(audit,ensure_ascii=False))
