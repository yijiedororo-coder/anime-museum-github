import csv, json, re, urllib.request, hashlib, time, sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from lxml import html

sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).resolve().parent.parent
cache=root/'tools/zuta-archive'; cache.mkdir(exist_ok=True)
def fetch(url):
    p=cache/(hashlib.sha256(url.encode()).hexdigest()+'.html')
    if p.exists(): return p.read_text(encoding='utf-8')
    for retry in range(3):
        try:
            b=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35).read().decode('utf-8-sig')
            p.write_text(b,encoding='utf-8'); return b
        except Exception:
            if retry==2: raise
            time.sleep(1+retry)
def clean(s): return re.sub(r'\s+',' ',s).strip()
def canon(u):
    for _ in range(6):
        q=parse_qs(urlparse(u).query)
        nxt=next((q[k][0] for k in ['vc_url','a8ejpredirect','lsurl','pc','lurl','goods_url'] if k in q),None)
        if not nxt: break
        u=nxt
    return u.replace('http://','https://',1)
first=html.fromstring(fetch('https://zutapoke.com/category/merchandise/'))
pageurls={'https://zutapoke.com/category/merchandise/'}
for u in first.xpath('//a/@href'):
    if re.search(r'/category/merchandise/page/\d+/',u): pageurls.add(u)
last=max([int(re.search(r'/page/(\d+)/',u)[1]) for u in pageurls if '/page/' in u] or [1])
pageurls.update('https://zutapoke.com/category/merchandise/page/'+str(n)+'/' for n in range(2,last+1))
articles={}; failures=[]
with ThreadPoolExecutor(max_workers=4) as ex:
    tasks={ex.submit(fetch,u):u for u in sorted(pageurls)}
    for f in as_completed(tasks):
        u=tasks[f]
        try:
            d=html.fromstring(f.result())
            for a in d.xpath('//a[contains(@class,"p-postList__link")]'):
                link=a.get('href'); ts=a.xpath('.//*[contains(@class,"p-postList__title")]')
                if link and re.match(r'https://zutapoke.com/\d+/$',link): articles[link]=clean(ts[0].text_content() if ts else a.text_content())
        except Exception as e: failures.append({'url':u,'reason':str(e)})
print('Archive pages:',len(pageurls),'article URLs:',len(articles),flush=True)
intel=[]; dolls=[]
with ThreadPoolExecutor(max_workers=4) as ex:
    tasks={ex.submit(fetch,u):u for u in articles}
    for f in as_completed(tasks):
        u=tasks[f]
        try:
            doc=html.fromstring(f.result()); bodies=doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," post_content ")]')
            body=max(bodies,key=lambda b:len(b.text_content())) if bodies else doc
            text=clean(body.text_content())
            og=doc.xpath('//meta[@property="og:image"]/@content')
            headings=[clean(x.text_content()) for x in body.xpath('.//h2|.//h3|.//h4')]
            prices=list(dict.fromkeys(re.findall(r'[0-9,]+(?:円|円税込)',text)))
            dates=list(dict.fromkeys(re.findall(r'20\d{2}年\s*\d{1,2}月(?:\s*\d{1,2}日)?',text)))
            intel.append({'title':articles[u],'url':u,'sections':headings,'prices':prices,'dates':dates,'image':og[0] if og else '', 'checkedAt':'2026-10-06'})
            if u=='https://zutapoke.com/14433/':
                hs=body.xpath('.//h3|.//h4')
                for h in hs:
                    name=clean(h.text_content())
                    if not any(k in name for k in ['ちびぐるみ','ぬいぐるみ','たぴぬい','ぬいピン','ぬい','もちもち']): continue
                    if any(k in name for k in ['リンク','販売サイト','通販サイト']): continue
                    parts=[]
                    for n in h.itersiblings():
                        if n.tag in ['h2','h3','h4']: break
                        parts.append(n)
                    imgs=[n for p in parts for n in p.xpath('.//img')]
                    src=next((i.get('data-src') or i.get('src') for i in imgs if (i.get('data-src') or i.get('src','')).startswith('https:')),None)
                    if not src: continue
                    links=[canon(x) for p in parts for x in p.xpath('.//a/@href') if x.startswith('http') and 'wp-content/uploads' not in x]
                    detail=clean(' '.join(p.text_content() for p in parts))
                    size=re.findall(r'(?:サイズ|高さ)[：: ]*[^。]{0,35}?(?:cm|㎝)',detail)
                    date=re.findall(r'20\d{2}年\d{1,2}月(?:\d{1,2}日)?',detail+' '+name)
                    dolls.append({'name':name,'image':src,'sourceUrl':u,'size':size,'date':date[:2],'links':list(dict.fromkeys(links))})
        except Exception as e: failures.append({'url':u,'reason':str(e)})
        if len(intel)%40==0: print('Read articles:',len(intel),flush=True)
