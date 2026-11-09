"""Merge fresh November 9 source changes; all old IDs, variants and link order remain."""
import copy,csv,hashlib,json,re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-11-09';CACHE=ROOT/'tools/zuta-monitor'/DATE
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
p=ROOT/'data/gakumas-data.js';data=json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0];oldcount=len(w['merch']);changed=set();newids=[];added=[]
byid={g['id']:g for g in w['merch']}
def append(g):
 assert g['id'] not in byid
 w['merch'].append(g);byid[g['id']]=g;newids.append(g['id'])
def channel(g,u,name,raw,note,kind='商品页（来源同款图片对应）'):
 if any(c['url']==u for c in g['channels']):return
 g['channels'].append({'name':name,'url':u,'originalUrl':raw,'linkType':kind,'sourceNote':note});g['checkedAt']=DATE;added.append((g['id'],u))
 if g['id'] not in newids:changed.add(g['id'])
def base(gid,name,category,image,source):return {'id':gid,'kind':'merch','name':name,'category':category,'originalType':name,'characters':'系列多角色；单品角色见对应来源图片，未逐项独立核定','price':'来源未列，待确认','releaseDate':'来源未列，待确认','size':'来源未列，待确认','description':'按来源公开资料整理；报价不代表实时库存。','image':image,'sourceUrl':source,'sourceName':'学マスまとめ · 2026-11-09核查','checkedAt':DATE,'channels':[],'sourceRecordIds':[],'variants':[],'availability':'来源资料快照，店内受理状态需自行确认。'}
source='https://zutapoke.com/17245/';plans=json.loads((CACHE/'chugai-plan.json').read_text(encoding='utf-8'))
# New families remain grouped because most retailer pages are limited; do not guess role order.
families={}
for key,label,price,category in [('acrylstand','亚克力收藏立牌','1,980円 / 个（来源）','亚克力立牌'),('keyholder','心形糖果附属钥匙扣','1,540円 / 个（来源）','钥匙扣'),('uchiwa','透明团扇','1,210円 / 个（来源）','其他周边')]:
 image=next(x['image'] for x in plans if '/gakumas-sweets-'+key+'-' in x['image']);g=base('zuta-chugai-sweets-'+key+'-202611','Chugai Grace Café · 甜点主题'+label+'系列',category,image,source);g.update({'price':price,'description':'周报称本次首次开放通販；系列集中归档，各链接是不同角色单品，不能视为整套。多数AnimeStore页HTTP429，Animate页无可核实详情；未按图片顺序猜测角色。','specifications':['各图片与来源商品链接逐一配对；渠道备注附图片地址以便识别。','2026年9月活动先行销售仅在本次成功核实的倉本千奈立牌、篠澤広钥匙扣页列出，其他角色未独立核对。']});append(g);families[key]=g
for x in plans:
 u=direct(x['raw']);host=urlparse(u).netloc;name='AnimeStore' if host=='anime-store.jp' else 'Animate';note=DATE+'来源图片对应；'+('来源称满6,600円免运费，地区及条件未核；商店多数返回HTTP429，未重试限流页。' if name=='AnimeStore' else '商店详情未独立核实。')+'图片：'+x['image']
 if x['matches']:targets=[byid[i] for i in x['matches']]
 elif '/gakumas-sweets-' in x['image']:
  key=next(k for k in families if '/gakumas-sweets-'+k+'-' in x['image']);targets=[families[key]]
 elif x['image'].endswith('/image-146.png'):
  targets=[byid['zuta-db-'+str(i)] for i in range(3607,3620)];note+=' 随机徽章系列/BOX入口，不能指定本条角色；售价与销售单位需店内确认。'
 elif x['image'].endswith('/image-147.png'):
  targets=[byid['zuta-db-'+str(i)] for i in range(3621,3647)];note+=' 随机签名卡系列入口，不保证本条角色或签名版本；单包与BOX单位须核对。'
 else:raise AssertionError(x)
 for g in targets:channel(g,u,name,x['raw'],note,'系列内角色商品页（角色见图片）' if g['id'] in newids else '商品页（图片对应；随机商品不能指定角色）' if len(targets)>1 else '商品页（来源同款图片对应）')
