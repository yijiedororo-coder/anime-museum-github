"""Collect only the 51 product references in the new public Zutapoke article."""
import concurrent.futures, hashlib, io, json, re, urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse
from lxml import html
from PIL import Image, ImageChops
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'tools/zuta-monitor/2026-10-15'
DETAILS = OUT / 'curtain-details'
DETAILS.mkdir(exist_ok=True)
ARTICLE = 'https://zutapoke.com/28183/'
errors = []
def clean(s): return re.sub(r'\s+', ' ', s).strip()
def fetch(u, binary=False):
    p = DETAILS / (hashlib.sha256(u.encode()).hexdigest() + ('.img' if binary else '.html'))
    if p.exists(): return p.read_bytes() if binary else p.read_text(encoding='utf-8')
    with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'}), timeout=35) as r:
        raw = r.read()
        encoding = r.headers.get_content_charset() or 'utf-8-sig'
    if binary:
        p.write_bytes(raw); return raw
    text = raw.decode(encoding,errors='replace');p.write_text(text, encoding='utf-8');return text

listing = html.fromstring((OUT/'curtain-listing.html').read_text(encoding='utf-8'))
candidates = {}
for a in listing.xpath('//a[@href]'):
    u = a.get('href'); name = clean(a.text_content())
    if not name: continue
    if any(s in u for s in ['/fulltshirt_gkmas', '/cushion_gkmas', '/tape_gkmas']) or re.search(r'/astand_gkmas(1[4-9]|2[0-6])-big/', u):
        candidates[u] = name
assert len(candidates) == 51

def product(pair):
    u, name = pair
    d = html.fromstring(fetch(u));slug = urlparse(u).path.strip('/').split('/')[-1]
    title = clean(d.xpath('//title')[0].text_content())
    assert name in title
    prices = [clean(x.text_content()) for x in d.xpath('//*[@class="itemPrice"]')]
    for x in d.xpath('//script|//style'): x.drop_tree()
    text = clean(d.text_content())
    price = re.search(r'価格：([\d,]+)円',text)
    specs = {}
    for tr in d.xpath('//table[contains(@class,"item_detail_table")]//tr'):
        if not tr.xpath('./th') or not tr.xpath('./td'):continue
        key=clean(tr.xpath('./th')[0].text_content())
        if key in specs:key+='（尺码表）'
        specs[key]=' / '.join(clean(' / '.join(td.itertext())) for td in tr.xpath('./td'))
    gallery = list(dict.fromkeys(d.xpath(f'//a[contains(@href,"/parts/item_img/gkmas/{slug}/")]/@href')))
    buys = list(dict.fromkeys(d.xpath('//a[contains(.,"購入はこちら")]/@href')))
    buyLabels = {a.get('href'):clean(a.text_content()) for a in d.xpath('//a[contains(.,"購入はこちら")]')}
    start = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}:\d{2})より販売開始',text)
    schedule = [[clean(td.text_content()) for td in tr.xpath('./td')] for tr in d.xpath('//table[contains(@class,"nouki_table")]//tr') if len(tr.xpath('./td')) == 2]
    assert price and gallery and buys and schedule
    assert all(v.startswith('https://curtain-damashii.shop/shopdetail/') for v in buys)
    return {'name': name, 'url': u, 'slug': slug, 'price': price.group(1)+'円', 'specifications': specs, 'images': gallery, 'buyUrls': buys, 'buyLabels':buyLabels,'shippingSchedule': schedule,'saleStart':start.group(1) if start else None}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    products = list(pool.map(product,candidates.items()))

def shop_check(pair):
    u, expected_name = pair
    d=html.fromstring(fetch(u));title=clean(d.xpath('//title')[0].text_content())
    assert re.sub(r'\s+','',expected_name) in re.sub(r'\s+','',title),f'Shop product mismatch: {u}'
    return u, title
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    checked_shops=dict(pool.map(shop_check,[(u,p['name']) for p in products for u in p['buyUrls']]))
for p in products:p['verifiedShopTitles']={u:checked_shops[u] for u in p['buyUrls']}

