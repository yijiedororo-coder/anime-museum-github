"""Append one verified BOX/reissue channel to the existing thirteen character records."""
import copy,csv,json,re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-06';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
assert not probe['newArticles'] and all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
source='https://zutapoke.com/17245/';u='https://www.dmm.com/mono/hobby/-/detail/=/cid=c261004582/'
change=next(c for c in probe['articleChanges'] if c['url']==source);assert len(change['linksAdded'])==1 and 'c261004582' in change['linksAdded'][0]
d=html.fromstring((CACHE/'dmm-verify.html').read_text(encoding='utf-8'));title=d.xpath('string(//title)')
assert all(t in title for t in ['再販','BOX販売','スイーツver.','13個入'])
for x in d.xpath('//script|//style'):x.drop_tree()
t=re.sub(r'\s+',' ',d.text_content());assert all(s in t for s in ['5,901','2027年2月末','4549502231728','約57mm'])
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];ids=['zuta-db-'+str(i) for i in range(3607,3620)]
for gid in ids:
 g=next(g for g in w['merch'] if g['id']==gid);assert 'トレーディンググリッター缶バッジ スイーツver.' in g['name'];assert all(c['url']!=u for c in g['channels'])
 g['channels'].append({'name':'DMM','url':u,'originalUrl':change['linksAdded'][0],'linkType':'商品页（再版BOX，非角色单卖）','sourceNote':'2026-11-06核查：1BOX 13个、全13种；含税5,901円，参考价7,150円。DMM列2027年2月末前再版发售。此入口不能指定本条角色，不保证一箱集齐；报价、运费与受理状态可能变化。'})
 g.setdefault('sourceObservations',[]).append({'sourceUrl':u,'sourceName':'DMM直接商品页 · 再版BOX核查','price':'再版BOX 5,901円含税，参考7,150円；1BOX13个，不是单枚价格。原单枚550円资料保留。','releaseDate':'本次再版：2027年2月末前发售予定；原版2026年1月记录保留，不覆盖。','size':'约57mm；纸、马口铁；厂商中外鉱業；JAN 4549502231728。','checkedAt':DATE});g['checkedAt']=DATE
article=next(a for a in w['articleIndex'] if a['url']==source);article.setdefault('sections',[]).append('2026-11-06新增DMM甜点主题闪粉徽章再版BOX商品页：1BOX13个、全13种，5,901円含税（参考7,150円）；DMM列2027年2月末前发售予定。旧版角色单枚价格与月份保留；不能指定角色，不保证整箱集齐。');article['checkedAt']=DATE
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'latestUpdate':{'checkedAt':DATE,'newProducts':0,'changedProducts':13,'newChannelLinks':13,'uniqueNewChannelUrls':1,'newArticles':0,'changedArticles':1,'newEvents':0}});w['retrievedAt']=DATE
for old,now in zip(before['items'][0]['merch'],w['merch']):
 assert old['id']==now['id'] and now['channels'][:len(old['channels'])]==old['channels']
 if old['id'] not in ids:assert old==now
 else:assert old['price']==now['price'] and old['releaseDate']==now['releaseDate']
assert len(w['merch'])==len(before['items'][0]['merch']) and w['events']==before['items'][0]['events']
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
p=ROOT/'data/gakumas-products.csv'
with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
for row in rows[1:]:
 if row[0] in ids:
  g=next(g for g in w['merch'] if g['id']==row[0]);row[8]=json.dumps(g['channels'],ensure_ascii=False);row[12]=DATE
with p.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows)
audit={'checkedAt':probe['checkedAt'],'newProducts':0,'changedProducts':13,'changedProductIds':ids,'newChannelLinks':13,'uniqueNewChannelUrls':1,'newArticles':0,'changedArticles':[source],'newEvents':0,'verifiedUrl':u,'verifiedFacts':['再版BOX13个，全13种；非角色单卖，不推定全套保证','5,901円含税 / 参考7,150円','2027年2月末前予定；约57mm；纸、马口铁；中外鉱業；JAN4549502231728'],'sourceErrors':[],'ignoredChanges':'其余18篇仅撤下乐天积分促销文字，未更新商品报价或日期。','limitations':'报价与预约信息为核查时快照；原版单枚资料保留。'}
(ROOT/'data/gakumas-monitor-2026-11-06.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(audit,ensure_ascii=False))
