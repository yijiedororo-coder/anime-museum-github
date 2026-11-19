"""Append thirty independently read Gamers pages, keeping shop/BOX prices distinct."""
import copy,csv,hashlib,json,re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-19';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
checks=json.loads((CACHE/'retail-check.json').read_text(encoding='utf-8'));plans={x['url']:x for x in json.loads((CACHE/'merge-plan.json').read_text(encoding='utf-8'))};assert len(checks)==len(plans)==30 and all('text' in x for x in checks)
# The retried article is compared after a complete read, so a disconnected response is not treated as a change.
u='https://zutapoke.com/10207/';filename=hashlib.sha256(u.encode()).hexdigest()+'.html';assert (CACHE/filename).exists()
from lxml import html
def content(path):
 d=html.fromstring(path.read_text(encoding='utf-8'));a=d.xpath('//main/article/*[contains(@class,"post_content")]')[0]
 for x in a.xpath('.//script|.//style|.//ins'):x.drop_tree()
 return re.sub(r'\s+',' ',a.text_content()).strip(),a.xpath('.//a/@href')
assert content(CACHE/filename)==content(ROOT/'tools/zuta-monitor/2026-11-18'/filename)
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];byid={g['id']:g for g in w['merch']};changed=set();added=[];source='https://zutapoke.com/29552/'
for x in checks:
 t=x['title'];text=x['text'];assert 'ギアビート' in t and '2027/03/26' in text
 if '公式アクリルスタンド' in t:gid='zuta-gearbeat-category-1-202611'
 elif '公式ぬいぐるみ' in t:gid='zuta-gearbeat-plush-2026'
 elif '公式キャラファイングラフ' in t:gid='zuta-gearbeat-category-5-202611'
 elif '公式懐中時計風' in t:gid='zuta-gearbeat-category-6-202611'
 elif 'トレーディングブローチ' in t:gid='zuta-gearbeat-category-10-202611'
 elif 'トレーディングコレクション' in t:gid='zuta-gearbeat-category-11-202611'
 else:raise AssertionError(t)
 g=byid[gid];assert all(c['url']!=x['url'] for c in g['channels']);price=re.search(r'[\d,]+円\(税込\)',text)[0];random='トレーディング' in t
 name=t.split(' | ')[0];note=DATE+'已核对标题、'+price+'及2027-03-26标注；'+('仅BOX销售，展示单价不是已核对BOX总价；不保证齐套。' if random else '实际交付和库存以商店最新状态为准。')
 g['channels'].append({'name':'Gamers','url':x['url'],'originalUrl':plans[x['url']]['raw'],'linkType':'商品页（BOX销售）' if random else '商品页（'+name+'）','sourceNote':note});g['checkedAt']=DATE;changed.add(gid);added.append(x['url'])
 if random:
  if 'ブローチ' in t:
   assert '1BOX:13個入り' in text;spec='Gamers：BOX13个/全13种，约W64×H93mm；PET、马口铁、铁、锌合金，附链条。'
  else:
   assert '1BOX:26個入り' in text;spec='Gamers：BOX26个/全26种（全息13种+PET13种），约H130×W80mm，纸/ PET。'
  g.setdefault('sourceObservations',[]).append({'sourceName':'Gamers · BOX资料独立核对','sourceUrl':x['url'],'price':price+'展示单价；BOX总价未确认。Animate原来源报价保留（卡片599円，与本店600円分开）。' if 'コレクション' in t else price+'展示单价；BOX总价未确认。','size':spec,'releaseDate':'2027-03-26（Gamers）','description':'店铺明确1BOX也可能无法集齐所有款式；此规格不自动套用其他店铺。','checkedAt':DATE})
a=next(a for a in w['articleIndex'] if a['url']==source);a.setdefault('sections',[]).append('2026-11-19追加30个Gamers已核对商品页：立牌13、毛绒13、精细画/怀表风挂件各1、随机徽章/卡片BOX各1。均列2027年3月26日。Gamers收藏卡展示单价600円，Animate来源599円分别保留；BOX徽章13个、卡片26个，均不保证齐套，BOX总价仍需核。');a['checkedAt']=DATE
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'latestUpdate':{'checkedAt':DATE,'newProducts':0,'changedProducts':len(changed),'newArticles':0,'changedArticles':1,'newEvents':0,'newChannelLinks':30}});w['retrievedAt']=DATE
assert len(changed)==6 and len(w['merch'])==len(before['items'][0]['merch']) and w['events']==before['items'][0]['events']
for old,now in zip(before['items'][0]['merch'],w['merch']):
 assert old['id']==now['id'] and now['channels'][:len(old['channels'])]==old['channels']
 if old['id'] not in changed:assert old==now
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
p=ROOT/'data/gakumas-products.csv'
with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
for row in rows[1:]:
 if row[0] in changed:row[8]=json.dumps(byid[row[0]]['channels'],ensure_ascii=False);row[12]=DATE
with p.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows)
audit={'checkedAt':probe['checkedAt'],'newProducts':0,'changedProducts':6,'changedProductIds':sorted(changed),'newChannelLinks':30,'verifiedUrls':added,'newArticles':0,'changedArticles':[source],'newEvents':0,'sourceErrors':[],'retry':'10207首次断开，单次重试成功，完整正文与上次相同。','limitations':['Gamers随机卡片600円和Animate来源599円分别保留，不统一改价。','店铺提供BOX13/26个与不齐套规则，展示单价不当作BOX总价。'],'ignoredChanges':'28955仅关联口号本团队称谓修正，无商品事实变化。'}
(ROOT/'data/gakumas-monitor-2026-11-19.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k!='verifiedUrls'},ensure_ascii=False))
