"""Apply only the confirmed Battle Spirits source update from the fresh October 14 check."""
import copy, csv, hashlib, json, re
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from lxml import html

ROOT = Path(__file__).resolve().parent.parent
DATE = '2026-10-14'
CACHE = ROOT / 'tools/zuta-monitor' / DATE
PROBE = json.loads((CACHE / 'probe.json').read_text(encoding='utf-8'))
assert not PROBE['errors'] and not PROBE['missingBaseline']
assert not PROBE['newArticles']
assert all(not v['new'] and not v['changed'] and not v['removed'] for v in PROBE['csvChanges'].values())
URL = 'https://zutapoke.com/27849/'
assert URL in [c['url'] for c in PROBE['articleChanges']]
raw = (CACHE / (hashlib.sha256(URL.encode()).hexdigest() + '.html')).read_text(encoding='utf-8')
body = html.fromstring(raw).xpath('//main/article/div[@class="post_content"]')[0]
source_text = re.sub(r'\s+', ' ', body.text_content()).strip()
assert '5,808円⇒4,937円' in source_text and '1,980円⇒1,683円' in source_text
source_link = next(u for u in body.xpath('.//a/@href') if 'affiliate.suruga-ya.jp' in u)
search_link = parse_qs(urlparse(source_link).query)['goods_url'][0]
assert search_link.startswith('https://www.suruga-ya.jp/search?')

files = ['gakumas-data.js', 'gakumas-products.csv', 'gakumas-article-index.json', 'gakumas-collection-report.json']
backup = CACHE / 'before-update'
backup.mkdir(exist_ok=True)
for file in files:
    target = backup / file
    if not target.exists():
        target.write_bytes((ROOT / 'data' / file).read_bytes())
path = ROOT / 'data/gakumas-data.js'
data = json.loads(path.read_text(encoding='utf-8').split('=', 1)[1].strip().removesuffix(';'))
before = copy.deepcopy(data)
work = data['items'][0]
targets = {
    'zuta-update-battlespirits-26rcb03': ('5,808', '4,937', 'BOX'),
    'zuta-update-battlespirits-26rsd13': ('1,980', '1,683', '套'),
}
changed = []
for g in work['merch']:
    if g['id'] not in targets:
        continue
    assert g['sourceUrl'] == URL
    base, quote, unit = targets[g['id']]
    new_price = f'{DATE}来源新增：骏河屋参考{base}→{quote}日元 / {unit}；'
    if g['price'].startswith(new_price):
        continue
    g.setdefault('history', []).append({k: copy.deepcopy(g.get(k)) for k in ['checkedAt', 'price', 'releaseDate', 'image', 'channels', 'description']})
    g['price'] = new_price + g['price']
    g['description'] += f' {DATE}核查：来源文章新增骏河屋渠道，参考报价为{base}→{quote}日元 / {unit}。所列链接是学园偶像大师系列预约商品的搜索页，需要在结果中确认具体规格；来源报价不代表实时库存或结算价。'
    g['channels'].append({
        'name': '骏河屋', 'url': search_link,
        'linkType': '搜索页（学园偶像大师系列共用；非单品直达）',
        'sourceNote': f'{DATE}来源文章新增，参考{base}→{quote}日元 / {unit}；原文章列系列搜索入口。',
        'originalUrl': source_link,
    })
    g['availability'] = '此前记录的DMM页面显示预约受付结束；本次仅核对汇总文章，未重新核查商店库存。请在商品页确认当前状态。'
    g['checkedAt'] = DATE
    changed.append(g['id'])
assert len(changed) == 2, 'Expected exactly two previously unprocessed product changes'

