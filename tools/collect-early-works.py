"""Fetch public manufacturer facts for the first chronological research batch.

Requires beautifulsoup4 (research-only dependency, not a website dependency).
Always fetches current pages; cached HTML is evidence, never an import input.
Only names, specifications, dates, prices, images and original links are extracted.
"""
import concurrent.futures
import hashlib
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
NOW = datetime.now(timezone(timedelta(hours=9)))
DAY = NOW.date().isoformat()
CACHE = ROOT / 'tools' / 'chronology-research' / DAY
CACHE.mkdir(parents=True, exist_ok=True)
MANIFEST, FAILURES, GOODS = [], [], {'onepiece': [], 'hotd': []}
LOCK = threading.Lock()
ALLOWED = {'www.megahobby.jp', 'bsp-prize.jp', 'www.cospa.com', 'gashapon.jp',
           'www.nbcuni.co.jp', 'store.kadokawa.co.jp', 'www.mugiwara-store.com'}


def clean(value):
    return re.sub(r'\s+', ' ', value or '').strip()


def text(node):
    return clean(node.get_text(' ', strip=True)) if node else ''


def url(base, value):
    result = urllib.parse.urljoin(base, value or '')
    return result if result.startswith('https://') else ''


def fetch(address):
    if urllib.parse.urlsplit(address).hostname not in ALLOWED:
        raise ValueError('Unapproved research host')
    try:
        request = urllib.request.Request(address, headers={'User-Agent': 'AnimeMuseumResearch/1.0 (public product archive)'})
        with urllib.request.urlopen(request, timeout=30) as response:
            if urllib.parse.urlsplit(response.url).hostname not in ALLOWED:
                raise ValueError('Unexpected redirect host')
            raw = response.read(6_000_001)
            if len(raw) > 6_000_000:
                raise ValueError('Source exceeds research size limit')
        stamp = datetime.now(timezone(timedelta(hours=9))).isoformat()
        name = hashlib.sha256(address.encode()).hexdigest()[:20] + '.html'
        (CACHE / name).write_bytes(raw)
        with LOCK:
            MANIFEST.append({'url': address, 'checkedAtJST': stamp, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
        return BeautifulSoup(raw, 'html.parser')
    except Exception as error:
        with LOCK:
            FAILURES.append({'url': address, 'reason': type(error).__name__ + ': ' + str(error)[:180]})
        return None


def category(name):
    for terms, result in [
        (['ぬいぐるみ', 'ちびぐるみ', 'クッション'], '娃娃 / 毛绒'),
        (['アクリルスタンド', 'アクレクト'], '立牌'),
        (['缶バッジ', 'ピンバッジ'], '徽章'),
        (['Tシャツ', 'パーカー', 'シャツ', '甚平', '制服', 'スカート'], '服饰'),
        (['チャーム', 'キーホルダー', 'ストラップ', 'アクセサリー', 'ラバーマスコット'], '挂件'),
        (['マグ', 'タオル', 'ケース', 'バッグ', 'フラッグ', 'ワッペン', 'ポーチ', 'ブランケット', 'ティッシュ', 'タイマー', 'ライト', 'タンブラー', 'グラス', 'カップ', 'プレート', 'バケット', '時計', 'トランク'], '生活 / 收藏'),
        (['色紙', 'クリアファイル', 'ペン', 'ステーショナリー'], '卡片 / 文具'),
        (['タペストリー', 'ポスター'], '海报 / 摆件'),
    ]:
        if any(term in name for term in terms):
            return result
    return '手办 / 收藏模型'


def add(work, name, source, maker, brand, price='', date='', image='', target='',
        kind='零售周边', cat='', specs=None, images=None, channels=None, note=''):
    name = clean(name)
    if not name:
        raise ValueError('Empty product name')
    identity = '\n'.join([work, name, target or source, date, price])
    goods = {
        'id': 'early-' + hashlib.sha256(identity.encode()).hexdigest()[:18],
        'name': name, 'kind': 'merch', 'category': cat or category(name),
        'originalType': brand, 'series': brand, 'characters': '角色及款式见原商品名 / 官方配图',
        'manufacturer': maker, 'productBrand': brand, 'acquisitionType': kind,
        'price': clean(price) or ('景品无统一零售价；抓取费用由运营店铺决定' if kind == '娃娃机景品' else '来源未标注价格'),
        'releaseDate': clean(date) or '来源未标注明确发售日期',
        'size': '来源目录未标尺寸；请核对商品详情',
        'description': '按官方公开目录登记的商品 / 系列档案。' + note,
        'specifications': specs or [], 'image': image, 'images': images or ([image] if image else []),
        'sourceUrl': source, 'sourceName': maker + ' · 官方公开资料', 'checkedAt': DAY,
        'channels': channels or [], 'addedInBatch': DAY + '-chronology-first',
        'availability': '历史及已公告商品资料，不表示当前有货。原价、投放与发售日期保留为来源记录；价格可能采用当时税率。未核查实时库存。',
        'imagePlaceholder': not bool(image),
    }
    if target and not channels:
        goods['channels'].append({'name': maker + ' 商品入口', 'url': target,
                                  'linkType': '官方目录列出的商品页（目标库存未核查）'})
    goods['channels'].append({'name': maker + ' 官方资料', 'url': source, 'linkType': '官方资料页 / 目录（非购买确认）'})
    GOODS[work].append(goods)
    return goods


def megahouse():
    pending, visited = {1}, set()
    while pending:
        page = min(pending)
        pending.remove(page)
        visited.add(page)
        address = f'https://www.megahobby.jp/products/portraitofpirates/{page}/?sort=new'
        soup = fetch(address)
        if soup is None:
            continue
        cards = soup.select('a:has(dd.p_name)')
        for card in cards:
            name = text(card.select_one('dd.p_name'))
            if 'ワンピース' not in name and 'ONE PIECE' not in name:
                continue
            img = card.select_one('dt img')
            add('onepiece', name, address, 'MegaHouse', 'Portrait.Of.Pirates',
                text(card.select_one('dd.price span')), text(card.select_one('dd.release span')),
                url(address, img.get('src')) if img else '', url(address, card['href']),
                cat='手办 / 收藏模型',
                note='保留普通、限定、复刻及再版目录记录；发售日期可能为历史日期或未来计划。')
        for anchor in soup.select('a[href]'):
            match = re.search(r'/products/portraitofpirates/(\d+)/', anchor['href'])
            if match:
                found = int(match[1])
                if found > 40:
                    raise ValueError('P.O.P pagination exceeded audited limit')
                if found not in visited:
                    pending.add(found)
        print(json.dumps({'source': 'MegaHouse', 'page': page, 'products': len(cards)}), flush=True)
        time.sleep(.2)


def banpresto():
    base = 'https://bsp-prize.jp/search/?ref=title&title=IP00002025'
    first = fetch(base)
    if first is None:
        return
    pages = max([1] + [int(m.group(1)) for a in first.select('a[href]')
                       if (m := re.search(r'[?&]page=(\d+)', a['href']))])
    if pages > 50:
        raise ValueError('Banpresto pagination exceeded audited limit')
    for page in range(1, pages + 1):
        address = base if page == 1 else base + '&page=' + str(page)
        soup = first if page == 1 else fetch(address)
        if soup is None:
            continue
        cards = soup.select('a:has(p.products_name)')
        for card in cards:
            name, date = text(card.select_one('p.products_name')), text(card.select_one('p.products_date'))
            img = card.select_one('img')
            if 'くじ' in name:
                kind = '抽签商品'
            elif '登場' in date:
                kind = '娃娃机景品'
            elif 'プレミアムバンダイ' in name or '発送' in date or 'オンラインストア' in name:
                kind = '零售 / 受注商品'
            else:
                kind = '获取方式见官方商品页'
            add('onepiece', name, address, 'BANDAI SPIRITS', 'Banpresto', date=date,
                image=url(address, img.get('src')) if img else '', target=url(address, card['href']), kind=kind,
                note='按作品筛选后的官方目录收录；一条多款系列保留为一条档案，不把随机款数当作独立商品数量。')
        print(json.dumps({'source': 'Banpresto', 'page': page, 'products': len(cards)}), flush=True)
        time.sleep(.2)
    # Plush detail pages add dimensions and the actual shop locator, rather than guessing a retail link.
    plush = [g for g in GOODS['onepiece'] if g['productBrand'] == 'Banpresto' and g['category'] == '娃娃 / 毛绒']
    for g in plush:
        target = g['channels'][0]['url']
        soup = fetch(target)
        if soup is None:
            continue
        spec = text(soup.select_one('.productDetail_spec dd'))
        if spec:
            g['specifications'].append(spec)
            match = re.search(r'約\s*[\d.]+\s*(?:cm|㎝|mm)', spec)
            if match:
                g['size'] = match.group(0)
        locator = soup.select_one('.productDetail_shopSearch a[href]')
        if locator and url(target, locator['href']):
            g['channels'].insert(1, {'name': 'Banpresto 对应景品店铺查询', 'url': url(target, locator['href']),
                                    'linkType': '官方店铺查询（非直购 / 非剩余库存）'})
        g['verificationUrl'] = target
        time.sleep(.12)


def cospa():
    address = 'https://www.cospa.com/cospa/itemlist/series_index/WA/itemp_series_id/00039'
    soup = fetch(address)
    if soup is None:
        return
    cards = soup.select('div.item_tn')
    for card in cards:
        anchor, img = card.select_one('h3 a[href]'), card.select_one('a.item-tn img')
        if not anchor:
            continue
        name = text(anchor)
        if name.endswith('..'):
            detail = fetch(url(address, anchor['href']))
            full_name = text(detail.select_one('h1.sp-product_title')) if detail else ''
            if full_name:
                name = full_name.removesuffix(' [ONE PIECE]').strip()
        specs = [text(card.select_one('.itemsize'))] if card.select_one('.itemsize') else []
        specs += ['目录颜色：' + ' / '.join(x['title'] for x in card.select('.colortip[title]'))] if card.select('.colortip[title]') else []
        add('onepiece', name, address, 'COSPA', 'COSPA ONE PIECE', text(card.select_one('samp strong')),
            image=url(address, img.get('src')) if img else '', target=url(address, anchor['href']), specs=specs)
    print(json.dumps({'source': 'COSPA', 'products': len(cards)}), flush=True)


def gashapon():
    address = 'https://gashapon.jp/onepiece/item/'
    soup = fetch(address)
    if soup is None:
        return
    cards = soup.select('li.pg-items__item')
    for card in cards:
        title = card.select_one('.pg-items__name img')
        if not title:
            continue
        name = title.get('alt', '')
        images = [url(address, i.get('src')) for i in card.select('.pg-detail__item img')]
        links = []
        for a in card.select('.pg-items__link a[href]'):
            target = url(address, a['href'])
            if not target:
                continue
            label = text(a)
            link_type = ('官方客服咨询（非购买入口）' if '問い合わせ' in label else
                         '官方玩法说明（非购买入口）' if '遊び方' in label else
                         '官方对应店铺查询（非实时库存）' if '店' in label else
                         '官方商品资料页' if '商品ページ' in label else '官方在线扭蛋 / 预约入口（非库存确认）')
            links.append({'name': 'BANDAI 扭蛋 · ' + label, 'url': target, 'linkType': link_type})
        add('onepiece', name, address, 'BANDAI', 'Gashapon ONE PIECE', text(card.select_one('.pg-items__price')),
            text(card.select_one('.pg-items__release')), images[0] if images else '', images=images,
            kind='扭蛋 / 在线扭蛋', channels=links, cat=category(name) if category(name) != '手办 / 收藏模型' else '扭蛋 / 迷你模型',
            note='价格为来源注明的单次或对应销售单位；整套款数并非保证抽取结果。')
    print(json.dumps({'source': 'Gashapon', 'products': len(cards)}), flush=True)


def hotd():
    base = 'https://www.nbcuni.co.jp/rondorobe/anime/hotd/'
    # Official historical music / home video / book directories.
    details = {}
    for section in ['hp0007', 'hp0008', 'hp0009']:
        address = base + 'contents/' + section + '/list00000000.html'
        soup = fetch(address)
        if soup is None:
            continue
        for a in soup.select('a[href]'):
            target = url(address, a['href'])
            if target and re.search(r'/contents/hp000[789]/index\d+\.html$', target):
                details[target] = text(a) or details.get(target, '')
    for address, label in sorted(details.items()):
        soup = fetch(address)
        if soup is None:
            continue
        heading = soup.find('h3')
        name = text(heading) or label
        body = text(soup)
        images = [url(address, i['src']) for i in soup.select('img[src]') if '/contents/' in i['src'] and ('/base/' in i['src'] or '/block/' in i['src'])]
        date = re.search(r'(20\d{2}[/年.-]\d{1,2}[/月.-]\d{1,2}日?)\s*発売', body)
        date_value = date.group(1) + ' 発売（当时公告）' if date else ''
        editions = []
        if 'Blu-ray' in name and 'DVD' in name:
            for edition in ['Blu-ray', 'DVD']:
                found = re.search(re.escape(edition) + r'\s*[￥¥]\s*([\d,]+)\s*\(([^)]+)\)\s*([A-Z]+-\d+)', body)
                if found:
                    editions.append((edition, '¥' + found.group(1) + ' (' + found.group(2) + '・当时税率)', found.group(3)))
        if editions:
            for edition, price, sku in editions:
                g = add('hotd', name.replace('Blu-ray&DVD', edition), address, 'NBCUniversal', 'TV动画卷装影像',
                        price, date_value, images[0] if images else '', cat='音乐 / 影像', specs=['官方品番：' + sku])
                g['description'] += 'Blu-ray与DVD分别登记；初回特典与通常特典以原官方页面为准。'
        else:
            prices = re.findall(r'[￥¥]\s*[\d,]+\s*(?:\([^)]{1,15}\))?', body)
            add('hotd', name, address, 'NBCUniversal' if '/hp0009/' not in address else '官方发行方见原页', '动画官方音像 / 书籍',
                ' / '.join(dict.fromkeys(prices[:4])), date_value, images[0] if images else '', cat='音乐 / 影像' if '/hp0009/' not in address else '书籍 / 场刊')
    # Early crane prizes explicitly documented by the anime's official publisher.
    address = base + 'news/hp0001/index00950000.html'
    soup = fetch(address)
    if soup:
        images = [url(address, i['src']) for i in soup.select('img[src]') if '/block/' in i['src']]
        for i, (name, cat, count) in enumerate([('Tシャツ', '服饰', '全5种'), ('マグカップ', '生活 / 收藏', '全2种'), ('ミニ抱き枕ストラップ', '挂件', '全3种')]):
            add('hotd', '学園黙示録 HIGHSCHOOL OF THE DEAD ' + name, address, 'コモン株式会社', '动画旧官网景品公告',
                image=images[i] if i < len(images) else '', kind='娃娃机景品', cat=cat, specs=[count],
                note='旧官网明确列为游乐场景品；该公告未给出明确投放年月，未推断日期。')
    address = base + 'news/hp0001/index00960000.html'
    soup = fetch(address)
    if soup:
        images = [url(address, i['src']) for i in soup.select('img[src]') if '/block/' in i['src']]
        add('hotd', '学園黙示録 × Fate/stay night C79联动Tシャツ', address, 'NBCUniversal / ロンドローブ', 'Comic Market 79',
            '¥2,000（税込・当时公告）', '2010-12-29 ～ 2010-12-31（C79会场）', images[0] if images else '',
            kind='活动会场限定', cat='服饰', specs=['GNZT-1157', '当时公告每人限购2件；历史规则，不是当前购买资格。'])
    address = base + 'news/hp0001/index00940000.html'
    soup = fetch(address)
    if soup:
        images = [url(address, i['src']) for i in soup.select('img[src]') if '/block/' in i['src']]
        add('hotd', '私立藤美学園女子制服', address, 'COSPA / COSPATIO', '官方制服商品公告',
            date='2月中旬予定（该公告正文未标年份）', image=images[0] if images else '', cat='服饰',
            note='保留官网历史公告；服装具体组件、尺码、价格需核对制造商原页。')
    # Original comics are explicitly marked as original-work material, not animation merchandise.
    address = 'https://store.kadokawa.co.jp/shop/series/series00028201'
    soup = fetch(address)
    if soup:
        seen = set()
        for a in soup.select('a[href]'):
            target = url(address, a['href'])
            if '/shop/g/g' not in target or target in seen:
                continue
            seen.add(target)
            detail = fetch(target)
            if detail is None:
                continue
            h1 = detail.select_one('h1.block-goods-name--text')
            name = text(h1)
            if '学園黙示録' not in name:
                continue
            body = text(detail)
            date = re.search(r'20\d{2}年\d{2}月\d{2}日', body)
            og = detail.select_one('meta[property="og:image"]')
            price = text(detail.select_one('.block-goods-price--price')).replace(' ', '')
            add('hotd', name, target, 'KADOKAWA', '原作漫画（非动画周边）', price + '（官方页面记录）' if price else '',
                date.group(0) if date else '', url(target, og.get('content')) if og else '', target,
                cat='书籍 / 原作漫画', note='作品的原作出版物，单列为原作漫画，不混同动画首播年份。')


def mugiwara():
    address = 'https://www.mugiwara-store.com/news/1492/'
    soup = fetch(address)
    if soup is None:
        return
    images = [url(address, i['src']) for i in soup.select('img[src]') if '/uploads/' in i['src'] and not any(x in i['src'] for x in ['logo', 'banner'])]
    rows = [('繋がるカラーアクリルスタンド', '1,540', '2025-08-09', '立牌'),
            ('トレーディングミニ色紙（全10種）', '770', '2025-08-09', '卡片 / 文具'),
            ('トレーディングアクリルチャーム（全10種）', '660', '2025-08-09', '挂件'),
            ('2連ワイヤーアクリルキーホルダー サウザンド・サニー号', '1,100', '2025-08-09', '挂件'),
            ('マルチクリアケース', '1,100', '2025-08-11', '生活 / 收藏')]
    body = text(soup)
    for name, price, date, cat in rows:
        if name not in body:
            raise ValueError('Mugiwara source changed; manual review required')
        g = add('onepiece', '麦わらストア 出張店 ' + name, address, 'ONE PIECE 麦わらストア', '出张店限定商品',
                '¥' + price + '（税込・单件）', date, images[0] if images else '', kind='门店限定', cat=cat,
                specs=['公告限定麦草商店出张店销售；常设店、原宿店及官方网店不在该次销售范围。'],
                note='页面配图为本批商品集合参考，不代表随机款式保证。')
        if images:
            g['specifications'].append('配图为官方公告商品集合图，具体角色与款式请查看来源。')


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(job) for job in [megahouse, banpresto, cospa, gashapon, hotd, mugiwara]]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    for work, records in GOODS.items():
        unique = {}
        for g in records:
            unique.setdefault(g['id'], g)
        GOODS[work] = list(unique.values())
    output = {'checkedAt': DAY, 'checkedAtJST': NOW.isoformat(),
              'scope': '首轮补充馆藏最早的1999与2010年作品；不是全市场穷尽调查。',
              'goods': GOODS, 'sources': sorted(MANIFEST, key=lambda x: x['url']), 'failures': FAILURES}
    (ROOT / 'data' / 'early-works-research.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'products': {k: len(v) for k, v in GOODS.items()}, 'sourcePages': len(MANIFEST), 'failures': FAILURES}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
