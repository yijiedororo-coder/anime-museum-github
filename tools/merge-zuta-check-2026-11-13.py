"""Merge November 13 source-backed channel additions; keep inventory unasserted."""
import copy,csv,hashlib,json
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-13';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
assert not probe['newArticles'] and all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];byid={g['id']:g for g in w['merch']};changed=set();added=[]
plans=json.loads((CACHE/'merge-plan.json').read_text(encoding='utf-8'));assert len(plans)==26
for x in plans:
 assert len(x['matches'])==1;g=byid[x['matches'][0]];assert g['id'] in ['zuta-chugai-sweets-acrylstand-202611','zuta-chugai-sweets-keyholder-202611']
 u=parse_qs(urlparse(x['raw']).query)['a8ejpredirect'][0];assert u.startswith('https://colleize.com/lineup/400/') and all(c['url']!=u for c in g['channels'])
 price='1,980円 / 个' if 'acrylstand' in g['id'] else '1,540円 / 个'
 g['channels'].append({'name':'Colleize','url':u,'originalUrl':x['raw'],'linkType':'系列内角色商品页（角色见对应图片）','sourceNote':DATE+'来源报价'+price+'；来源称满7,700円或会员免运费、积分最高10%，资格/地区/实际结算待店内确认。抽查仅返回通用站点页面，未独立核实商品规格或库存。对应图片：'+x['image']});g['checkedAt']=DATE;changed.add(g['id']);added.append(u)
source='https://zutapoke.com/27849/';c=next(c for c in probe['articleChanges'] if c['url']==source);assert len(c['linksAdded'])==1
raw=c['linksAdded'][0];u=parse_qs(urlparse(raw).query)['pc'][0];assert u.startswith('https://books.rakuten.co.jp/search?')
d=html.fromstring((CACHE/(hashlib.sha256(source.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'));image=d.xpath('//main/article//*[contains(@class,"post_content")]//img/@data-src')[0]
gid='zuta-battlespirits-sleeves-ab-202611';assert gid not in byid
w['merch'].append({'id':gid,'kind':'merch','name':'Battle Spirits 官方联名卡套 · 学园偶像大师A / B','originalName':'バトルスピリッツ オフィシャルコラボスリーブ 学園アイドルマスター A：輝けるアイドル / B：初星学園','category':'卡片 / 文具','originalType':'スリーブ,卡套','characters':'A：輝けるアイドル；B：初星学園（具体图案见来源）','price':'A、B各1,100円（来源报价；不是两款合计价）','releaseDate':'来源未列，待确认','size':'尺寸、每包数量来源未列，待确认','description':'卡牌保护套，作为A/B两个款式的系列归档，区别于补充包与起始套牌。新增入口为宽泛搜索，可能混入其他作品，不代表当前有对应商品。','image':image,'imagePlaceholder':True,'sourceUrl':source,'sourceName':'学マスまとめ · Battle Spirits渠道汇总','checkedAt':DATE,'channels':[{'name':'楽天ブックス','url':u,'originalUrl':raw,'linkType':'搜索页（非单品页，可能含其他作品）','sourceNote':'需自行选择学园偶像大师A或B卡套；每包数量、实际价格、库存未独立确认。'}],'sourceRecordIds':[],'variants':[],'specifications':['来源文章宣传图仅作系列参考，非已核实的A/B独立卡套图片。','未从搜索链接推定发售日、材质、尺寸、包数或实时库存。'],'availability':'来源情报，不表示现货。'})
hiro=byid['zuta-figure-13353-6f87df574942'];hiro.setdefault('sourceObservations',[]).append({'sourceName':'学マスまとめ · 手办汇总已发售区','sourceUrl':'https://zutapoke.com/13353/','releaseDate':'来源已将ESPRESTO-Textural layer-篠澤広移入已发售区，仍列2026-11-12；保留既有日期，不表示特定门店库存。','checkedAt':DATE});hiro['checkedAt']=DATE;changed.add(hiro['id'])
notes={'https://zutapoke.com/17245/':'2026-11-13补入Colleize收藏立牌与糖果钥匙扣共26个角色入口，来源各1,980円 / 1,540円；原渠道保留，店内规格与库存未独立确认。',source:'2026-11-13补入Battle Spirits官方联名卡套A「輝けるアイドル」及B「初星学園」系列，各1,100円；入口为乐天Books搜索页，并非单品页。发售日、尺寸、每包数量待确认。','https://zutapoke.com/13353/':'2026-11-13来源将篠澤広ESPRESTO移入已发售区，日期仍为11月12日；没有据此推定门店现货。'}
for url,note in notes.items():
 a=next(a for a in w['articleIndex'] if a['url']==url);a.setdefault('sections',[]).append(note);a['checkedAt']=DATE
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':1,'changedProducts':len(changed),'newChannelLinks':27,'newArticles':0,'changedArticles':3,'newEvents':0}});w['retrievedAt']=DATE
assert len(w['merch'])==len(before['items'][0]['merch'])+1 and w['events']==before['items'][0]['events']
for old,now in zip(before['items'][0]['merch'],w['merch']):
 assert old['id']==now['id'] and now['channels'][:len(old['channels'])]==old['channels']
 if old['id'] not in changed:assert old==now
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
 for g in w['merch']:
  vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')];writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProducts':1,'newProductIds':[gid],'changedProducts':len(changed),'changedProductIds':sorted(changed),'newChannelLinks':27,'newArticles':0,'changedArticles':list(notes),'newEvents':0,'sourceErrors':[],'limitations':['Colleize抽查为通用站点标题，不视为单品规格或库存独立验证。','卡套只提供搜索入口，尺寸/数量/发售日缺失已注明。'],'addedColleizeUrls':added}
(ROOT/'data/gakumas-monitor-2026-11-13.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k!='addedColleizeUrls'},ensure_ascii=False))
