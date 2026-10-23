"""Merge fresh source-linked retailer additions without replacing existing records."""
import copy
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
from zoneinfo import ZoneInfo
from lxml import html

ROOT = Path(__file__).resolve().parent.parent
DATE = '2026-10-23'
assert datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat() == DATE
CACHE = ROOT / 'tools/zuta-monitor' / DATE
probe = json.loads((CACHE / 'probe.json').read_text(encoding='utf-8'))
assert probe['checkedAt'].startswith(DATE) and not probe['errors']
assert all(not x['new'] and not x['changed'] and not x['removed'] for x in probe['csvChanges'].values())
path = ROOT / 'data/gakumas-data.js'
data = json.loads(path.read_text(encoding='utf-8').split('=', 1)[1].strip().removesuffix(';'))
before = copy.deepcopy(data)
w = data['items'][0]
changed = set()
added = []
observed = set()

def imagekey(u):
    return re.sub(r'-\d+x\d+(?=\.[a-z]+$)', '', urlparse(u).path)

def direct(u):
    u = 'https:' + u if u.startswith('//') else u
    q = parse_qs(urlparse(u).query)
    for k in ['vc_url', 'a8ejpredirect']:
        if k in q:
            return q[k][0]
    if '/aff/click.cgi/' in u and 'product%2F' in u:
        return 'https://www.neowing.co.jp/' + unquote(u.split('/')[-1])
    return u

for article in ['28183', '28368']:
    source = 'https://zutapoke.com/' + article + '/'
    document = html.fromstring((CACHE / (hashlib.sha256(source.encode()).hexdigest() + '.html')).read_text(encoding='utf-8'))
    body = document.xpath('//main/article/*[contains(concat(" ",normalize-space(@class)," ")," post_content ")]')[0]
    goods = [g for g in w['merch'] if g.get('sourceUrl') == source]
    assert len(goods) == (51 if article == '28183' else 1)
    byimage = {}
    for g in goods:
        for u in [g.get('image', ''), *g.get('images', [])]:
            if u:
                byimage.setdefault(imagekey(u), set()).add(g['id'])
    byid = {g['id']: g for g in goods}
    current = None
    for a in body.xpath('.//a'):
        original = a.get('href', '')
        u = direct(original)
        host = urlparse(u).netloc
        if host not in ['anime-store.jp', 'colleize.com', 'www.neowing.co.jp']:
            continue
        images = [x for x in a.xpath('.//img/@data-src|.//img/@src') if x.startswith('https:')]
        matches = set().union(*(byimage.get(imagekey(x), set()) for x in images)) if images else set()
        if images and not matches:
            current = None
            continue  # unrelated sidebar/recommendation images
        if matches:
            assert len(matches) == 1, (u, matches)
            current = byid[next(iter(matches))]
        elif not (host == 'colleize.com' and re.fullmatch(r'(?:M|L|XL)サイズ', a.text_content().strip()) and current):
            continue
        g = current
        if any(c['url'] == u for c in g['channels']):
            continue
        assert u.startswith('https://') and ('/products/' in u or host in ['colleize.com', 'www.neowing.co.jp'])
        size = a.text_content().strip()
        if not size and article == '28183' and host == 'colleize.com' and 'Tシャツ' in g['name']:
            size = 'Mサイズ（同图下方尺码链接对应）'
        name = {'anime-store.jp': 'AnimeStore', 'colleize.com': 'Colleize', 'www.neowing.co.jp': 'NeoWing'}[host]
        channel = {'name': name, 'url': u, 'originalUrl': 'https:' + original if original.startswith('//') else original,
                   'linkType': '商品页（来源图片对应' + ('；' + size if size else '') + '；店内规格与库存未核实）',
                   'sourceNote': DATE + '按来源正文商品图及其下方明确尺码链接对应；不把广告推荐当新品，不代表实时库存。'}
        g['channels'].append(channel)
        changed.add(g['id'])
        added.append({'id': g['id'], 'name': g['name'], 'channel': channel})
        observationkey = (g['id'], name)
        if observationkey not in observed:
            price = ('7,700円（グラフィックTシャツ）' if 'Tシャツ' in g['name'] else
                     '4,400円' if g['category'] == '立牌' or 'タペストリー' in g['name'] else '2,970円') if article == '28183' else ('3,960円' if name == 'Colleize' else '3,049円（来源列出3,960円参考价）')
            g.setdefault('sourceObservations', []).append({'sourceName': '学マスまとめ · ' + name + '新增渠道', 'sourceUrl': source,
                'productUrl': u, 'price': price + '；来源2026-10-23报价，未核实店内结算价', 'releaseDate': '本次来源增补未另列月份；保留原商品发售记录', 'checkedAt': DATE})
            observed.add(observationkey)
        g['checkedAt'] = DATE
        quote = next(o['price'] for o in g['sourceObservations'] if o.get('checkedAt') == DATE and o.get('sourceName') == '学マスまとめ · ' + name + '新增渠道')
        channel['sourceNote'] += ' ' + quote

