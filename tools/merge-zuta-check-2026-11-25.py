"""Append November 25 Animate shirt sizes using explicit source image matching."""
import copy,csv,hashlib,json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-25';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
assert not probe['newArticles'] and all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
def direct(u):
 for _ in range(4):
  q=parse_qs(urlparse(u).query);v=next((q[k][0] for k in ['a8ejpredirect','lsurl'] if k in q),None)
  if not v:break
  u=v
 return u
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];shirts=[g for g in w['merch'] if g['id'].startswith('zuta-sponsor-shirt-')];source='https://zutapoke.com/29382/';d=html.fromstring((CACHE/(hashlib.sha256(source.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'));imageRole={}
for a in d.xpath('//a'):
 raw=a.get('href','');u=direct(raw)
 if not u.startswith('https://www.neowing.co.jp/'):continue
 matched=[g for g in shirts if any(c['url'].split('/')[-1] in u for c in g['channels'] if c['name']=='NeoWing')]
 if not matched:continue
 col=a.xpath('ancestor::div[contains(concat(" ",normalize-space(@class)," ")," swell-block-column ")][1]')[0];img=col.xpath('preceding-sibling::div[1]//img/@data-src');assert img;imageRole[img[0]]=matched[0]
change=next(c for c in probe['articleChanges'] if c['url']==source);assert len(change['linksAdded'])==20;changed=set();links=[]
for a in d.xpath('//a'):
 raw=a.get('href','')
 if raw not in change['linksAdded']:continue
 col=a.xpath('ancestor::div[contains(concat(" ",normalize-space(@class)," ")," swell-block-column ")][1]')[0];image=col.xpath('preceding-sibling::div[1]//img/@data-src')[0];g=imageRole[image];size=a.text_content().strip();assert size in {'S','M','L','XL'};u=direct(raw);assert 'animate-onlineshop.jp/products/detail.php?' in u and all(c['url']!=u for c in g['channels'])
 g['channels'].append({'name':'Animate','url':u,'originalUrl':raw,'linkType':'商品页（'+g['characters']+' / '+size+'；来源同图同尺码）','sourceNote':DATE+'来源各4,950円；以来源中与NeoWing相同角色图片和尺码按钮对应，未逐页独立核实店内价格、JAN、交付与库存。原已核NeoWing资料及其他渠道保留。'});g['checkedAt']=DATE;changed.add(g['id']);links.append(u)
assert len(changed)==5 and len(links)==20
ar=next(a for a in w['articleIndex'] if a['url']==source);ar.setdefault('sections',[]).append('2026-11-25补入5角色T恤Animate各4尺码，共20个入口；按来源同图同尺码匹配，报价各4,950円，未逐页独立核店内详情。原NeoWing、Colleize链接和历史资料保留。');ar['checkedAt']=DATE
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'latestUpdate':{'checkedAt':DATE,'newProducts':0,'changedProducts':5,'newArticles':0,'changedArticles':1,'newEvents':0,'newChannelLinks':20}});w['retrievedAt']=DATE
for old,now in zip(before['items'][0]['merch'],w['merch']):
 assert old['id']==now['id'] and now['channels'][:len(old['channels'])]==old['channels']
 if old['id'] not in changed:assert old==now
assert len(w['merch'])==len(before['items'][0]['merch']) and w['events']==before['items'][0]['events']
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
p=ROOT/'data/gakumas-products.csv'
with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
for row in rows[1:]:
 if row[0] in changed:row[8]=json.dumps(next(g for g in shirts if g['id']==row[0])['channels'],ensure_ascii=False);row[12]=DATE
with p.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows)
audit={'checkedAt':probe['checkedAt'],'newProducts':0,'changedProducts':5,'changedProductIds':sorted(changed),'newChannelLinks':20,'addedUrls':links,'newArticles':0,'changedArticles':[source],'newEvents':0,'sourceErrors':[],'limitations':['Animate单品未逐页独立核实；角色/尺码依据来源同图同按钮，不能作为库存或交付保证。'],'ignoredChanges':'其余为促销横幅、推荐卡片摘要恢复、已核PalVerse日期措辞及排版，不创建新商品或活动。'}
(ROOT/'data/gakumas-monitor-2026-11-25.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k!='addedUrls'},ensure_ascii=False))
