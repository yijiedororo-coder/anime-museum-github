"""Collect bounded official catalogs; write research output without changing museum records."""
import concurrent.futures, hashlib, json, re, urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo
from lxml import html

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'tools/aobuta-research'
DATE = datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()
PRODUCTS, FAILURES = [], []
NAMES = ['桜島麻衣','古賀朋絵','双葉理央','豊浜のどか','梓川かえで','梓川花楓','牧之原翔子','美東美織','岩見沢寧々','赤城郁実','姫路紗良','広川卯月','梓川咲太','ミニスカサンタ']

def clean(s): return re.sub(r'\s+', ' ', s or '').strip()
def fetch(url):
    p = CACHE / (hashlib.sha256(url.encode()).hexdigest()+'.html')
    if not p.exists():
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        try: text = raw.decode('utf-8')
        except UnicodeDecodeError: text = raw.decode('cp932')
        p.write_text(text, encoding='utf-8')
    return html.fromstring(p.read_text(encoding='utf-8'))
def safe_fetch(u):
    try: return u, fetch(u)
    except Exception as e:
        FAILURES.append({'url':u, 'error':str(e)}); return u, None
def parallel(urls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        yield from pool.map(safe_fetch, sorted(set(urls)))
def category(n):
    for words, cat in [(['ぬいぐるみ','寝そべり','ちびぐるみ'],'娃娃 / 毛绒'),(['アクリルスタンド','アクリルフィギュア','アクリルキャラスタンド'],'立牌'),(['キーホルダー','ストラップ','チャーム'],'挂件'),(['フィギュア','Luminasta','XStellar','Coreful','AMP','ねんどろいど'],'手办'),(['プラモデル','MODEL SERIES'],'塑料模型'),(['バッジ'],'徽章'),(['タペストリー','ポスター','アクリルボード'],'海报 / 摆件'),(['ファイル','ステッカー','カード','色紙'],'卡片 / 文具'),(['シャツ','パーカー'],'服饰')]:
        if any(w in n for w in words): return cat
    return '生活 / 收藏'
def add(url, name, maker, images, release='', specs=None, price='', brand='', prize=False, variant='', channels=None):
    if not name or '青春ブタ' not in name and '桜島麻衣' not in name and '牧之原翔子' not in name: return
    images = list(dict.fromkeys(urljoin(url, i).replace('http://','https://',1) for i in images if i))
    p = dict(id='aobuta-maker-'+hashlib.sha256(url.encode()).hexdigest()[:16], name=clean(name), kind='merch', category=category(name), manufacturer=maker, productBrand=brand or maker, acquisitionType='娃娃机景品' if prize else '零售周边', variant=variant or '来源未单列版本', originalType='厂商商品 / '+maker, series=next((v for k,v in [('サンタクロース','圣诞女郎（TV）'),('おでかけシスター','外出妹（剧场版）'),('ランドセルガール','红书包女孩（剧场版）'),('ゆめみる少女','怀梦美少女（剧场版）'),('ディアフレンド','Dear Friend（剧场版）'),('バニーガール先輩','兔女郎学姐（TV）')] if k in name),'青春猪头少年系列'), characters='、'.join(n for n in NAMES if n in name) or '角色未在商品名列出，见来源图片', price='景品（无统一零售定价）' if prize else price or '来源未标价', releaseDate=release or '来源未标注完整发售日期', size=' / '.join(s for s in specs or [] if any(w in s for w in ['サイズ','全高','全長','スケール'])), specifications=specs or [], image=images[0] if images else 'assets/aobuta/dearfriend.jpg', images=images, sourceUrl=url, sourceName=maker+' · 官方产品目录', checkedAt=DATE, description='制造商公开的'+('娃娃机景品档案。普通版、限定版及再登场以各产品页面记录为准。' if prize else '零售周边档案。价格和发售安排按来源保存。'), channels=channels or [{'name':maker,'url':url,'linkType':'制造商产品资料（非实时库存）'}], availability='历史或预告产品资料，不代表当前有货。'+('通过游戏中心或在线抓娃娃平台投放；费用取决于平台和游玩次数，不能将单次游玩费当成商品价格。' if prize else '购买、预约、配送与库存请到原商品页核对。'))
    if not images: p['imagePlaceholder']=True
    for c in p['channels']:c['url']=c['url'].replace('http://','https://',1)
    PRODUCTS.append(p)

def taito():
    pending={'https://www.taito.co.jp/taito-prize/0000014375','https://www.taito.co.jp/taito-prize/0000003791','https://www.taito.co.jp/taito-prize/0452106100','https://www.taito.co.jp/taito-prize/0451800700'}; seen=set()
    while pending and len(seen)<220:
        batch=pending-seen; pending=set(); seen.update(batch)
        for u,d in parallel(batch):
            if d is None: continue
            title=d.xpath('//h2[@class="prize-detail-title"]')
            if not title or '青春ブタ' not in title[0].text_content(): continue
            name=clean(title[0].text_content()); date=d.xpath('//p[contains(@class,"prize-detail-text--red")]'); box=d.xpath('//div[@class="prize-detail-info"]/div[@class="prize-detail-text"]')
            text=clean(box[0].text_content()) if box else ''; size=re.search(r'サイズ(.+?)(?:種類|種 類|全\d|$)',text)
            specs=['サイズ：'+clean(size[1])] if size else []
            kinds=re.search(r'(?:種類|種類全|全)(\d+)\s*種',text)
            if kinds: specs.append('種類：全'+kinds[1]+'種')
            if '表情' in text and 'カラー' in text: specs.append('在线抓娃娃限定版：来源注明表情 / 服装颜色差异')
            og=d.xpath('//meta[@property="og:image"]/@content'); images=d.xpath('//div[contains(@class,"prize-detail-main")]//img[contains(@class,"prize-detail")]/@src')
            brand=next((b for b in ['AMP＋','AMP+','AMP','Coreful','Desktop Cute'] if b in name),'TAITO 景品')
            channels=[{'name':'TAITO','url':u,'linkType':'制造商景品资料（含来源店铺列表）'}]
            if 'タイクレ限定' in name: channels.append({'name':'TAITO 在线抓娃娃','url':'https://www.taito.co.jp/online_crane','linkType':'在线抓娃娃平台入口（非商品直购）'})
            add(u,name,'TAITO',og+images,clean(date[0].text_content()) if date else '',specs,brand=brand,prize=True,variant='タイクレ限定 / 在线抓娃娃限定' if 'タイクレ限定' in name else 'オンクレ限定 / 在线抓娃娃限定' if 'オンクレ限定' in name else 'Renewal / 改版' if 'Renewal' in name or 'リニューアル' in name else '普通版',channels=channels)
            for a in d.xpath('//a[@href]'):
                v=urljoin(u,a.get('href'))
                if re.search(r'/taito-prize/\d+$',v) and '青春ブタ' in a.text_content() and v not in seen: pending.add(v)
        print('TAITO official pages:',len(seen),'products:',len(PRODUCTS),flush=True)

def sega():
    urls=['https://segaplaza.jp/prize/'+p+'/' for p in ['D121919','D121798','D122302','D122516','D122099','D122100','B122156','D122452','D122706','D122718']]
    for u,d in parallel(urls):
        if d is None: continue
        data=[json.loads(s) for s in d.xpath('//script[@type="application/ld+json"]/text()')]
        p=next((x for x in data if x.get('@type')=='Product'),None)
        if not p: continue
        dates=d.xpath('//span[contains(@class,"dateSuffix")]/..'); specs=[clean(x.text_content()) for x in d.xpath('//ul[@class="spec"]/li') if not '©' in x.text_content()]
        name=p['name']; brand=next((b for b in ['Luminasta','XStellar','Yumemirize','Desktop×Decorate Collections','ふわぷち','寝そべり'] if b in name),'SEGA 景品')
        add(u,name,'SEGA',p.get('image',[]),clean(dates[0].text_content()) if dates else '',specs,brand=brand,prize=True,variant='来源正式产品款式',channels=[{'name':'SEGA','url':u,'linkType':'制造商景品产品资料'},{'name':'SEGA 取扱店铺','url':u+'?view=locations','linkType':'来源店铺查询（需核对当前是否投放）'}])

def charaon():
    lists={'https://www.charaon.jp/SHOP/130421/172662/list.html'}; visited=set(); urls=set()
    while lists:
        batch=lists-visited; visited.update(batch); lists=set()
        for u,d in parallel(batch):
            if d is None: continue
            lists.update(v for v in d.xpath('//link[@rel="next"]/@href') if v not in visited)
            for a in d.xpath('//a[@href]'):
                v=urljoin(u,a.get('href'))
                if re.search(r'/SHOP/AZAOB\w+\.html$',v): urls.add(v)
                if '/130421/172662/' in v and 'list' in v and v not in visited: lists.add(v)
        if len(visited)>8: break
    for u,d in parallel(urls):
        if d is None: continue
        product=None
        for s in d.xpath('//script[@type="application/ld+json"]/text()'):
            x=json.loads(s)
            for p in x if isinstance(x,list) else [x]:
                if p.get('@type')=='Product':product=p;break
        if not product: continue
        p=product; text=clean(d.text_content()); release=re.search(r'発売日\s*([\d年月日]+)',text); specs=[]
        for br in d.xpath('//p//br'):br.tail='\n'+(br.tail or '')
        for x in d.xpath('//p[contains(.,"■")]|//*[contains(text(),"■サイズ") or contains(text(),"■素材")]'):
            t=x.text_content()
            for line in t.splitlines():
                line=clean(line)
                if line.startswith('■') and len(line)<180: specs.append(line)
        images=p.get('image',[]); images=[images] if isinstance(images,str) else images
        for i in d.xpath('//img/@src'):
            if p['sku'] in i and 'pic-labo' in i: images.append(i)
        add(u,p['name'],'アズメーカー',images,release[0] if release else '',list(dict.fromkeys(specs)),price=f"{int(p['offers']['price']):,}日元（含税，来源记录）",brand='きゃらON！ / アズメーカー',channels=[{'name':'きゃらON！','url':u,'linkType':'制造商直营商品页'}])
    print('CharaON lists:',len(visited),'products:',len(urls),flush=True)

if __name__=='__main__':
    taito(); sega(); charaon()
    result={'checkedAt':DATE,'products':PRODUCTS,'failures':FAILURES}
    (CACHE/'maker-products.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    from collections import Counter
    print(json.dumps({'products':len(PRODUCTS),'makers':dict(Counter(p['manufacturer'] for p in PRODUCTS)),'failures':FAILURES},ensure_ascii=False),flush=True)
