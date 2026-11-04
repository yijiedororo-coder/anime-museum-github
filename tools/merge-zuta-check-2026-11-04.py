"""Merge freshly checked article and search-channel additions, without new SKUs."""
import copy,csv,hashlib,json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-04'
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
CACHE=ROOT/'tools/zuta-monitor'/DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'))
assert probe['checkedAt'].startswith(DATE) and not probe['errors']
assert all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
p=ROOT/'data/gakumas-data.js'
data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
before=copy.deepcopy(data);w=data['items'][0]
pal=next(g for g in w['merch'] if g['id']=='zuta-figure-13353-921b343e94d5')
change=next(c for c in probe['articleChanges'] if c['url']=='https://zutapoke.com/13353/')
assert len(change['linksAdded'])==2
for u in change['linksAdded']:
    assert 'vol.2' in u and ('amazon.co.jp/s?' in u or 'jp.mercari.com/search?' in u)
    assert not any(c['url']==u for c in pal['channels'])
    pal['channels'].append({'name':'Amazon' if 'amazon.co.jp' in u else 'Mercari（二手）','url':u,'linkType':'搜索页','sourceNote':'2026-11-04来源新增PalVerse第二弹搜索入口；搜索结果可能含单件、BOX或二手商品，价格、品相及库存需逐项确认。'})
pal['checkedAt']=DATE
pal.setdefault('sourceObservations',[]).append({'sourceUrl':'https://zutapoke.com/13353/','sourceName':'手办汇总：第二弹移入已发售区','releaseDate':'来源已改为2026-10-30，与本馆此前官方核实日期一致；保留原日期。','checkedAt':DATE})
source='https://zutapoke.com/29016/'
assert source in probe['newArticles']
d=html.fromstring((CACHE/(hashlib.sha256(source.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
assert 'ウエハース4' in d.xpath('string(//h1)')
wafer=next(g for g in w['merch'] if g['id']=='zuta-wafer4-4570117932168')
wafer.setdefault('sourceObservations',[]).append({'sourceUrl':source,'sourceName':'学マスまとめ · 威化饼4个人开箱','description':'2026-11-03发布的个人开箱，展示卡面与背面，并记录同一箱内出现重复卡。仅为该作者样本，不能推定固定稀有度配率、整箱保证或全套保证；本馆保留此前官方核实的29种、单包176円及2026-11-02发售日期。','checkedAt':DATE})
wafer['checkedAt']=DATE
assert not any(a['url']==source for a in w['articleIndex'])
w['articleIndex'].append({'title':d.xpath('string(//h1)'),'url':source,'checkedAt':DATE,'sections':['威化饼4个人开箱与卡面、背面实拍；文章于11月3日记述发售次日收到商品，正式发售日期仍为11月2日。','作者样本出现箱内重复卡；开箱数量和结果不代表厂家保证的封入配率，不保证一箱集齐。','链接至已入库的威化饼4系列，避免将开箱文章重复建为新商品；保留官方29种、单包176円资料。'],'prices':[],'dates':['2026-11-02']})
a=next(a for a in w['articleIndex'] if a['url']=='https://zutapoke.com/13353/')
a.setdefault('sections',[]).append('2026-11-04核查：PalVerse第二弹移入已发售区，来源日期修正为10月30日；本馆此前已按官方资料采用该日期。本次追加Amazon和Mercari搜索入口，不代表实时库存。');a['checkedAt']=DATE
a=next(a for a in w['articleIndex'] if a['url']=='https://zutapoke.com/15226/')
a.setdefault('sections',[]).append('2026-11-04核查：来源开头将威化饼3发售年份由2025更正为2026（2月2日）；不影响威化饼4的11月2日发售日期。');a['checkedAt']=DATE
changed=[pal['id'],wafer['id']]
for old,new in zip(before['items'][0]['merch'],w['merch']):
    assert old['id']==new['id'] and new['channels'][:len(old['channels'])]==old['channels']
    if old['id'] not in changed:assert old==new
assert len(w['merch'])==len(before['items'][0]['merch']) and w['events']==before['items'][0]['events']
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'latestUpdate':{'checkedAt':DATE,'newProducts':0,'changedProducts':2,'newChannelLinks':2,'newArticles':1,'changedArticles':2,'newEvents':0}});w['retrievedAt']=DATE
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
    (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
csvpath=ROOT/'data/gakumas-products.csv'
with csvpath.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
for row in rows[1:]:
    if row[0] in changed:
        g=next(g for g in w['merch'] if g['id']==row[0]);row[8]=json.dumps(g['channels'],ensure_ascii=False);row[12]=DATE
with csvpath.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows)
audit={'checkedAt':probe['checkedAt'],'newProducts':0,'changedProducts':2,'changedProductIds':changed,'newChannelLinks':2,'newArticles':[source],'changedArticles':['https://zutapoke.com/13353/','https://zutapoke.com/15226/'],'newEvents':0,'sourceErrors':[],'ignoredChanges':'其余变动为相关文章摘要、已结束游戏活动片段和排版修正，不作为新周边或新活动。','limitations':'开箱为个人样本；新增入口为搜索页，报价与库存未独立核实。'}
(ROOT/'data/gakumas-monitor-2026-11-04.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
