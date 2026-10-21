"""Import only freshly researched merchandise changes; preserve existing routes and facts."""
import copy
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from lxml import html

ROOT = Path(__file__).resolve().parent.parent
DATE = '2026-10-21'
CACHE = ROOT / 'tools/zuta-monitor' / DATE
SOURCE = 'https://zutapoke.com/28624/'
SUPPLEMENT = 'https://j-hobby.net/?p=1690165'
probe = json.loads((CACHE / 'probe.json').read_text(encoding='utf-8'))
research = json.loads((CACHE / 'research.json').read_text(encoding='utf-8'))
assert not probe['errors']
assert probe['checkedAt'].startswith(DATE)
assert all(not c['new'] and not c['changed'] and not c['removed'] for c in probe['csvChanges'].values())
assert len(research['records']) == 42

path = ROOT / 'data/gakumas-data.js'
data = json.loads(path.read_text(encoding='utf-8').split('=', 1)[1].strip().removesuffix(';'))
before = copy.deepcopy(data)
w = data['items'][0]
old = before['items'][0]
assert len(w['merch']) == 5371 and len(w['articleIndex']) == 284
backup = CACHE / 'before-update'
backup.mkdir(exist_ok=True)
for name in ['gakumas-data.js', 'gakumas-products.csv', 'gakumas-article-index.json', 'gakumas-collection-report.json']:
    assert not (backup / name).exists(), 'Do not rerun this one-shot import'
    (backup / name).write_bytes((ROOT / 'data' / name).read_bytes())

def clean(value):
    return re.sub(r'\s+', ' ', value).strip()

def doc(url):
    return html.fromstring((CACHE / (hashlib.sha256(url.encode()).hexdigest() + '.html')).read_text(encoding='utf-8'))