# Save the two successfully fetched retailer specification snapshots without extending them to all roles.
verification=json.loads((CACHE/'new-products-verification.json').read_text(encoding='utf-8'))
for v in verification:
 if v.get('description'):
  key='acrylstand' if 'アクリルコレクション' in v['title'] else 'keyholder';g=families[key]
  g.setdefault('sourceObservations',[]).append({'sourceUrl':v['url'].removesuffix('.js'),'sourceName':'AnimeStore公开商品资料（单个角色核实）','description':v['title']+'；'+html.fromstring('<div>'+v['description']+'</div>').text_content().strip(),'price':str(v['price']//100)+'円；仅该单品核查','checkedAt':DATE})
# Museum Card is one random series / BOX, not 26 separate products.
u='https://zutapoke.com/29247/';d=doc(u);imgs=list(dict.fromkeys(d.xpath('//main/article//*[contains(@class,"post_content")]//img/@data-src')));raw=d.xpath('//main/article//*[contains(@class,"post_content")]//a/@href')[0]
g=base('zuta-museumcard-exhibition-202706','Museum Card [Exhibition 学园偶像大师] · 全26种随机卡片系列','卡片 / 文具',imgs[0],u);g.update({'images':imgs,'price':'1包2张660円；1BOX13包8,580円（来源报价）','releaseDate':'2027年6月予定（来源）','size':'全26种随机；卡片尺寸来源未列','description':'来源标题虽提到发售，正文是预约情报；不是已经交付。全26种不代表一BOX保证集齐；Animate单品详情本次返回空内容，未独立确认厂商与规格。'});append(g);channel(g,direct(raw),'Animate',raw,'来源BOX购买入口；1BOX13包，单包2张，未承诺齐套。','商品页（BOX）')
# Three physical CDs, with one retailer page verified per title.
u='https://zutapoke.com/29288/';d=doc(u);body=d.xpath('//main/article/*[contains(@class,"post_content")]')[0];links=list(dict.fromkeys(body.xpath('.//a/@href')));shared=[(direct(a),a) for a in links if 'gamers' not in direct(a)]
for v in verification:
 if 'gamers.co.jp' not in v['url']:continue
 title=re.search('「(.+?)」',v['title'])[1];t=v['text'];assert '2,500円(税込)' in t and '2027/03/17' in t and 'マルチクロス' in t
 gd=doc(v['url']);img=gd.xpath('//meta[@property="og:image"]/@content');image=img[0] if img and img[0].startswith('https://') and 'image=&' not in img[0] else body.xpath('.//img/@data-src')[0]
 g=base('zuta-duet2-'+v['url'].strip('/').split('/')[-1],'Duet Song Collection 第2弹 · '+title,'音乐 / 影像',image,u);g.update({'originalName':v['title'].split(' | ')[0],'imagePlaceholder':True,'characters':'歌唱成员未逐项独立核对','price':'2,500円含税（Gamers单张CD）','releaseDate':'2027年3月17日（Gamers）','size':'CD；品番 '+re.search(r'BNEI-\d+',t)[0],'description':'实体CD，与已开放的流媒体配信分开记录。Gamers页核对标题、价格、日期、品番与特典；歌曲清单未确认，不转载歌词。','specifications':['Gamers：マルチクロス，送完为止。','来源另列Amazon大封面、Animate A3透明海报、ASOBI手机尺寸贴纸；适用规则和是否仍附赠未独立核实。']});append(g);channel(g,v['url'],'Gamers',v['url'],'已核对本张标题、2,500円、2027-03-17及マルチクロス；特典送完为止。')
 for link,original in shared:
  name='Amazon' if 'amazon.co.jp' in link else 'Animate' if 'animate' in link else 'ASOBI STORE'
  channel(g,link,name,original,'来源所列系列选择/搜索入口，需选择与本条标题一致的CD，特典适用条件待店内确认。','搜索页' if name=='Amazon' else '系列商品选择入口（非本张独立页）')
# Article index preserves new, substantive source summaries, not poll responses or lyrics.
sections={
'https://zutapoke.com/29247/':['Museum Card：全26种随机卡，1包2张660円、BOX13包8,580円，2027年6月予定；正文是预约信息，不是已发货。'],
'https://zutapoke.com/29288/':['Duet Song Collection第2弹3张：クロスファイア、慟哭のコンチェルト、FANTASTIC GATHERING!。Gamers核对每张2,500円、2027年3月17日发售。','渠道特典区分：Amazon大封面、Gamersマルチクロス、Animate A3透明海报、ASOBI手机尺寸贴纸。除Gamers外条件未独立核实。'],
'https://zutapoke.com/29204/':['第49号：新增Museum Card预约；Chugai Grace Café收藏立牌1,980円、糖果钥匙扣1,540円、透明团扇1,210円等通販情报。','3rd Single完走纪念周边11月15日结束；Starlight Dining服装毛绒来源称附斗篷，店内条件未独立确认。','Suntory毛巾套装11月2日至22日、各4,480円另运费；Kitamura贺年卡11月4日10:00至12月20日23:59，预计2027年1月1日至上旬送达（均为周报情报）。','Part7一番赏12月12日，A葛城リーリヤ、B紫雲清夏、C姫崎莉波1/7手办，Last One清夏特别版；未独立核实厂商完整奖项或抽奖价格。','ROUND1第2弹12月1日至2027年1月31日；Gearbeat Concerto蒸汽朋克快闪12月24日至2027年1月11日；地点、商品清单、价格待官方资料。','年末感谢祭12月24日19:00；Lalaport联动、WS卡牌第2弹宣布，完整日期或商品规格待公布，不虚构商品条目。']}
for url,notes in sections.items():
 assert not any(a['url']==url for a in w['articleIndex']);w['articleIndex'].append({'title':doc(url).xpath('string(//h1)'),'url':url,'checkedAt':DATE,'sections':notes,'prices':[],'dates':[]})
a=next(a for a in w['articleIndex'] if a['url']==source);a.setdefault('sections',[]).append('2026-11-09补入AnimeStore、Animate新渠道及3类首次通販系列；随机徽章与签名卡入口按系列关联，不能指定角色。多数AnimeStore页限流，规格不扩展到未核角色。');a['checkedAt']=DATE
# Weekly event leads explicitly identify source-only dates and pending official checks.
weekly='https://zutapoke.com/29204/';key='zuta-week49';w['eventSources'][key]=['学マスまとめ · 第49号（未独立核实官方）',weekly];newEvents=[]
for slug,name,start,end,summary,cost in [
('suntory-towel','Suntory原创毛巾套装销售（周报情报）','2026-11-02','2026-11-22','周报列原创设计毛巾套装销售；款式、饮料组合与渠道细则待核。','来源各4,480円另运费'),
('kitamura-newyear','Kitamura · 寄给你的贺年卡（周报情报）','2026-11-04T10:00','2026-12-20T23:59','周报称可选偶像，预计2027年1月1日至上旬送达；全员款外附留言，具体规格待官方。','来源未列，待确认'),
('round1-v2','ROUND1联动第2弹（周报预告）','2026-12-01','2027-01-31','周报公布联动期间；活动内容和适用门店尚待公布。','待确认'),
('gearbeat-popup','Gearbeat Concerto蒸汽朋克快闪（周报预告）','2026-12-24','2027-01-11','周报提到毛绒等周边，场地、详细商品与销售规则待官方。','待确认'),
('yearend-stream','偶像大师年末感谢祭直播（周报预告）','2026-12-24T19:00','','周报列七瀬つむぎ（有村麻央役）参与，YouTube、Niconico、X Live、bilibili配信；具体直播入口待官方。','来源未列，待确认')]:
 eid='gk-week49-'+slug;assert not any(e['id']==eid for e in w['events']);newEvents.append(eid)
 w['events'].append({'id':eid,'kind':'event','name':name,'category':'周报线索 / 待官方复核','start':start,'end':end,'endLabel':'来源未列结束时间' if not end else '来源日期，官方待复核','summary':summary,'reward':'具体商品、特典与适用条件待官方确认。','cost':cost,'regions':['日本'],'sourceUrl':weekly,'sources':[key],'checkedAt':DATE,'activeDates':['日本时间；仅转述本次周报，未独立核对主办方。'],'steps':['先查看周报来源，再等待或核对主办方详细公告。'],'places':[],'notes':['不代表实时库存、已开售或入场资格。'],'pending':['官方活动入口、详细地点、费用及参与规则'],'media':{'images':[],'verifiedFacts':[],'resources':[],'sources':[]}})
# Existing Part7 event keeps its ID and prior facts; new source detail appended as a qualified note.
e=next(e for e in w['events'] if e['id']=='ichiban-kuji-part7');e.setdefault('notes',[]).append('2026-11-09第49号新增奖项线索：A莉莉娅、B清夏、C莉波1/7手办及Last One清夏特别版；12月12日来源预告。未独立核实厂商奖项、抽奖价格，原资料保留。');e['sources'].append(key);e['checkedAt']=DATE
r=w['collectionReport'];r.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':len(newids),'changedProducts':len(changed),'newChannelLinks':len(added),'newArticles':3,'changedArticles':1,'newEvents':len(newEvents),'changedEvents':1}});w['retrievedAt']=DATE
assert len(newids)==7
for old,now in zip(before['items'][0]['merch'],w['merch']):
 assert old['id']==now['id'] and now['channels'][:len(old['channels'])]==old['channels']
 if old['id'] not in changed:assert old==now
assert [e['id'] for e in before['items'][0]['events']]==[e['id'] for e in w['events'][:len(before['items'][0]['events'])]]
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',r)]:
 (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
 for g in w['merch']:
  vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')];writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProducts':len(newids),'newProductIds':newids,'changedProducts':len(changed),'changedProductIds':sorted(changed),'newChannelLinks':len(added),'uniqueNewChannelUrls':len(set(u for _,u in added)),'newArticles':list(sections),'changedArticles':[source],'newEvents':newEvents,'changedEvents':['ichiban-kuji-part7'],'sourceErrors':[],'limitations':['24个AnimeStore公开商品端点返回429，未重试或绕过；另2页成功核对的规格仅对应明确角色。','Animate Museum Card详情返回空内容，按来源商品报价、日期记录。','新增活动为周报线索，已单列待官方复核，不伪造主办方确认。'],'ignoredChanges':'29016仅嵌入旧文章年份修正摘要，无新的威化饼4事实。'}
(ROOT/'data/gakumas-monitor-2026-11-09.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k!='changedProductIds'},ensure_ascii=False))