rows=list(csv.DictReader(open(root/'tools/goodsdb.csv',encoding='utf-8-sig')))
shops={r['shop']:r for r in csv.DictReader(open(root/'tools/shopset.csv',encoding='utf-8-sig'))}
names={'rakuten':'乐天市场','animate':'Animate','amiami':'AmiAmi','7net':'Seven Net','eeoStore':'eeo Store','GAMERS':'Gamers','surugaya':'骏河屋','ASOBISTORE':'ASOBI STORE','PREMIUMBANDAI':'Premium Bandai','imasofficial':'偶像大师官方','mercari':'Mercari（二手）','YAHOO':'Yahoo购物','MOVIC':'Movic'}
def category(t):
    if 'ぬい' in t or 'ちびぐるみ' in t:return '娃娃 / 毛绒'
    if 'フィギュア' in t:return '手办'
    if 'アクリルスタンド' in t or '等身パネル' in t:return '立牌'
    if 'バッジ' in t:return '徽章'
    if 'キーホルダー' in t:return '挂件'
    if any(x in t for x in ['カード','ステッカー','クリアファイル']):return '卡片 / 文具'
    if any(x in t for x in ['アクリルパネル','アクリルブロック','アート','ポスター','タペストリー']):return '海报 / 摆件'
    if 'CD' in t:return '音乐'
    if '書籍' in t:return '书籍'
    if 'アパレル' in t or 'シャツ' in t:return '服饰'
    if any(x in t for x in ['タオル','マット','うちわ','ライト']):return '生活 / 应援'
    return '其他'
def channels(r):
    links=[]
    for key,s in shops.items():
        v=r.get(key,'').strip()
        if not v: continue
        if v=='1': url=s['top']; kind='商店入口'
        elif v=='2':
            q=quote('学園アイドルマスター '+r['name'],safe='')
            if key=='rakuten':
                q=quote(r['name'],safe='').replace('%20','+').replace('%','%25'); url=s['url_front']+q+s['url_back']+q+'%252F'
            elif key=='surugaya':url=s['url_front']+quote(quote(r['name'],safe='').replace('%20','+'),safe='')+s['url_back']
            else:url=s['url_front']+q+s['url_back']
            kind='商品搜索'
        elif v.startswith('http'):url=v;kind='来源链接'
        else:continue
        url=canon(url)
        path=urlparse(url).path.lower()
        if kind=='来源链接':
            kind='来源直链'
            if re.search(r'(search|/collections/|/category/|/list)',url.lower()):kind='搜索 / 分类页'
            elif path in ('','/'):kind='商店入口'
        if url.startswith('https://'):links.append({'name':names.get(key,key),'url':url,'linkType':kind,'sourceNote':r.get(key+'_pick','').strip()})
    return links