article = html.fromstring((OUT/(hashlib.sha256(ARTICLE.encode()).hexdigest()+'.html')).read_text(encoding='utf-8'))
body = article.xpath('//main/article/div[@class="post_content"]')[0]
references = []
for heading in body.xpath('.//p[contains(@class,"is-style-icon_announce")]'):
    group = clean(heading.text_content())
    for a in heading.getnext().xpath('.//a[@href]'):
        images = a.xpath('.//img/@data-src')
        assert len(images) == 1
        references.append({'group': group, 'affiliateUrl': a.get('href'), 'image': images[0]})
assert len(references) == 51

def signature(u):
    im = Image.open(io.BytesIO(fetch(u,True))).convert('RGBA')
    white = Image.new('RGBA',im.size,'white');white.alpha_composite(im);im = white.convert('RGB')
    diff = ImageChops.difference(im, Image.new('RGB',im.size,'white')).convert('L')
    bbox = diff.point(lambda x: 255 if x>25 else 0).getbbox()
    if bbox:im=im.crop(bbox)
    rgb=np.asarray(im.resize((64,64))).astype(float)
    basis=np.cos(np.pi*np.arange(32)[:,None]*(2*np.arange(32)[None,:]+1)/64)*np.sqrt(2/32)
    basis[0]/=np.sqrt(2)
    coeff=(basis @ np.asarray(im.convert('L').resize((32,32))).astype(float) @ basis.T)[:8,:8].flatten()[1:]
    return rgb,coeff>np.median(coeff)
imageurls = list(dict.fromkeys([r['image'] for r in references] + [u for p in products for u in p['images']]))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    signatures = dict(zip(imageurls,pool.map(signature,imageurls)))

matches=[]
for ref in references:
    a,ah=signatures[ref['image']]
    options=[]
    for product in products:
        if not product['name'].startswith(ref['group'].split('（')[0]):continue
        gallery_scores=[]
        for image_url in product['images']:
            b,bh=signatures[image_url]
            mae=float(np.abs(a-b).mean());hamming=int(np.sum(ah!=bh))
            gallery_scores.append((mae+0.5*hamming,mae,hamming,image_url))
        score,mae,hamming,matched_image=min(gallery_scores)
        options.append((score,mae,hamming,product,matched_image))
    options.sort(key=lambda x:x[0]);best=options[0]
    matches.append({**ref,'product':best[3],'imageMatch':{'score':round(best[0],3),'meanError':round(best[1],3),'hamming':best[2],'nextScore':round(options[1][0],3),'matchedImage':best[4]}})
result={'article':ARTICLE,'checkedAt':'2026-10-15','products':matches,'errors':errors,'promotionLinkIssue':'首次原推广入口 DNS 无法解析；已核对厂商官网资料及其购买入口。'}
(OUT/'curtain-products.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
assert len({r['product']['url'] for r in matches})==51,'Image matches must be one-to-one'
assert max(r['imageMatch']['score'] for r in matches)<25,'Review uncertain product image matches'
assert all(r['imageMatch']['nextScore']-r['imageMatch']['score']>3 for r in matches),'Review ambiguous product image matches'
print(json.dumps({'products':len(matches),'shopPagesChecked':len(checked_shops),'groups':{g:sum(r['group']==g for r in matches) for g in dict.fromkeys(r['group'] for r in matches)},'maxImageMatchError':max(r['imageMatch']['score'] for r in matches),'examples':[{**r['product'],'imageMatch':r['imageMatch']} for r in matches if r['product']['slug'] in ['fulltshirt_gkmas01','astand_gkmas14-big','tape_gkmas01-b2ws','cushion_gkmas01']]},ensure_ascii=False))