article = next(a for a in work['articleIndex'] if a['url'] == URL)
article.setdefault('history', []).append({k: copy.deepcopy(article.get(k)) for k in ['checkedAt', 'prices', 'dates', 'sections', 'image']})
article['prices'] = list(dict.fromkeys(re.findall(r'[\d,]+円', source_text)))
article['sections'].append(f'{DATE}渠道与报价核查：新增骏河屋系列搜索入口；輝けるアイドル补充包参考5,808→4,937日元 / BOX，始まりのステップ入门套装参考1,980→1,683日元 / 套。DMM入门套装另为6套BOX规格；来源报价不代表实时价格或库存。')
article['checkedAt'] = DATE
article['channelUpdates'] = article.get('channelUpdates', []) + [{
    'checkedAt': DATE, 'name': '骏河屋', 'url': search_link,
    'sourceUrl': URL, 'originalUrl': source_link,
    'linkType': '搜索页（系列共用）',
}]
summary = next(c for c in work['channelSummary'] if c['name'] == '骏河屋')
if '卡片 / 文具' not in summary['examples']:
    summary['examples'].append('卡片 / 文具')
report = work['collectionReport']
report['checkedAt'] = DATE
report['latestUpdate'] = {'checkedAt': DATE, 'newProducts': 0, 'changedProducts': 2, 'newArticles': 0, 'changedArticles': 1}
work['retrievedAt'] = DATE

# Preserve every original product, route, image, release date and channel order.
old_work = before['items'][0]
assert [g['id'] for g in work['merch']] == [g['id'] for g in old_work['merch']]
for old, new in zip(old_work['merch'], work['merch']):
    if old['id'] not in targets:
        assert old == new
    else:
        for key in ['id', 'name', 'releaseDate', 'image', 'sourceUrl']:
            assert old[key] == new[key]
        assert old['channels'] == new['channels'][:len(old['channels'])]
        assert old['price'] in new['price']
assert len(work['merch']) == 5272 and len(work['articleIndex']) == 281

path.write_text('window.MUSEUM_ADDITIONS = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
(ROOT / 'data/gakumas-article-index.json').write_text(json.dumps(work['articleIndex'], ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT / 'data/gakumas-collection-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
with (ROOT / 'data/gakumas-products.csv').open('w', encoding='utf-8-sig', newline='') as fp:
    writer = csv.writer(fp)
    writer.writerow(['商品ID', '商品名', '分类', '角色', '原始类型', '发售月份(来源)', '参考价(来源)', '尺寸', '渠道及链接', '来源', 'DB原编号', '其他同名记录', '整理日期'])
    for g in work['merch']:
        values = [g['id'], g['name'], g['category'], g.get('characters', ''), g.get('originalType', ''), g.get('releaseDate', ''), g['price'], g.get('size', ''), json.dumps(g['channels'], ensure_ascii=False), g['sourceUrl'], '/'.join(g.get('sourceRecordIds', [])), json.dumps(g.get('variants', []), ensure_ascii=False), g['checkedAt']]
        writer.writerow(["'" + v if str(v).startswith(('=', '+', '-', '@')) else v for v in values])
audit = {
    'checkedAt': PROBE['checkedAt'], 'databaseRows': 5271, 'freshResponses': 300,
    'articlesChecked': 281, 'archivePages': 16, 'newArticles': [],
    'confirmedNewProducts': 0, 'substantiveChangedProducts': 2, 'substantiveChangedArticles': 1,
    'changes': [{'article': URL, 'productIds': changed, 'channel': '骏河屋', 'prices': {'26RCB03_BOX': '5,808→4,937円', '26RSD13_single': '1,980→1,683円'}}],
    'ignoredChanges': [{'article': 'https://zutapoke.com/12464/', 'reason': '游戏ガシャ历史表移除一个预测标记，非本次周边商品范围；未改变商品档案。'}],
    'errors': [], 'publication': 'pending',
}
(ROOT / 'tools' / f'monitor-check-{DATE}.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'newProducts': 0, 'changedProducts': len(changed), 'newArticles': 0, 'changedArticles': 1, 'products': len(work['merch']), 'csvRows': len(work['merch'])}, ensure_ascii=False))
