"""Merge November 10 retailer additions without changing historical price or ordering."""
import copy,csv,hashlib,json,re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote,parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-10';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
assert all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
plans=json.loads((CACHE/'merge-plan.json').read_text(encoding='utf-8'));assert len(plans)==69 and all(x['matches'] for x in plans)
checks=json.loads((CACHE/'retail-check.json').read_text(encoding='utf-8'));assert '1723円' in checks[0]['text'] and '2027年02月' in checks[0]['text'];assert 'お探しのページが見つかりません' in checks[1]['title']
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];byid={g['id']:g for g in w['merch']};changed=set();added=[]
def quote(g,image):
 n=g['name']
 if 'sweets-acrylstand' in g['id']:return '收藏立牌1,980円→1,723円 / 个'
 if 'sweets-keyholder' in g['id']:return '心形糖果钥匙扣1,540円→1,340円 / 个'
 if image.endswith('/image-146.png'):return '随机闪粉徽章BOX 7,150円→6,221円；非角色单卖'
 if image.endswith('/image-147.png'):return '随机签名卡BOX 6,160円→5,359円；非角色/签名版本保证'
 if 'アクリルフィギュアスタンド' in n:return '亚克力人形立牌1,870円→1,627円 / 个'
 if 'B2ハーフ' in n:return 'B2半幅挂画2,750円→2,393円 / 个'
 if 'アートパネル' in n:return '菜单风全息亚克力画板3,300円→2,871円 / 个'
 if 'クリアファイル' in n:return 'A4文件夹550円→479円'
 return '按来源13%优惠报价，具体销售单位和价格见对应商店'
for x in plans:
 museum=x['source']=='https://zutapoke.com/29247/'
 u=parse_qs(urlparse(x['raw']).query)['pc'][0] if museum else 'https://www.neowing.co.jp/'+unquote(x['raw'].split('/A894380/')[1])
 assert u.startswith('https://')
 for gid in x['matches']:
  g=byid[gid];assert all(c['url']!=u for c in g['channels'])
  price='BOX 8,580円（来源报价）' if museum else quote(g,x['image'])
  note=(DATE+'来源新链接；当前乐天Books返回“找不到页面”，不能确认该商品页、报价、免运费或受理状态。原Animate链接保留。') if museum else DATE+'来源报价：'+price+'；来源称一般满1,500円免运费，含挂画或BOX订单满5,000円，地区/条件以店内为准。原报价与月份保留，不代表现货。图片：'+x['image']
  g['channels'].append({'name':'楽天ブックス' if museum else 'NeoWing','url':u,'originalUrl':x['raw'],'linkType':'来源商品链接（本次访问：找不到页面）' if museum else '商品页（来源图片对应；随机款不能指定角色）' if len(x['matches'])>1 else '商品页（来源同款图片对应）','sourceNote':note})
  g.setdefault('sourceObservations',[]).append({'sourceName':'来源新增乐天Books入口（当前失效）' if museum else '学マスまとめ · NeoWing新增渠道报价','sourceUrl':x['source'] if museum else u,'price':price,'description':note,'checkedAt':DATE});g['checkedAt']=DATE;changed.add(gid);added.append((gid,u))
g=byid['zuta-chugai-sweets-acrylstand-202611'];g['sourceObservations'].append({'sourceName':'NeoWing · 花海咲季单品独立核查','sourceUrl':checks[0]['url'],'price':'原价1,980円，核查价1,723円；只对应花海咲季这条单品','releaseDate':'2027年2月（该商店发售标注）；店内预约截止2026-11-23，不能推定所有店铺同日截止。','checkedAt':DATE})
for url,note in [('https://zutapoke.com/17245/','2026-11-10补入68个NeoWing商品页；来源列13%折扣，角色款与BOX分开标注，运费门槛一般1,500円、含挂画或BOX为5,000円。仅咲季收藏立牌单品独立核对到1,723円、2027年2月及店内11月23日截止，其他条目按来源报价。'),('https://zutapoke.com/29247/','2026-11-10来源新增乐天Books BOX报价8,580円并称免运费；直接访问返回找不到页面，已标记链接当前异常，不视为有效在售商品页；原Animate链接保留。')]:
 a=next(a for a in w['articleIndex'] if a['url']==url);a.setdefault('sections',[]).append(note);a['checkedAt']=DATE
source='https://zutapoke.com/29314/';d=html.fromstring((CACHE/(hashlib.sha256(source.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'));assert not any(a['url']==source for a in w['articleIndex'])
w['articleIndex'].append({'title':d.xpath('string(//h1)'),'url':source,'checkedAt':DATE,'sections':['作者关于香名江实装及玩家体验的个人评论，属于观点文章；没有新增商品、价格、销售渠道或已确认活动日期。','文中的未来角色实装推测不作为本馆官方情报，不据此创建商品或活动。'],'prices':[],'dates':[]})
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'latestUpdate':{'checkedAt':DATE,'newProducts':0,'changedProducts':len(changed),'newChannelLinks':len(added),'uniqueNewChannelUrls':len(set(u for _,u in added)),'newArticles':1,'changedArticles':2,'newEvents':0}});w['retrievedAt']=DATE
assert len(w['merch'])==len(before['items'][0]['merch']) and w['events']==before['items'][0]['events']
for old,now in zip(before['items'][0]['merch'],w['merch']):
 assert old['id']==now['id'] and now['channels'][:len(old['channels'])]==old['channels'] and old.get('price')==now.get('price') and old.get('releaseDate')==now.get('releaseDate')
 if old['id'] not in changed:assert old==now
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
p=ROOT/'data/gakumas-products.csv'
with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
for row in rows[1:]:
 if row[0] in changed:row[8]=json.dumps(byid[row[0]]['channels'],ensure_ascii=False);row[12]=DATE
with p.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows)
audit={'checkedAt':probe['checkedAt'],'newProducts':0,'changedProducts':len(changed),'changedProductIds':sorted(changed),'newChannelLinks':len(added),'uniqueNewChannelUrls':len(set(u for _,u in added)),'newArticles':[source],'changedArticles':['https://zutapoke.com/17245/','https://zutapoke.com/29247/'],'newEvents':0,'sourceErrors':[],'retailerLimitations':['乐天Books18894662直接访问为找不到页面，保留来源链接但明确当前异常；未确认为在售渠道。','NeoWing仅独立核对咲季收藏立牌，其他角色/品类报价来自来源文章；不推定实时库存或统一交付月。'],'ignoredChanges':'其余变化为乐天促销横幅及游戏抽卡预测更新，不作为新增周边或官方活动。'}
(ROOT/'data/gakumas-monitor-2026-11-10.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k!='changedProductIds'},ensure_ascii=False))
