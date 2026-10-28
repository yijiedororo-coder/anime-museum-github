"""Import refreshed plush cards conservatively, keeping all old IDs and link order."""
import copy,csv,hashlib,json,re,unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from zoneinfo import ZoneInfo
from lxml import html
ROOT=Path(__file__).resolve().parent.parent;DATE='2026-10-28';CACHE=ROOT/'tools/zuta-monitor'/DATE
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()==DATE
probe=json.loads((CACHE/'probe.json').read_text(encoding='utf-8'));assert not probe['errors']
assert all(not v['new'] and not v['changed'] and not v['removed'] for v in probe['csvChanges'].values())
source='https://zutapoke.com/14433/'
doc=html.fromstring((CACHE/(hashlib.sha256(source.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
cards=doc.xpath('//article[contains(@class,"gpl-card")]');assert len(cards)==75
path=ROOT/'data/gakumas-data.js';data=json.loads(path.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'));before=copy.deepcopy(data);w=data['items'][0]
oldgoods=w['merch'][:];byid={g['id']:g for g in oldgoods};plush=[g for g in oldgoods if g.get('sourceUrl')==source]
def norm(t):
    t=unicodedata.normalize('NFKC',t).replace('学園アイドルマスター','');t=re.sub(r'^(?:\d{4}年)?\d*月(?:\d+日)?(?:登場|発売|発送)?\s*','',t)
    return re.sub(r'\s+','',t).lower()
def base(t):return re.sub(r'\([^)]*\)','',norm(t))
def direct(u):
    u='https:'+u if u.startswith('//') else u;q=parse_qs(urlparse(u).query)
    for k in ['pc','goods_url']:
        if k in q:return q[k][0]
    return u
manual={7:['zuta-plush-abbd738db6b6'],8:['zuta-plush-abbd738db6b6'],11:['zuta-plush-e2a5a289f5b1','zuta-plush-12f76219d804'],14:['zuta-plush-74dadaf6806b'],48:['zuta-plush-0387ec2e52b0'],49:['zuta-plush-3313093145f1'],50:['zuta-plush-a779c797aa00'],52:['zuta-db-352','zuta-db-353','zuta-db-354'],53:['zuta-plush-61e1d9c4a917'],54:['zuta-plush-61e1d9c4a917'],59:['zuta-plush-d6298341830b'],60:['zuta-plush-d6298341830b'],67:['zuta-db-355'],69:['zuta-plush-5f70f00a5bc9'],70:['zuta-db-385'],71:['zuta-db-384'],72:['zuta-db-394'],73:['zuta-db-386'],74:['zuta-db-387']}
newids=[];mapping=[];newlinks=0
for index,c in enumerate(cards):
    title=c.xpath('string(.//h3)').strip();roles=c.xpath('string(./p[@class="gpl-idols"])').strip()
    facts=[p.text_content().strip() for p in c.xpath('./p') if p.get('class')!='gpl-idols'];facttext='；'.join(facts)
    images=list(dict.fromkeys(x for x in c.xpath('.//div[contains(@class,"gpl-gallery")]//img/@data-src|.//div[contains(@class,"gpl-gallery")]//img/@src') if x.startswith('https://')))
    matched=[byid[i] for i in manual[index]] if index in manual else ([g for g in plush if norm(g['name'])==norm(title)] or [g for g in plush if base(g['name'])==base(title)])
    if index in [38,40,41]:
        number={38:'3',40:'2',41:'1'}[index]
        matched=[g for g in oldgoods if g['id'].startswith('zuta-db-') and norm(g['name']).startswith('もちどる(第'+number+'弾)')]
    if index==62:matched=[g for g in oldgoods if g['id'].startswith('zuta-db-') and norm(g['name']).startswith(norm(title))]
    if index==46:matched=[g for g in plush if '20cmぬいぐるみ' in g['name']]
    if index==44:matched=[g for g in plush if 'まんなかさいず' in g['name']]
    if not matched:
        assert index in [47,51,68],(index,title)
        gid='zuta-plush-card-'+hashlib.sha256(title.encode()).hexdigest()[:12];assert gid not in byid
        g={'id':gid,'kind':'merch','name':title,'originalName':title,'category':'娃娃 / 毛绒','originalType':'ぬいぐるみ,来源系列汇总','characters':roles or '来源未标注','manufacturer':'来源未标注','releaseDate':next((t for t in facts if t.startswith(('発売・登場：','発送・お渡し：'))),'来源未标注'),'price':'来源本条未列统一价格；搜索结果不作为报价','size':next((t for t in facts if t.startswith('サイズ：')),'来源未标注'),'description':'根据重新整理的毛绒汇总页补充系列档案；角色、日期与渠道为来源记录，不代表实时库存。','image':images[0] if images else w['poster'],'images':[],'sourceUrl':source,'sourceName':'学マスまとめ · 毛绒汇总','checkedAt':DATE,'channels':[],'specifications':[],'availability':'搜索入口不代表单品在售；厂商独立资料与库存请另行核对。'}
        w['merch'].append(g);matched=[g];byid[gid]=g;newids.append(gid)
    links=[]
    for shop in c.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," gpl-affiliate-shop ")]'):
        label=shop.xpath('string(.//p[contains(@class,"gpl-shop-label")])').replace('▼','').strip()
        name={'楽天市場':'乐天市场','駿河屋':'骏河屋','メルカリ':'Mercari（二手）','Amazon':'Amazon'}.get(label,label)
        assert name in ['Amazon','乐天市场','骏河屋','Mercari（二手）'],name
        for a in shop.xpath('.//a[@href]'):
            u=direct(a.get('href'));assert u.startswith('https://')
            links.append({'name':name,'url':u,'originalUrl':a.get('href'),'role':a.text_content().strip(),'linkType':'搜索页（'+a.text_content().strip()+'；并非单品页）','sourceNote':DATE+'来源角色按钮对应；搜索结果可能混入不同款、二手或非授权商品，不代表现货或售价。'})
    official=[u for u in c.xpath('.//a/@href') if u.startswith('https://') and any(t in u for t in ['bsp-prize.jp/','p-bandai.jp/'])]
    for g in matched:
        # A card can consolidate several historical records; keep the card context explicit.
        anchor=next(n.get('id') for n in c.iterancestors() if n.tag=='section' and n.get('id'))
        obs={'sourceName':'学マスまとめ · 新版毛绒卡片 · '+title,'sourceUrl':source+'#'+anchor,'sourceArticle':source,'releaseDate':facttext or '来源未列日期规格','price':'本卡未列统一价格；保留原商品报价','size':next((t for t in facts if t.startswith('サイズ：')),'本卡未标注尺寸'),'characters':roles,'checkedAt':DATE}
        g.setdefault('sourceObservations',[]).append(obs)
        g.setdefault('images',[])
        for image in (images if len(matched)==1 else []):
            if image not in g['images'] and image!=g['image']:g['images'].append(image)
        known={x['url'] for x in g['channels']}
        # If this historical record explicitly identifies a subset, retain only corresponding character searches.
        identity=norm(g['name']+' '+str(g.get('characters','')))
        shortnames=[a for a in ['咲季','手毬','ことね','燕','麻央','リーリヤ','千奈','清夏','広','星南','美鈴','佑芽','莉波','あさり','亜紗里'] if a in identity]
        candidates=[x for x in links if not shortnames or any(a in x['role'] for a in shortnames)]
        for link in candidates:
            if link['url'] not in known:
                g['channels'].append({k:v for k,v in link.items() if k!='role'});known.add(link['url']);newlinks+=1
        for u in official:
            if u not in known:g['channels'].append({'name':'官方商品资料','url':u,'linkType':'官方资料页（来源卡片列出，未逐一重新核对）','sourceNote':DATE+'原文资料入口；同一卡片可能包括不同角色，具体款式请核对。'});known.add(u);newlinks+=1
        g['checkedAt']=DATE
    mapping.append({'index':index,'sourceTitle':title,'goods':[g['id'] for g in matched],'sourceSearchLinks':len(links),'images':len(images)})

# The figure summary now repeats yesterday's known two-character preview: enrich it rather than duplicate it.
g=byid['zuta-preview-12413-angel-devil-saki-ume-202704'];change=next(a for a in probe['articleChanges'] if '/13353/' in a['url'])
for u in change['imagesAdded']:
    if u not in g['images']:g['images'].append(u)
g.setdefault('sourceObservations',[]).append({'sourceName':'学マスまとめ · 手办汇总新增单独图示','sourceUrl':'https://zutapoke.com/13353/','releaseDate':'2027年4月登场预定；仍为来源预告','price':'未列价格','checkedAt':DATE});g['checkedAt']=DATE
for number,note in [('14433','2026-10-28新版75张毛绒卡片已逐项对应馆藏：角色搜索入口明确标为搜索页，保留旧价格、月份、图片和链接；合并卡片的日期仅作来源观察，不覆盖角色不同批次。'),('13353','2026-10-28新增咲季Sugary devil、佑芽Sugary angel单独图示；合并进10月27日已有双角色系列预告，不重复计为新品。')]:
    a=next(a for a in w['articleIndex'] if a['url']=='https://zutapoke.com/'+number+'/');a.setdefault('sections',[]).append(note);a['checkedAt']=DATE
changed=[a['id'] for a,b in zip(w['merch'],before['items'][0]['merch']) if a!=b]
assert w['events']==before['items'][0]['events']
assert [g['id'] for g in oldgoods]==[g['id'] for g in w['merch'][:len(oldgoods)]]
for prev,now in zip(before['items'][0]['merch'],w['merch']):
    assert now['channels'][:len(prev['channels'])]==prev['channels']
    assert now.get('price')==prev.get('price') and now.get('releaseDate')==prev.get('releaseDate')
report=w['collectionReport'];report.update({'checkedAt':DATE,'products':len(w['merch']),'articlesRead':len(w['articleIndex']),'categories':dict(Counter(g['category'] for g in w['merch'])),'latestUpdate':{'checkedAt':DATE,'newProducts':len(newids),'changedProducts':len(changed),'newArticles':0,'changedArticles':2,'newChannelLinks':newlinks}});w['retrievedAt']=DATE
path.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
for name,value in [('gakumas-article-index.json',w['articleIndex']),('gakumas-collection-report.json',report)]:
    (ROOT/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
    for g in w['merch']:
        vals=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')]
        writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
audit={'checkedAt':probe['checkedAt'],'newProducts':len(newids),'changedProducts':len(changed),'newChannelLinks':newlinks,'newProductIds':newids,'changedProductIds':changed,'cardsMapped':mapping,'sourceErrors':probe['errors'],'limitations':'角色搜索页不代表单品、库存或报价；新整理的合并卡片可能涵盖多个批次，保留原商品日期价格，来源日期仅追加观察。历史游戏文章嵌入摘要变化未作为周边更新。'}
(ROOT/'data/gakumas-monitor-2026-10-28.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k not in ['cardsMapped','changedProductIds']},ensure_ascii=False))
