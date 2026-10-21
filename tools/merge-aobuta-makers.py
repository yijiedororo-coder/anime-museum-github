"""Append verified maker records while keeping existing IDs, routes and source links."""
import json, csv, re, hashlib, unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from lxml import html

ROOT=Path(__file__).resolve().parent.parent; CACHE=ROOT/'tools/aobuta-research'; DATE='2026-10-13'; BATCH=DATE+'-makers'
target=ROOT/'data/aobuta-data.js'
obj=json.loads(target.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';')); record=obj['items'][0]
baseline=CACHE/'baseline-before-makers.json'
if not baseline.exists():baseline.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8')
goods=record['merch']; before=len(goods); old_ids=[g['id'] for g in goods]
def canonical(u):
    u=u.replace('/en/taito-prize/','/taito-prize/');return u.rstrip('/')
def norm(n):
    n=unicodedata.normalize('NFKC',n)
    n=re.sub(r'[「『]青春ブタ野郎[」』]シリーズ|青春ブタ野郎シリーズ|青春ブタ野郎は(?:バニーガール先輩|おでかけシスター|ランドセルガール|ゆめみる少女|サンタクロース)の夢を見ない','',n)
    return re.sub(r'[\s「」『』“”～ー―−\-・＋+（）()]','',n).lower()
def month(g):
    m=re.search(r'(20\d{2})年(\d+)月',g.get('releaseDate',''));return (m[1],int(m[2])) if m else None
def add_channels(g,channels):
    for c in channels:
        if not any(canonical(x['url'])==canonical(c['url']) and x['name']==c['name'] for x in g['channels']):g['channels'].append(c)
def merge(g,p):
    if g.get('addedInBatch')==BATCH and g['id']==p['id'] and p['manufacturer']=='KOTOBUKIYA':
        for k in ['image','images','releaseDate','specifications']:g[k]=p[k]
    for c in g['channels']:
        if c['url'].startswith('http://') and g.get('addedInBatch')==BATCH:c['url']=c['url'].replace('http://','https://',1)
    for k in ['manufacturer','productBrand','acquisitionType','variant']:
        if p.get(k) and (not g.get(k) or g.get(k)=='来源未标厂商'):g[k]=p[k]
    observation={k:p.get(k,'') for k in ['price','releaseDate','size','image','sourceUrl','sourceName','checkedAt']}
    g.setdefault('sourceObservations',[])
    if not any(x.get('sourceUrl')==p['sourceUrl'] for x in g['sourceObservations']):g['sourceObservations'].append(observation)
    g['images']=list(dict.fromkeys(g.get('images',[])+p.get('images',[])))
    g['specifications']=list(dict.fromkeys(g.get('specifications',[])+p.get('specifications',[])))
    add_channels(g,p['channels']);g['checkedAt']=DATE
    g['sourceObservations']=[v for v in g['sourceObservations'] if v['sourceUrl']!=g['sourceUrl'] or any(v.get(k)!=g.get(k) for k in ['price','releaseDate','size','image'])]

# Enrich earlier records only from their saved source's explicit maker fields.
for g in goods:
    p=CACHE/(hashlib.sha256(g['sourceUrl'].split('#')[0].encode()).hexdigest()+'.html')
    if p.exists():
        d=html.fromstring(p.read_text(encoding='utf-8'))
        if 'goodsmile' in g['sourceUrl']:
            dt=d.xpath('//dt[normalize-space(.)="メーカー"]')
            if dt and dt[0].getnext() is not None:g['manufacturer']=dt[0].getnext().text_content().strip()
        elif 'ao-buta.com/tv/goods/' in g['sourceUrl']:
            box=d.xpath('//div[@class="goods_detail"]')
            if box:
                for br in box[0].xpath('.//br'):br.tail='\n'+(br.tail or '')
            text=box[0].text_content() if box else ''
            m=re.search(r'発売元[：:\s]+([^\s\r\n]+)',text)
            if m:g['manufacturer']=m[1].strip()
    old_maker=g.get('manufacturer'); maker_map={'株式会社ホビーストック':'HOBBY STOCK','株式会社アニプレックス':'ANIPLEX','株式会社キャビネット':'キャビネット','グッドスマイルカンパニー':'Good Smile Company','ＫＡＤＯＫＡＷＡ':'KADOKAWA'}
    if old_maker in maker_map:
        g['manufacturer']=maker_map[old_maker]
    if old_maker and (g.get('productBrand')==old_maker or len(g.get('productBrand',''))>70):g['productBrand']=g['manufacturer']
    if 'AMNIBUS' in g['sourceName']:g['manufacturer']='アルマビアンカ';g['productBrand']='AMNIBUS'
    if not g.get('acquisitionType'):
        g['acquisitionType']='娃娃机景品' if '景品' in g['price'] else '购买特典' if '特典（' in g['price'] else '零售周边'
    g.setdefault('manufacturer','来源未标厂商');g.setdefault('productBrand',g['manufacturer'])

new=[]; merged=[]
sources=[]
for f in ['maker-products.json','maker-supplements.json']:
    result=json.loads((CACHE/f).read_text(encoding='utf-8'));assert result['checkedAt']==DATE
    assert not result['failures'];sources+=result['products']
