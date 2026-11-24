"""Import November 24 source changes, preserving contradictory date observations."""
import copy,csv,hashlib,json,re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-24';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
assert all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
def doc(u):return html.fromstring((CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
def direct(u):
 if u.startswith('//'):u='https:'+u
 for _ in range(4):
  q=parse_qs(urlparse(u).query);v=next((q[k][0] for k in ['vc_url','a8ejpredirect','lsurl'] if k in q),None)
  if not v:break
  u=v
 return u
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];ids=[]
checks=json.loads((CACHE/'retail-check.json').read_text(encoding='utf-8'));assert len(checks)==10 and all('text' in x for x in checks);plans=json.loads((CACHE/'supergroupies-plan.json').read_text(encoding='utf-8'))
for x in checks:
 if 'super-groupies' not in x['url']:continue
 title=x['title'].split(' 学園アイドルマスター')[0];pid=x['url'].split('/')[-1];gid='zuta-supergroupies-'+pid;assert not any(g['id']==gid for g in w['merch'])
 role=title.split(' モデル')[0];price='22,000円' if '腕時計' in title else '15,400円' if '長財布' in title else '19,800円';assert price.removesuffix('円') in x['text'];match=next(y for y in plans if direct(y['raw'])==x['url']);image=match['image']
 delivery=re.search(r'お届け(?:・支払い)?時期:\s*([^ ]+)',x['text']);date=delivery[1] if delivery else '商品页历史交付月份未提取，待确认'
 g={'id':gid,'kind':'merch','name':'SuperGroupies · '+title,'originalName':title,'category':'服饰 / 生活周边','originalType':'腕時計' if '腕時計' in title else '長財布' if '長財布' in title else 'ショルダーバッグ','characters':role,'manufacturer':'SuperGroupies','price':price+'含税（品牌商品页）','releaseDate':'品牌页历史交付标注：'+date+'；本次补货不是新发售日','size':'具体尺寸/材质见品牌页，本次未逐字段整理','description':'麻央、莉莉娅、千奈主题服饰配件，按角色与品类独立保存；周报称包袋、钱包库存限定重新销售，不将报道或品牌状态视为访客打开时仍有库存。','image':image,'sourceUrl':'https://zutapoke.com/25853/','sourceName':'学マスまとめ / SuperGroupies品牌页核查','verificationUrl':x['url'],'checkedAt':DATE,'channels':[],'sourceRecordIds':[],'variants':[],'availability':'不得从本次页面快照推定实时库存；腕表与包袋/钱包销售阶段可能不同。','specifications':['品牌页标注全国统一运费1,000円，实际条件及结算以商店为准。','部分商品页同时出现历史预约模块及明显异常的2126年截止日期；本馆不采纳该异常日期，不创建预约截止提醒。']}
 for y in plans:
  if y['image']!=image:continue
  u=direct(y['raw']);name='SuperGroupise' if 'super-groupies' in u else 'Animate';g['channels'].append({'name':name,'url':u,'originalUrl':y['raw'],'linkType':'品牌商品页' if name=='SuperGroupise' else '商品页（来源同图对应）','sourceNote':'品牌标题、角色和价格已核对；Animate未逐项核店内规格和状态。原网站渠道名称沿用现有筛选标签。'})
 assert len(g['channels'])==2;w['merch'].append(g);ids.append(gid)
# Preserve old model price/date; append the new shop quote and the discrepant reported day.
g=next(g for g in w['merch'] if g['id']=='zuta-figure-13353-097ddbf59f68');v=next(x for x in checks if 'dmm.com' in x['url']);assert '3,795円税込' in v['text'] and '4580886844692' in v['text']
g.setdefault('sourceObservations',[]).append({'sourceName':'DMM / 第51号 · 30MS咲季','sourceUrl':v['url'],'price':'DMM核查3,795円含税，参考5,060円；旧报价保留，不代表实时库存。','releaseDate':'周报称2026-11-21发售；DMM仍标11月末前予定。原记录11月30日保留为旧观察，不把不同来源日期合成一个确定官方日期。','description':'JAN4580886844692。厂商候选页本次404，未冒称已核厂家发售日。','checkedAt':DATE});g['checkedAt']=DATE
for c in g['channels']:
 if c['url']==v['url']:c.setdefault('sourceNote','');c['sourceNote']+='；2026-11-24 DMM报价3,795円，历史报价另留。'
# Keep purchase-link order; only append if the direct DMM page was not already present.
if not any(c['url']==v['url'] for c in g['channels']):g['channels'].append({'name':'DMM','url':v['url'],'linkType':'商品页','sourceNote':'2026-11-24核对3,795円及JAN；不代表实时库存。'})
newid='zuta-mugyumi-vol3-preview-202611';assert not any(g['id']==newid for g in w['merch'])
w['merch'].append({'id':newid,'kind':'merch','name':'むぎゅみに收藏手办 vol.3 · 周报预告','originalName':'むぎゅみにコレクションフィギュア vol.3','category':'手办 / 模型','originalType':'コレクションフィギュア','characters':'秦谷美鈴 / 花海佑芽 / 姫崎莉波 / 氷渡香名江（周报阵容）','price':'来源未公布，待确认','releaseDate':'2027年6月25日（周报；厂商待核）','size':'尺寸、销售单位与配率待公布','description':'第3弹预告，独立于第1、2弹。来源称预约网站尚未公布；不捏造渠道、价格或整盒保证。','image':w['poster'],'imagePlaceholder':True,'sourceUrl':'https://zutapoke.com/29681/','sourceName':'学マスまとめ · 第51号','checkedAt':DATE,'channels':[],'sourceRecordIds':[],'variants':[],'availability':'预告资料，不代表已开售。'});ids.append(newid)
for u,note in [('https://zutapoke.com/25853/','2026-11-24第51号报道品牌包袋与钱包库存限定重新销售；9款角色/品类品牌页标题和价格核对。页面历史交付、异常截止模块保留为核查限制，不推断实时库存。'),('https://zutapoke.com/24647/','2026-11-24来源DMM报价由4,103円更新为3,795円，参考5,060円；DMM直接页核对。周报11月21日与DMM月底予定分别记录，不用库存反推发售日。')]:
 a=next(a for a in w['articleIndex'] if a['url']==u);a.setdefault('sections',[]).append(note);a['checkedAt']=DATE
weekly='https://zutapoke.com/29681/';assert not any(a['url']==weekly for a in w['articleIndex'])
w['articleIndex'].append({'title':doc(weekly).xpath('string(//h1)'),'url':weekly,'checkedAt':DATE,'sections':['第51号：SuperGroupies麻央、莉莉娅、千奈包袋/钱包补货报道；腕表销售阶段不同，不能当实时库存。','30MS咲季周报称11月21日发售，DMM3,795円；不同渠道日期各自注明。','むぎゅみに第3弹周报预告2027年6月25日，美鈴/佑芽/莉波/香名江；价格、渠道待公布。','11月27日倉本千奈ESPRESTO及初星商店Twinkle Rabbit主题；周报活动线索未独立核厂商/场地细则。','11月29日祭の湯及西武铁路联动结束提醒；具体营业时刻以主办方为准。'],'prices':[],'dates':[]})
# One qualified shop-theme lead; no invented merchandise lineup or closing day.
key='zuta-week51';w['eventSources'][key]=['学マスまとめ · 第51号（官方待核）',weekly];eid='gk-twinkle-rabbit-202611';assert not any(e['id']==eid for e in w['events'])
w['events'].append({'id':eid,'kind':'event','name':'初星商店 Twinkle Rabbit · 周报线索','category':'周报线索 / 待官方复核','start':'2026-11-27','end':'','endLabel':'结束日待公布/确认','summary':'周报列11月27日初星商店「トゥインクルラビット」主题；详细商品、价格、适用门店和入场规则未独立确认。','reward':'内容待官方','cost':'待确认','regions':['日本'],'sourceUrl':weekly,'sources':[key],'checkedAt':DATE,'activeDates':['日本时间；开始时刻与截止日待核。'],'steps':['查看初星商店官方后续公告后再确定购买或到访安排。'],'places':[],'notes':['仅为来源线索，未将未知商品建成确定SKU。'],'pending':['官方公告、商品目录、价格、结束日及入场规则'],'media':{'images':[],'verifiedFacts':[],'resources':[],'sources':[]}})
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':len(ids),'changedProducts':1,'newArticles':1,'changedArticles':2,'newEvents':1}});w['retrievedAt']=DATE
assert len(ids)==10
for old,now in zip(before['items'][0]['merch'],w['merch']):
 assert old['id']==now['id']
 # Previously recorded channel objects can gain a dated note, but URLs and ordering stay exact.
 assert [c['url'] for c in now['channels'][:len(old['channels'])]]==[c['url'] for c in old['channels']]
 if old['id']!=g['id']:assert old==now
assert w['events'][:-1]==before['items'][0]['events']
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
 for item in w['merch']:
  vals=[item['id'],item['name'],item['category'],item.get('characters',''),item.get('originalType',''),item.get('releaseDate',''),item.get('price',''),item.get('size',''),json.dumps(item['channels'],ensure_ascii=False),item['sourceUrl'],'/'.join(item.get('sourceRecordIds',[])),json.dumps(item.get('variants',[]),ensure_ascii=False),item.get('checkedAt','')];writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProducts':10,'newProductIds':ids,'changedProducts':1,'changedProductIds':['zuta-figure-13353-097ddbf59f68'],'newArticles':[weekly],'changedArticles':['https://zutapoke.com/25853/','https://zutapoke.com/24647/'],'newEvents':[eid],'verifiedUrls':[x['url'] for x in checks],'sourceErrors':[],'limitations':['SuperGroupies部分页异常2126年截止模块不采纳，不表示当前有库存。','30MS厂商候选页404，周报11/21与DMM月底日期分开保留。','第3弹手办与Twinkle Rabbit为周报线索，官方详目待核。'],'ignoredChanges':'其他旧文章只补全已结束游戏抽卡期间或改活动标题，未重复创建活动。'}
(ROOT/'data/gakumas-monitor-2026-11-24.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k!='verifiedUrls'},ensure_ascii=False))