p=root/'data/gakumas-data.js'; old=json.loads(p.read_text(encoding='utf-8').split(' = ',1)[1].rstrip().rstrip(';')); work=old['items'][0]
existing=[g for g in work['merch'] if g['id'].startswith('gakumas-')]
goods=[]; seen={}; duplicate=0
for r in rows:
    name=r['name'].strip(); idol=r['idol'].strip(); key=(re.sub(r'\s+','',name),idol)
    if not name:continue
    ch=channels(r)
    if key in seen:
        prev=seen[key]; duplicate+=1
        for c in ch:
            if c['url'] not in [x['url'] for x in prev['channels']]:prev['channels'].append(c)
        prev['sourceRecordIds'].append(r['No']);prev.setdefault('variants',[]).append({'sourceRecordId':r['No'],'releaseDate':r['date'],'price':r['price'],'originalType':r['type'],'image':r['imageURL'],'channels':ch});continue
    g={'id':'zuta-db-'+r['No'],'kind':'merch','name':name,'category':category(r['type']),'originalType':r['type'],'characters':idol,'releaseDate':r['date'].strip(),'price':r['price'].strip() or '来源未标价','description':'按来源数据库记录整理；角色、类型和发售月份见下方。','image':r['imageURL'].strip(),'imageSource':r['imageURL'].strip(),'sourceUrl':'https://zutapoke.com/goodsdb/','sourceName':'学マスまとめ · 商品数据库','sourceRecordIds':[r['No']],'checkedAt':'2026-10-06','channels':ch,'availability':'来源链接可能是商品页、搜索页或商店入口；库存与预约状态需在商店确认。'}
    if not g['image'].startswith('https://'): g['image']=work['localPoster']
    goods.append(g);seen[key]=g
# Keep the prior curated entries and their numeric deep links stable.
for g in existing:
    if g['category']=='毛绒':g['category']='娃娃 / 毛绒'
for d in dolls:
    if any(re.sub(r'\s+','',d['name'])==re.sub(r'\s+','',g['name']) for g in goods):continue
    goods.append({'id':'zuta-plush-'+hashlib.sha256(d['name'].encode()).hexdigest()[:12],'kind':'merch','name':d['name'],'category':'娃娃 / 毛绒','originalType':'ぬいぐるみ汇总','characters':'来源标题见商品名','releaseDate':' / '.join(d['date']) or '来源未标注完整日期','size':' / '.join(d['size']),'price':'来源未标价 / 景品或历史商品','description':'娃娃汇总页的系列记录，包含历史与预告款；来源文章的“発売前”等标签可能已过期，本站不据此判断实时库存。','image':d['image'],'imageSource':d['image'],'sourceUrl':d['sourceUrl'],'sourceName':'学マスまとめ · 娃娃汇总','checkedAt':'2026-10-06','channels':[{'name':('官方商品资料' if any(k in urlparse(u).netloc for k in ['bsp-prize','idolmaster','p-bandai']) else '来源销售链接'),'url':u,'linkType':'资料 / 销售链接'} for u in d['links']],'availability':'景品、历史商品与预告款请通过来源及官方页面核对。'})
work['merch']=existing+goods
ch={c['name'] for g in work['merch'] for c in g['channels']}
work['channelSummary']=[{'name':n,'description':'来源列出的购买或资料渠道；请在详情辨别商品页、搜索页与官方资料链接','examples':list(dict.fromkeys(g['category'] for g in work['merch'] if any(c['name']==n for c in g['channels'])))[:6],'sourceUrl':'https://zutapoke.com/goodsdb/'} for n in sorted(ch)]
report={'checkedAt':'2026-10-06','databaseRows':len(rows),'databaseProducts':len(seen),'mergedDuplicateRows':duplicate,'archivePages':len(pageurls),'articlesRead':len(intel),'plushSupplement':len(dolls),'products':len(work['merch']),'categories':dict(Counter(g['category'] for g in work['merch'])),'failures':failures,'imagePolicy':'新增数据库图片引用来源公开图片地址，旧19条仍为本地图片。'}
work['collectionReport']=report;work['articleIndex']=sorted(intel,key=lambda x:x['url'])
p.write_text('window.MUSEUM_ADDITIONS = '+json.dumps(old,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
(root/'data/gakumas-collection-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'data/gakumas-article-index.json').write_text(json.dumps(intel,ensure_ascii=False,indent=2),encoding='utf-8')
with (root/'data/gakumas-products.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    writer=csv.writer(fp);writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
    for g in work['merch']:
        values=[g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g['price'],g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),'2026-10-06']
        writer.writerow([("'"+v if str(v).startswith(('=','+','-','@')) else v) for v in values])
print(json.dumps(report,ensure_ascii=False),flush=True)
