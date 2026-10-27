"""Append a source-only prize preview without inferring official specifications."""
import copy, csv, hashlib, json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from lxml import html

ROOT=Path(__file__).resolve().parent.parent
DATE='2026-10-27'
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
CACHE=ROOT/'tools/zuta-monitor'/DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'))
assert probe['checkedAt'].startswith(DATE) and not probe['errors']
assert all(not v['new'] and not v['changed'] and not v['removed'] for v in probe['csvChanges'].values())
source='https://zutapoke.com/12413/'
doc=html.fromstring((CACHE/(hashlib.sha256(source.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
h=next(h for h in doc.xpath('//h4') if '天使と悪魔テーマの咲季・佑芽' in h.text_content())
assert '2027年4月登場' in h.text_content()
image=h.getnext().xpath('.//img/@data-src')[0]
assert image=='https://zutapoke.com/wp-content/uploads/2026/07/image-372-1024x576.png'
path=ROOT/'data/gakumas-data.js'
data=json.loads(path.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
before=copy.deepcopy(data);w=data['items'][0]
gid='zuta-preview-12413-angel-devil-saki-ume-202704'
assert all(g['id']!=gid for g in w['merch'])
assert all('/2026/07/image-372' not in json.dumps(g,ensure_ascii=False) for g in w['merch'])
g={'id':gid,'kind':'merch','name':'天使与恶魔主题 · 花海咲季、花海佑芽 · 景品系列预告','originalName':h.text_content().strip(),'category':'手办','originalType':'プライズ,シリーズ予告,天使と悪魔','characters':'花海咲季、花海佑芽','manufacturer':'来源本节未标注；待厂商确认','acquisitionType':'娃娃机景品（来源预告；投放运营商待确认）','releaseDate':'2027年4月预定登场（来源汇总；具体日期及厂商独立确认待核）','price':'景品预告未列零售价；不推算抓取成本','size':'来源未标注','description':'被追踪的景品日程新增天使与恶魔主题咲季、佑芽预告。作为一个系列预告归档，尚不拆分为已确认的两款正式商品。','specifications':['来源只提供月份、角色主题和一张共同预告图。','正式商品名、厂商品牌、单品数量、尺寸、材质及投放渠道尚未独立核实。','2027年4月为来源预定登场月份，不代表当前可购买或可抓取。'],'image':image,'images':[image],'sourceUrl':source,'sourceName':'学マスまとめ · 景品登场日程','checkedAt':DATE,'channels':[],'availability':'预告情报；来源本节未列购买或运营商链接，待后续确认。'}
w['merch'].append(g)
article=next(a for a in w['articleIndex'] if a['url']==source)
article.setdefault('sections',[]).append('2026-10-27新增：2027年4月预定登场的天使与恶魔主题咲季、佑芽；按一个系列预告收录，正式商品名、规格、具体日期与渠道待核。')
article['checkedAt']=DATE
report=w['collectionReport'];report.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':1,'changedProducts':0,'newArticles':0,'changedArticles':1,'scope':'来源景品日程新增系列预告，未作为官方确认单品'}})
w['retrievedAt']=DATE
assert w['merch'][:-1]==before['items'][0]['merch']
assert w['events']==before['items'][0]['events']
path.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',report)]:
    (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
csvpath=ROOT/'data/gakumas-products.csv'
with csvpath.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
assert len(rows)-1==len(before['items'][0]['merch'])
values=[g['id'],g['name'],g['category'],g.get('characters',''),g['originalType'],g['releaseDate'],g['price'],g['size'],json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'','[]',DATE]
rows.append(values)
with csvpath.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows)
audit={'checkedAt':probe['checkedAt'],'newProducts':1,'changedProducts':0,'newArticles':0,'changedArticles':1,'newProductIds':[gid],'databaseRows':5271,'articlesChecked':286,'sourceErrors':probe['errors'],'ignoredChanges':'乐天促销横幅移除、Battle Spirits相同渠道面板排序变化，以及历史游戏直播嵌入摘要时间修订；未发现价格、月份或渠道新增。','limitations':'仅来源系列预告；不声称厂商确认、两款正式单品、实时库存或可预约。'}
(ROOT/'data/gakumas-monitor-2026-10-27.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
