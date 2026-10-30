"""Import two source retailer additions and an explicitly unofficial fan project."""
import copy,csv,hashlib,json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-10-30';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert probe['checkedAt'].startswith(DATE) and not probe['errors']
assert all(not v['new'] and not v['changed'] and not v['removed'] for v in probe['csvChanges'].values())
def doc(u):return html.fromstring((CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
path=ROOT/'data/gakumas-data.js';data=json.loads(path.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0]
g=next(g for g in w['merch'] if g['id']=='gakumas-18');assert g['sourceUrl']=='https://zutapoke.com/27755/'
change=next(c for c in probe['articleChanges'] if c['url']==g['sourceUrl']);assert len(change['linksAdded'])==2
added=[]
for original in change['linksAdded']:
    raw='https:'+original if original.startswith('//') else original;q=parse_qs(urlparse(raw).query)
    u=q.get('vc_url',q.get('a8ejpredirect',[]))[0]
    assert urlparse(u).netloc in ['anime-store.jp','colleize.com']
    assert all(c['url']!=u for c in g['channels'])
    name='AnimeStore' if 'anime-store.jp' in u else 'Colleize'
    c={'name':name,'url':u,'originalUrl':raw,'linkType':'商品页（来源同款手办图示对应；店内规格未独立核对）','sourceNote':DATE+'来源汇总新增渠道，标价22,000円并称免运费；适用地区、条件、实际结算价与库存请在商店确认。'}
    g['channels'].append(c);added.append(c)
g.setdefault('sourceObservations',[]).append({'sourceName':'学マスまとめ · 新增AnimeStore / Colleize渠道','sourceUrl':g['sourceUrl'],'price':'两店来源报价22,000円；原有其他店铺报价保留','releaseDate':'本次来源更新未另列日期；保留原记录','checkedAt':DATE});g['checkedAt']=DATE
a=next(a for a in w['articleIndex'] if a['url']==g['sourceUrl']);a.setdefault('sections',[]).append('2026-10-30新增AnimeStore与Colleize商品链接，来源报价各22,000円并称免运费；店内条件未独立核实，不代表实时库存。');a['checkedAt']=DATE
source='https://zutapoke.com/14805/';d=doc(source);body=d.xpath('//main/article/*[contains(concat(" ",normalize-space(@class)," ")," post_content ")]')[0];text=body.text_content()
assert '非公式' in text and '無料配布' in text and 'HPS標' in text
resources=[('初星音乐祭版协赞说明（粉丝企划）','https://twipla.jp/events/745162'),('標FINAL版协赞说明（粉丝企划）','https://twipla.jp/events/735372')]
for _,u in resources:assert u in body.xpath('.//a/@href') or u in text
assert not any(a['url']==source for a in w['articleIndex'])
w['articleIndex'].append({'title':d.xpath('string(//h1)'),'url':source,'checkedAt':DATE,'sections':['非官方粉丝应援口号本企划：初星音乐祭版再配发及標FINAL版新配发，文章称通过HPS標合同展示企划免费配发。','初星音乐祭版称为最终配发、内容修正；標FINAL版为另一版本。两份Twipla协赞说明分别保留，协赞不等于购买普通官方周边。','文章称可为协赞者留置，標FINAL版另称可邮寄；具体金额、截止时间、库存、现场日期与地址尚未独立核实。','本馆仅收录企划概要和来源，不转载口号本、歌词或文章中的法律解释。'],'prices':[],'dates':[]})
eid='gk-fan-callguide-hps-shirube-202610';assert not any(e['id']==eid for e in w['events'])
w['eventSources']['zuta-fan-14805']=['学マスまとめ · 非官方粉丝口号本企划',source]
w['events'].append({'id':eid,'kind':'event','name':'HPS標 · 粉丝应援口号本配发企划（非官方）','category':'粉丝企划（非官方）','start':'','end':'','endLabel':'配发日期、地点待确认','summary':'来源文章介绍初星音乐祭版口号本再配发及標FINAL版新配发，称在HPS標合同展示企划免费配发。该企划由粉丝组织，不是游戏官方物贩或官方活动。','reward':'两种不同版本的纸质应援口号本；内容、数量与配发条件以企划方最新说明为准。','cost':'来源称现场免费配发；协赞属于自愿支持，金额、留置及邮寄条件待确认，本馆不代为报名或付款。','regions':['日本'],'sourceUrl':source,'sources':['zuta-fan-14805'],'checkedAt':DATE,'activeDates':['2026-10-30日本时间核查；文章日期不作为活动发生日期。'],'steps':['查看原文及对应版本的Twipla企划说明。','参与前自行确认现场日期、地址、配发数量、留置及邮寄条件。'],'places':[],'notes':['明确区分非官方粉丝企划和官方联名、物贩。','本馆不转载口号本、歌词或法律解释。'],'pending':['具体配发日期、场地与入场条件','各版本数量及当前是否仍受理协赞、留置或邮寄'],'media':{'images':[],'verifiedFacts':['来源文章称初星音乐祭版为最终配发修订版，另有標FINAL版。'],'resources':[{'label':label,'url':u} for label,u in resources],'sources':[]}})
report=w['collectionReport'];report.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'latestUpdate':{'checkedAt':DATE,'newProducts':0,'changedProducts':1,'newChannelLinks':2,'newArticles':1,'changedArticles':1,'newEvents':1}});w['retrievedAt']=DATE
assert len(w['merch'])==len(before['items'][0]['merch'])
for prev,now in zip(before['items'][0]['merch'],w['merch']):
    assert prev['id']==now['id'];assert now['channels'][:len(prev['channels'])]==prev['channels']
    if prev['id']!='gakumas-18':assert prev==now
assert w['events'][:-1]==before['items'][0]['events']
path.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',report)]:
    (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
p=ROOT/'data/gakumas-products.csv'
with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
row=next(r for r in rows[1:] if r[0]=='gakumas-18');row[8]=json.dumps(g['channels'],ensure_ascii=False);row[12]=DATE
with p.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows)
audit={'checkedAt':probe['checkedAt'],'newProducts':0,'changedProducts':1,'changedProductIds':['gakumas-18'],'newChannelLinks':2,'addedLinks':added,'newArticles':[source],'changedArticles':[g['sourceUrl']],'newEvents':[eid],'sourceErrors':probe['errors'],'ignoredChanges':'其余18篇仅乐天促销横幅文字变化，商品价格、月份、链接及图片未变化。','limitations':'两条商品链接按来源图示对应；店内价格、运费条件与库存未独立确认。粉丝企划的日期、地址及协赞状态待核，未当作官方活动。'}
(ROOT/'data/gakumas-monitor-2026-10-30.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='addedLinks'},ensure_ascii=False))