assert len(added) == 130 and len(changed) == 52
for old, new in zip(before['items'][0]['merch'], w['merch']):
    assert old['id'] == new['id']
    assert new['channels'][:len(old['channels'])] == old['channels']
    for key in old:
        if key not in ['channels', 'sourceObservations', 'checkedAt']:
            assert old[key] == new[key], (old['id'], key)

for number in ['28183', '28368']:
    a = next(a for a in w['articleIndex'] if a['url'] == 'https://zutapoke.com/' + number + '/')
    a['checkedAt'] = DATE
    a.setdefault('sections', []).append('2026-10-23补充：' + ('AnimeStore与Colleize商品页，按来源图片及M/L/XL尺码逐项映射；保留既有官方、NeoWing及Animate链接。' if number == '28183' else '新增NeoWing及Colleize商品链接；来源报价分别为3,049円和3,960円，不代表实时库存或结算价。'))

report = w['collectionReport']
report.update({'checkedAt': DATE, 'products': len(w['merch']), 'articlesRead': len(w['articleIndex']),
               'categories': dict(Counter(g['category'] for g in w['merch'])),
               'latestUpdate': {'checkedAt': DATE, 'newProducts': 0, 'changedProducts': len(changed), 'newArticles': 0, 'changedArticles': 2, 'newChannelLinks': len(added)}})
w['retrievedAt'] = DATE
path.write_text('window.MUSEUM_ADDITIONS = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
for filename, payload in [('gakumas-article-index.json', w['articleIndex']), ('gakumas-collection-report.json', report)]:
    (ROOT / 'data' / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
with (ROOT / 'data/gakumas-products.csv').open('w', encoding='utf-8-sig', newline='') as fp:
    writer = csv.writer(fp)
    writer.writerow(['商品ID','商品名','分类','角色','原始类型','发售月份(来源)','参考价(来源)','尺寸','渠道及链接','来源','DB原编号','其他同名记录','整理日期'])
    for g in w['merch']:
        values = [g['id'],g['name'],g['category'],g.get('characters',''),g.get('originalType',''),g.get('releaseDate',''),g.get('price',''),g.get('size',''),json.dumps(g['channels'],ensure_ascii=False),g['sourceUrl'],'/'.join(g.get('sourceRecordIds',[])),json.dumps(g.get('variants',[]),ensure_ascii=False),g.get('checkedAt','')]
        writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in values])
audit = {'checkedAt': probe['checkedAt'], 'newProducts': 0, 'changedProducts': len(changed), 'newChannelLinks': len(added), 'changedProductIds': sorted(changed), 'addedLinks': added,
         'ignoredChanges': 'sunflower及藤田ことね文章仅调整商店排列；PLv新文章与ガシャ变更为游戏攻略；3rd Single渠道事实已收录。', 'sourceErrors': probe['errors']}
(ROOT / 'data/gakumas-monitor-2026-10-23.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k not in ['addedLinks','changedProductIds']},ensure_ascii=False))
