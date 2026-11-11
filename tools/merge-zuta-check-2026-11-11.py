"""Import November 11 plush families and verified popup/release distinction."""
import copy,csv,hashlib,json,re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-11';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors'] and probe['checkedAt'].startswith(DATE)
assert not probe['newArticles'] and all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
def doc(u):return html.fromstring((CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0]
source='https://zutapoke.com/14433/';cards=doc(source).xpath('//article[contains(@class,"gpl-card")]');gift=next(c for c in cards if 'いちななさいず' in c.xpath('string(.//h3)'));gear=next(c for c in cards if 'ギアビート' in c.xpath('string(.//h3)'))
gifturl='https://www.gift-gift.jp/nui/nui1311.html';asobi='https://shop.asobistore.jp/products/detail/252305-7_gk-c001-00-00';official='https://idolmaster-official.jp/news/01_20322'
checks=json.loads((CACHE/'official-check.json').read_text(encoding='utf-8'));assert '5,060円' in checks[0]['text'] and '本商品は受注生産ではございません' in checks[0]['text'];assert '2027年3月26日' in checks[1]['text'] and '12月07日' in checks[1]['text']
assert '2027年3月26日' in doc(official).text_content()
newids=[]
for card,gid,name,url in [(gift,'zuta-gift-ichinana-202611','Gift · 17厘米いちななさいず ふもふも毛绒系列',gifturl),(gear,'zuta-gearbeat-plush-2026','Gearbeat Concerto · 蒸汽朋克官方毛绒系列',asobi)]:
 assert not any(g['id']==gid for g in w['merch']);images=list(dict.fromkeys(i for i in card.xpath('.//img/@data-src|.//img/@src') if i.startswith('https://')))
 g={'id':gid,'kind':'merch','name':name,'originalName':card.xpath('string(.//h3)').strip(),'category':'毛绒 / 娃娃','originalType':'ぬいぐるみ','characters':card.xpath('string(.//p[contains(@class,"gpl-idols")])').strip(),'image':images[0],'images':images,'sourceUrl':source,'sourceName':'学マスまとめ毛绒汇总 / 官方资料核对','verificationUrl':url,'checkedAt':DATE,'channels':[{'name':'官方商品资料' if gid.startswith('zuta-gift') else 'ASOBI STORE','url':url,'linkType':'厂商资料页（花海咲季单品）' if gid.startswith('zuta-gift') else '商品页（花海咲季；其他角色需切换）','sourceNote':'官方页只对应花海咲季，不把同一购买链接标成其他角色单品。'}],'sourceRecordIds':[],'variants':[],'availability':'来源资料快照；不能推定现货或各角色受理状态。'}
 if gid.startswith('zuta-gift'):
  g.update({'manufacturer':'Gift','price':'各5,060円含税（来源；官方咲季页一致）','releaseDate':'2026年11月予定；咲季官方标注网上批次约11月发货，历史先行销售另计','size':'来源称约17cm；咲季官方为头顶约17cm / 全高约20cm，手毬来源同样区分，其他5款来源称全高约17cm','description':'本次汇总新增7角色的小号系列，与现有まんなかさいず系列区分。各角色照片集中保留，不按画廊次序猜测单品角色。','specifications':['咲季官方旧销售窗口为2026-08-15约10:30至09-27约23:59，现已过去；不是当前仍开放受注。','官方咲季页明确非受注生产、首批数量有限；不能把11月发货标注当作现货。','除咲季外6款具体官方单品页未独立核对；规格差异按来源注明。']})
 else:
  g.update({'manufacturer':'官方ASOBI STORE销售；生产厂商未标注','price':'各3,600円含税（来源；官方咲季页核对）','releaseDate':'官方整体发售予定2027年3月26日；快闪先行销售2026年12月24日起，非同一日期','size':'约W110×H165×D85mm，聚酯纤维（咲季官方核对；来源作为系列规格）','description':'全13种蒸汽朋克衣装毛绒。来源把12月24日写在发售栏，官方明确该日是线下快闪先行销售，正式发售为2027年3月26日。','specifications':['ASOBI 2026-12-07 23:59前下单为受注生产，此后数量限定；官方也提醒期内可能因产量上限提前结束。','咲季页列随机票券风卡1张，全13种、不可选图且可能重复；其他角色适用条件仍以各页确认。','日本快闪12月24日至次年1月11日；上海为12月24日至次年1月3日，结束日期不同。'],'sourceObservations':[{'sourceName':'官方公告核对：通贩与快闪先行销售区分','sourceUrl':official,'releaseDate':'2027-03-26正式发售予定；2026-12-24快闪先行','checkedAt':DATE}]})
 w['merch'].append(g);newids.append(gid)
a=next(a for a in w['articleIndex'] if a['url']==source);a.setdefault('sections',[]).append('2026-11-11新增Gift小号ふもふも7角色系列与Gearbeat Concerto毛绒13种系列。咲季官方核实Gift 5,060円、11月批次，非受注生产；Gearbeat 3,600円、12月7日23:59受注分界。官方公告明确2027年3月26日发售，12月24日是快闪先行销售，不能混用。');a['checkedAt']=DATE
key='gearbeat-official';w['eventSources'][key]=['偶像大师官方 · Gearbeat Concerto公告',official]
e=next(e for e in w['events'] if e['id']=='gk-week49-gearbeat-popup');e.update({'name':'Gearbeat Concerto · 日本蒸汽朋克快闪','category':'官方快闪 / 先行销售','sourceUrl':official,'sources':list(dict.fromkeys(e['sources']+[key])),'checkedAt':DATE,'summary':'官方确认日本于2026年12月24日至2027年1月11日在偶像大师官方商店各店举办（315!!!SHOP除外），为先行销售；商品正式发售予定2027年3月26日。','regions':['日本'],'pending':['各店即时营业、入场限制、现场库存及具体商品受理状态'],'places':['偶像大师官方商店各店（315!!!SHOP除外）']});e['notes'].append('官方限购：每会计每商品3件，尺寸合计3件；随机商品上限3BOX或种类数×3，角色精细画仅1件，现场规定可能调整。');e['media']['verifiedFacts']=['官方公告核对日本期间、适用店铺、正式发售日与先行销售区分。']
newEvents=[]
for slug,name,start,end,summary,regions in [('order','Gearbeat Concerto · ASOBI受注分界','','2026-12-07T23:59','官方列12月7日23:59前为受注生产、以后数量限定，期间也可能因产量上限提前结束；正式发售2027年3月26日。',['日本']),('shanghai','Gearbeat Concerto · 上海快闪','2026-12-24','2027-01-03','官方确认上海新世界城4F特设会场，地址黄浦区南京西路2–68号；结束日早于日本，特典及参与条件需看中国主办方通知。',['中国 / 上海'])]:
 eid='gk-gearbeat-'+slug+'-202611';assert not any(e['id']==eid for e in w['events']);newEvents.append(eid)
 w['events'].append({'id':eid,'kind':'event','name':name,'category':'周边受注 / 销售提醒' if slug=='order' else '官方快闪 / 先行销售','start':start,'end':end,'endLabel':'受注生产分界' if slug=='order' else '上海场结束','summary':summary,'reward':'商品及适用特典依各渠道规则；不保证齐套或现场库存。','cost':'各商品不同，毛绒来源各3,600円；现场结算币种与运费另核。','regions':regions,'sourceUrl':official,'sources':[key],'checkedAt':DATE,'activeDates':['日本时间记录受注截止；上海现场开放时刻未列。'],'steps':['查看官方公告及对应渠道最新规则。'],'places':[],'notes':['受注与线下快闪、正式发售日期分别记录。'],'pending':['实时受理状态、库存、具体开放时间与渠道适用细则'],'media':{'images':[],'verifiedFacts':['已核对官方公告与咲季商品页。'],'resources':[],'sources':[]}})
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':2,'changedProducts':0,'newArticles':0,'changedArticles':1,'newEvents':2,'changedEvents':1}});w['retrievedAt']=DATE
assert w['merch'][:-2]==before['items'][0]['merch']
assert [e['id'] for e in w['events'][:-2]]==[e['id'] for e in before['items'][0]['events']]
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
 for g in w['merch']:
  vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')];writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProducts':2,'newProductIds':newids,'changedProducts':0,'newArticles':0,'changedArticles':[source],'newEvents':newEvents,'changedEvents':['gk-week49-gearbeat-popup'],'sourceErrors':[],'officialVerified':[gifturl,asobi,official],'correction':'Gearbeat官方正式发售2027-03-26，2026-12-24是快闪先行；上海01-03结束，日本01-11结束。','limitations':['Gift仅咲季官方单品已独立核实，其他6款按来源区分规格；不是全角色官方单品均已核对。','Gearbeat咲季独立单品及整体公告已核对，其他角色特典细则需逐页确认。'],'ignoredChanges':'其余为乐天促销文字、游戏活动摘要和手办渠道面板顺序调整，未产生新商品事实。'}
(ROOT/'data/gakumas-monitor-2026-11-11.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(audit,ensure_ascii=False))