newids = []
oldids = {g['id'] for g in w['merch']}
oldurls = {c['url'] for g in w['merch'] for c in g['channels']}
idols = ['花海咲季', '月村手毬', '藤田ことね', '有村麻央', '葛城リーリヤ', '倉本千奈', '紫雲清夏', '篠澤広', '姫崎莉波', '花海佑芽', '秦谷美鈴', '十王星南', '雨夜燕']
for i, r in enumerate(research['records']):
    pid = r['productId']
    direct = 'https://www.animate-onlineshop.jp/products/detail.php?product_id=' + pid
    assert r['productUrl'] == direct and direct not in oldurls
    assert re.search(r'/pd/' + pid + r'/', r['supplementaryProductUrl'])
    gid = 'zuta-article-28624-animate-' + pid
    assert gid not in oldids
    if i < 39:
        single = ['1st Single', '2nd Single', '3rd Single'][i // 13]
        character = r['characterLabel']
        assert character == idols[i % 13] and single in r['name']
        name = f'3rd Single 完走纪念 · 官方亚克力立牌 · {character} / {single}'
        category = '立牌'
        originaltype = 'アクリルスタンド,3rd Single 完走記念,' + single
        price = '来源标价：2,200円 / 个（2026-10-21记录；不代表实时结算价）'
        variant = single + ' · ' + character
        specs = ['本档案为单个角色、单个Single图样的立牌；1st、2nd、3rd图样分别建档。', '来源商品图包含立牌及CD造型底座示意，不是音乐CD商品。']
    else:
        letter, count = [('A', 13), ('B', 12), ('C', 13)][i - 39]
        assert r['characterLabel'] == f'{letter}（全{count}種）'
        name = f'3rd Single 完走纪念 · 官方随机CD型钥匙扣 {letter} · 全{count}种'
        category = '挂件'
        originaltype = 'トレーディングCD型キーホルダー,3rd Single 完走記念,' + letter + '组'
        character = f'系列多角色（{letter}组全{count}种；角色名单以店内资料为准）'
        price = '来源标价：1,100円（销售单位在汇总页未注明，不作为BOX价格；2026-10-21记录）'
        variant = letter + f'组 · 全{count}种'
        specs = [f'补充资料页标题列明{letter}组全{count}种；保留为一个随机商品系列，不拆成可指定款式。', '抽选方式、每盒数量、是否一盒集齐及销售单位未在来源汇总页说明，需在商店确认。', 'CD造型为商品设计，不是音乐CD。']
    specs += ['发售月份、尺寸、材质及制造商：来源汇总页未标注；不以文章发布日期代替发售日。', '商品名、Single分组与A/B/C款式由第二份公开资料按相同Animate商品编号交叉核对，并检查来源商品图片。', 'Animate抽查商品页转入Queue-it动态等待页面，店内详情核查受限；没有确认库存、预约状态或实际运费。']
    g = {'id': gid, 'kind': 'merch', 'name': name, 'originalName': r['name'], 'category': category,
         'originalType': originaltype, 'characters': character, 'variant': variant,
         'manufacturer': '来源未标注', 'releaseDate': '来源未标注；店内发售日期尚未核实',
         'size': '来源未标注', 'price': price,
         'description': '学园偶像大师3rd Single完走纪念系列。保留来源图样与对应单品购买链接；不同Single、不同角色和随机系列分别归档。价格为来源文章的整理日记录。发售日期和库存尚未确认。',
         'image': r['image'], 'imageSource': r['image'], 'sourceUrl': SOURCE,
         'sourceName': '学マスまとめ · 3rd Single完走纪念周边', 'checkedAt': DATE, 'specifications': specs,
         'channels': [{'name': 'Animate', 'url': direct, 'originalUrl': r['originalUrl'],
                       'linkType': '商品页（原文编号对应；店内详情核查受限）',
                       'sourceNote': '来源图片链接与单品编号一一对应。抽查页面转入动态等待页，未核实店内规格、发售月份或库存。'}],
         'sourceObservations': [{'sourceName': 'j-hobby Collection · 名称与图样分组补充', 'sourceUrl': SUPPLEMENT,
                                 'releaseDate': '本页未标注发售月份', 'price': '本页未另列价格；标价以主来源记录为准',
                                 'size': '本页未标注尺寸', 'checkedAt': DATE}],
         'availability': '本次确认来源文章新增商品资料；不代表商店现货或正在受理预约。Animate店内详情核查受限，请打开原商品页确认。'}
    w['merch'].append(g)
    newids.append(gid)

battleurl = 'https://zutapoke.com/27849/'
battledoc = doc(battleurl)
battlebody = battledoc.xpath('//main/article/div[@class="post_content"]')[0]
amazonurls = list(dict.fromkeys(u for u in battlebody.xpath('.//a/@href') if urlparse(u).netloc == 'www.amazon.co.jp'))
assert len(amazonurls) == 1 and urlparse(amazonurls[0]).path == '/s'
amazon = amazonurls[0]
assert '学園アイドルマスター' in parse_qs(urlparse(amazon).query)['k'][0]
changed = []
for g in w['merch']:
    if g['id'] not in ['zuta-update-battlespirits-26rcb03', 'zuta-update-battlespirits-26rsd13']:
        continue
    assert not any(c['name'] == 'Amazon' for c in g['channels'])
    g.setdefault('history', []).append({k: copy.deepcopy(g.get(k)) for k in ['checkedAt', 'price', 'releaseDate', 'image', 'channels', 'description', 'availability']})
    g['channels'].append({'name': 'Amazon', 'url': amazon, 'originalUrl': amazon,
                          'linkType': '搜索页（Battle Spirits联名系列共用；非单品直达）',
                          'sourceNote': '2026-10-21来源新增Amazon标签及Amazon搜索链接；新面板正文仍写楽天市場，渠道归属以实际域名为准。面板系列标价为补充包BOX 5,808円、入门套装1,980円，不是已核实的Amazon报价。'})
    g['checkedAt'] = DATE
    g['description'] += ' 2026-10-21：来源新增Amazon系列搜索入口，需在结果中分别确认26RCB03补充包BOX与26RSD13入门套装；原报价、历史渠道和链接顺序完整保留。新增面板正文标题误写楽天市場，未将面板标价当作Amazon实时售价。'
    changed.append(g['id'])

a = next(a for a in w['articleIndex'] if a['url'] == battleurl)
a.setdefault('history', []).append({k: copy.deepcopy(v) for k, v in a.items() if k != 'history'})
a['checkedAt'] = DATE
a['sections'].append('2026-10-21：新增Amazon系列搜索链接，两个商品分别补充渠道。该链接不是单品页；面板标题存在楽天市場误标，5,808円与1,980円仅作来源系列标价，不作Amazon实时价格。')
newdoc = doc(SOURCE)
assert not any(a['url'] == SOURCE for a in w['articleIndex'])
w['articleIndex'].append({'title': clean(newdoc.xpath('string(//h1)')), 'url': SOURCE,
                         'sections': ['3rd Single完走纪念系列：39款官方亚克力立牌，按1st、2nd、3rd Single与13名角色拆分，每款2,200円。',
                                      '官方随机CD型钥匙扣A、B、C三组，来源标价1,100円；补充资料标题列A/C各13种、B组12种，销售单位与封入规则待店内确认。',
                                      '42个来源图片链接与Animate商品编号一一对应；发售月份、尺寸和厂商未标注，店内详情因动态等待页核查受限。',
                                      '文章发表于2026年10月21日，该日期不代表商品发售日期。'],
                         'prices': ['2,200円', '1,100円'], 'dates': [],
                         'image': newdoc.xpath('//meta[@property="og:image"]/@content')[0], 'checkedAt': DATE})
report = w['collectionReport']
report.update({'checkedAt': DATE, 'products': len(w['merch']), 'articlesRead': len(w['articleIndex']),
               'categories': dict(Counter(g['category'] for g in w['merch'])),
               'latestUpdate': {'checkedAt': DATE, 'newProducts': 42, 'changedProducts': 2, 'newArticles': 1, 'changedArticles': 1}})
w['retrievedAt'] = DATE

assert len(newids) == 42 and len(changed) == 2
assert len(w['merch']) == 5413 and len(w['articleIndex']) == 285
for prev, now in zip(old['merch'], w['merch']):
    for key in ['id', 'name', 'image', 'sourceUrl', 'price', 'releaseDate']:
        assert now.get(key) == prev.get(key), (prev['id'], key)
    assert now['channels'][:len(prev['channels'])] == prev['channels']
    if prev['id'] not in changed:
        assert now == prev
assert [g['id'] for g in w['merch'][:len(old['merch'])]] == [g['id'] for g in old['merch']]
assert data.keys() == before.keys()
path.write_text('window.MUSEUM_ADDITIONS = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
(ROOT / 'data/gakumas-article-index.json').write_text(json.dumps(w['articleIndex'], ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT / 'data/gakumas-collection-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
with (ROOT / 'data/gakumas-products.csv').open('w', encoding='utf-8-sig', newline='') as fp:
    writer = csv.writer(fp)
    writer.writerow(['商品ID', '商品名', '分类', '角色', '原始类型', '发售月份(来源)', '参考价(来源)', '尺寸', '渠道及链接', '来源', 'DB原编号', '其他同名记录', '整理日期'])
    for g in w['merch']:
        vals = [g['id'], g['name'], g['category'], g.get('characters', ''), g.get('originalType', ''), g.get('releaseDate', ''), g['price'], g.get('size', ''), json.dumps(g['channels'], ensure_ascii=False), g['sourceUrl'], '/'.join(g.get('sourceRecordIds', [])), json.dumps(g.get('variants', []), ensure_ascii=False), g['checkedAt']]
        writer.writerow(["'" + str(v) if str(v).startswith(('=', '+', '-', '@')) else v for v in vals])

audit = {'checkedAt': probe['checkedAt'], 'databaseRows': 5271, 'freshResponses': probe['freshResponses'],
         'articlesChecked': probe['articlesChecked'], 'archivePages': probe['archivePages'],
         'newArticles': [SOURCE], 'confirmedNewProducts': 42, 'substantiveChangedProducts': 2, 'substantiveChangedArticles': 1,
         'newProductIds': newids, 'changedProductIds': changed, 'crossCheckedProductLinkIds': [r['productId'] for r in research['records']],
         'sourceAnomalies': ['Battle Spirits新增Amazon面板的正文误写楽天市場，按实际URL标注为Amazon搜索入口，不认定为店内报价。', 'Animate抽查商品页转入动态等待页面；42个链接依原文单品编号保留，店内规格、发售月份与库存未核实。'],
         'ignoredChanges': '17篇仅推荐商品或嵌入摘要变化；PLv与ガシャ日程为游戏信息，不属于本次周边范围。',
         'errors': [], 'publication': 'pending'}
(ROOT / 'tools/monitor-check-2026-10-21.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'newProducts': len(newids), 'changedProducts': len(changed), 'products': len(w['merch']), 'articles': len(w['articleIndex'])}, ensure_ascii=False))