# Prefer the maker/producer's own version before operator descriptions.
sources.sort(key=lambda g:('onkure.dmm.com' in g['sourceUrl'],g['sourceUrl']))
for p in sources:
    same=next((g for g in goods if g['id']==p['id'] or any(canonical(v)==canonical(p['sourceUrl']) for v in [g['sourceUrl']]+[c['url'] for c in g['channels']])),None)
    if not same:
        same=next((g for g in goods if g.get('manufacturer')==p['manufacturer'] and norm(g['name'])==norm(p['name']) and month(g)==month(p)),None)
    if same:
        merge(same,p);merged.append({'id':same['id'],'source':p['sourceUrl']});continue
    p['addedInBatch']=BATCH;p['addedAt']=DATE;goods.append(p);new.append(p['id'])

# Names stay complete in detail; cards have a compact readable product title.
for g in goods:
    if g.get('addedInBatch')==BATCH:
        short=re.sub(r'^(?:[「『]?青春ブタ野郎[」』]?シリーズ|青春ブタ野郎は(?:バニーガール先輩|おでかけシスター|ランドセルガール|ゆめみる少女|サンタクロース)の夢を見ない)\s*','',g['name'])
        g['displayName']=short or g['name']

assert [g['id'] for g in goods[:before]]==old_ids
assert len({g['id'] for g in goods})==len(goods)
prizes=[g for g in goods if g['acquisitionType']=='娃娃机景品']
makers=Counter(g['manufacturer'] for g in goods if g['manufacturer']!='来源未标厂商')
report={'checkedAt':DATE,'batch':BATCH,'newProducts':len([g for g in goods if g.get('addedInBatch')==BATCH]),'totalProducts':len(goods),'prizeProducts':len(prizes),'manufacturerCounts':dict(makers),'sourceCatalogs':{'TAITO':43,'SEGA':10,'アズメーカー':85,'DMM景品档案':31},'sourceNotes':['TAITO按公开关联产品收录43个档案，包含普通、在线抓娃娃限定、Renewal及再登场记录。','SEGA现行作品检索10个档案；早期物品另用DMM运营商历史资料补充。','きゃらON！青春猪头目录3页共85个款式，商品子页逐条核对；部分早期商品与原动画目录合并。','FuRyu早期charahiroba链接已迁移、部分历史页不再可用；历史景品以DMM运营商档案注明来源。','elCOCO官方商城部分请求返回403；三款手办通过Design COCO制作档案核对，并保留厂商原链接。'],'limits':'仅覆盖可核查的公开厂商、制作方及运营商目录；不是全市场穷尽清单。景品没有统一零售价格，日期是来源的出荷 / 投放 / 发售计划。'}
record['manufacturerResearch']=report;record['retrievedAt']=DATE
record['status']=re.sub(r'\d+条周边档案',str(len(goods))+'条周边档案',record['status'])
record['libraryReport']['goods']=len(goods);record['libraryReport']['checkedAt']=DATE
record['libraryReport']['categories']=dict(Counter(g['category'] for g in goods))
known={c['name']:c for c in record['channelSummary']}
for g in goods:
    for c in g['channels']:
        if c['name'] not in known:known[c['name']]={'name':c['name'],'sourceUrl':c['url'],'description':c.get('linkType','来源资料或渠道'),'examples':[]}
        if len(known[c['name']]['examples'])<3 and g.get('displayName',g['name']) not in known[c['name']]['examples']:known[c['name']]['examples'].append(g.get('displayName',g['name']))
record['channelSummary']=list(known.values())
target.write_text('window.MUSEUM_EVENTS = '+json.dumps(obj,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
fields=['商品ID','商品名','原完整商品名','分类','制造商或发行方','品牌','获取方式','款式','系列或联名','角色','来源参考价','来源发售记录','尺寸','规格及限制','来源','购买或资料渠道','其他来源记录','核查日期']
def cell(s):
    s=str(s or '');return "'"+s if s[:1] in '=+-@' else s
with (ROOT/'data/aobuta-products.csv').open('w',encoding='utf-8-sig',newline='') as out:
    w=csv.writer(out);w.writerow(fields)
    for g in goods:w.writerow([cell(x) for x in [g['id'],g['name'],g.get('originalName',''),g['category'],g['manufacturer'],g['productBrand'],g['acquisitionType'],g.get('variant',''),g.get('series',g['originalType']),g['characters'],g['price'],g['releaseDate'],g['size'],' / '.join(g.get('specifications',[])),g['sourceUrl'],' | '.join(c['name']+' ['+c.get('linkType','来源链接')+'] '+c['url'] for c in g['channels']),json.dumps(g.get('sourceObservations',[]),ensure_ascii=False),g['checkedAt']]])
(CACHE/'maker-import-report.json').write_text(json.dumps({**report,'appendedIds':[g['id'] for g in goods if g.get('addedInBatch')==BATCH],'merged':merged},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'before':before,'after':len(goods),'appended':len(new),'mergedSources':len(merged),'prizes':len(prizes),'makers':dict(makers)},ensure_ascii=False))
