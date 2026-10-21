"""Merge primary-source research without rebuilding the existing museum catalog."""
import copy
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / 'tools/gakumas-oct20-research'
DATE = '2026-10-21'
OFFICIAL = 'https://idolmaster-official.jp/news/01_20075'
THIRD = 'https://shop.asobistore.jp/category/gakuen_3rdcd_comp_gd'
OUEN = json.loads((RESEARCH / 'ouenbu-urls.json').read_text(encoding='utf-8'))['url']

def read(name):
    return json.loads((RESEARCH / name).read_text(encoding='utf-8'))

def clean(value):
    return re.sub(r'\s+', ' ', value).strip()

def norm(value):
    return re.sub(r'\s+', '', value)

def table(row):
    return {key: clean(value) for group in row['tables'] for key, value in group}

def specs(row):
    return [key + '：' + value for key, value in table(row).items()]

path = ROOT / 'data/gakumas-data.js'
data = json.loads(path.read_text(encoding='utf-8').split('=', 1)[1].strip().removesuffix(';'))
before = copy.deepcopy(data)
w = data['items'][0]
old = before['items'][0]
assert len(old['merch']) == 5413 and not old.get('events')
assert len(old['articleIndex']) == 285
backup = RESEARCH / 'before-update'
backup.mkdir(exist_ok=True)
for f in ['gakumas-data.js', 'gakumas-products.csv', 'gakumas-article-index.json', 'gakumas-collection-report.json']:
    if not (backup / f).exists():
        (backup / f).write_bytes((ROOT / 'data' / f).read_bytes())
if not (backup / 'events.before.js').exists():
    (backup / 'events.before.js').write_bytes((ROOT / 'public-site/dist/events.js').read_bytes())

byid = {g['id']: g for g in w['merch']}
newids = []
changed = set()

def history(g):
    if g['id'] not in changed:
        g.setdefault('history', []).append({k: copy.deepcopy(v) for k, v in g.items() if k != 'history'})
        changed.add(g['id'])

def channel(g, name, url, kind='商品页', note=''):
    if any(c['url'] == url for c in g['channels']):
        return
    assert url.startswith('https://')
    g['channels'].append({'name': name, 'url': url, 'linkType': kind,
                          'sourceNote': note or DATE + '核对公开商品资料；不代表实时库存或结算价。'})

def add(g):
    assert g['id'] not in byid
    assert g['image'].startswith('https://') and g['sourceUrl'].startswith('https://')
    g['checkedAt'] = DATE
    g['originalType'] += ',10月20日专题'
    w['merch'].append(g)
    byid[g['id']] = g
    newids.append(g['id'])

def core(row, gid, category, characters):
    facts = table(row)
    delivery = facts.get('お届け', facts.get('発売日', '来源未标注'))
    return {'id': gid, 'kind': 'merch', 'name': row['name'], 'originalName': row['name'],
            'category': category, 'originalType': category, 'characters': characters,
            'manufacturer': facts.get('レーベル', '商品页未单列制造商'),
            'acquisitionType': '官方受注 / 商品资料', 'price': f"ASOBI STORE：{row['priceYen']:,}円（含税；{DATE}资料快照）",
            'releaseDate': delivery.split('※')[0].strip(), 'size': facts.get('商品仕様', facts.get('仕様', '来源未标注')),
            'description': '按官方商品页核对价格、规格和批次；公告日、受注截止与发货/发行日期分别记录。',
            'image': row['image'], 'imageSource': row['image'], 'images': [row['image']],
            'sourceUrl': row['url'], 'sourceName': 'ASOBI STORE · 官方商品资料', 'specifications': specs(row),
            'channels': [{'name': 'ASOBI STORE', 'url': row['url'], 'linkType': '官方商品页',
                          'sourceNote': DATE + '逐页核对规格与价格；所列日程不等于现货库存。'}],
            'availability': '以官方商品页对应受注批次为准；本档案不报告实时库存。'}

asobi = read('asobi-products.json')
assert len(asobi) == 85 and len({r['url'] for r in asobi}) == 85
idols = ['花海咲季', '月村手毬', '藤田ことね', '有村麻央', '葛城リーリヤ', '倉本千奈', '紫雲清夏', '篠澤広', '姫崎莉波', '花海佑芽', '秦谷美鈴', '十王星南', '雨夜燕']
for i, row in enumerate(asobi[:39]):
    assert 'B2タペストリー' in row['name'] and row['priceYen'] == 5000
    role = idols[i % 13]
    assert norm(role) in norm(row['name'])
    g = core(row, 'official-third-tapestry-' + row['url'].rsplit('/', 1)[-1], '海报 / 摆件', role)
    g['name'] = '3rd Single 完走纪念 · B2挂画 · ' + role + ' / ' + ['1st Single', '2nd Single', '3rd Single'][i // 13]
    g['originalType'] = 'タペストリー,3rd Single 完走記念,' + ['1st Single', '2nd Single', '3rd Single'][i // 13]
    g['size'] = '约W515×H728mm（B2）'
    g['description'] += ' 10月20日开始受注、11月15日截止；ASOBI STORE批次预计2027年3月上旬起陆续发货。该挂画与同封面的立牌是不同商品。'
    g['specifications'] += ['定价5,000日元/幅（含税）。受注期：2026年10月20日至11月15日。', '聚酯本体、PVC管、嫘萦吊绳；套装含挂画1幅、管2根及绳1条。']
    add(g)

existing42 = [g for g in old['merch'] if g['id'].startswith('zuta-article-28624-animate-')]
assert len(existing42) == 42
for row in asobi[39:81]:
    if 'アクリルスタンド' in row['name']:
        variant = norm(re.findall(r'【([^】]+)】', row['name'])[-1])
        found = [g for g in existing42 if variant == norm(re.findall(r'【([^】]+)】', g['originalName'])[-1])]
    else:
        letter = re.search(r'CD型キーホルダー\s*([ABC])', row['name'])[1]
        found = [g for g in existing42 if re.search(r'CD型キーホルダー\s*' + letter, g['originalName'])]
    assert len(found) == 1, row['name']
    g = byid[found[0]['id']]
    history(g)
    g['price'] = f"ASOBI STORE官方：{row['priceYen']:,}円 / 个或包（含税；{DATE}快照；旧来源报价保留在历史记录）"
    g['releaseDate'] = 'ASOBI STORE：2027年3月上旬起陆续发货；Animate批次日期尚未独立核实'
    g['size'] = '立牌本体约W90×H162mm；底座约W80×H80mm' if 'アクリルスタンド' in row['name'] else '本体约W45×H41×D12mm（不含金属件）；CD片约直径32mm'
    g['specifications'] = specs(row) + ['ASOBI STORE受注：10月20日至11月15日；Animate自10月21日起受注相应立牌与钥匙扣。', '原Animate链接、编号、图片和店内核查限制保留；新增ASOBI官方页可核对规格。']
    if 'CD型キーホルダー' in row['name']:
        g['specifications'] += ['官方已确认每包仅含1个随机钥匙扣，不是整盒价格。A/C各13种、B组12种（B不含雨夜燕的2nd图样）。']
        g['characters'] = ','.join(idols if letter != 'B' else [r for r in idols if r != '雨夜燕'])
    g['description'] += ' 本次补充官方单品核对：明确尺寸、材质、每包数量与ASOBI批次的2027年3月交付日程。'
    g['images'] = list(dict.fromkeys([*g.get('images', []), row['image']]))
    g['verificationUrl'] = row['url']
    g['originalType'] += ',10月20日专题'
    g['checkedAt'] = DATE
    g.setdefault('sourceObservations', []).append({'sourceName': 'ASOBI STORE · 官方规格核对', 'sourceUrl': row['url'], 'releaseDate': '2027年3月上旬起陆续发货', 'price': str(row['priceYen']) + '円（含税）', 'size': g['size'], 'checkedAt': DATE})
    channel(g, 'ASOBI STORE', row['url'], '官方商品页（价格、规格、受注批次已核对）')

for row in asobi[81:]:
    is_stand = 'アクリルスタンド' in row['name']
    role = '秦谷美鈴' if '美鈴' in row['name'] else '月村手毬'
    if not is_stand and role == '月村手毬':
        g = byid['zuta-db-394']
        history(g)
        g['releaseDate'] += '；本次ASOBI再受注：2027年2月中旬起依次发货'
        g['description'] += ' 10月20日官方提醒本轮受注于10月25日截止；原2025年3月发行记录不覆盖，本轮为不同再受注批次。'
        g['images'] = list(dict.fromkeys([*g.get('images', []), row['image']]))
        g['verificationUrl'] = row['url']
        g['specifications'] = specs(row) + ['本轮受注截止为2026年10月25日；与历史首发月份分开记录。']
        g['checkedAt'] = DATE
        g['originalType'] += ',10月20日专题,ハリネズミゆたんぽ'
        g.setdefault('sourceObservations', []).append({'sourceName': 'ASOBI STORE · 再受注', 'sourceUrl': row['url'], 'releaseDate': '2027年2月中旬起依次发货', 'price': '7,800円（含税）', 'size': '套约H180×W240×D345mm；袋体550ml', 'checkedAt': DATE})
        channel(g, 'ASOBI STORE', row['url'], '官方商品页（本轮再受注）')
    else:
        g = core(row, 'official-hedgehog-' + row['url'].rsplit('/', 1)[-1], '立牌' if is_stand else '娃娃 / 毛绒', role)
        g['originalType'] = 'アクリルスタンド,ハリネズミゆたんぽ' if is_stand else '湯たんぽ,ハリネズミゆたんぽ'
        g['description'] += ' 10月20日为受注截止提醒，并非当天首次发布。该轮10月25日截止，2027年2月中旬起发货。'
        add(g)

product_names = ['亚克力立牌', '亚克力立牌13人全套（附背景板）', '花海咲季立体立牌', '随机徽章（13种）', '徽章13种全套BOX', 'CD风亚克力卡与徽章套装', '随机透明卡（13种）', '透明卡13种全套BOX', '随机视觉透明卡vol.6（12种）', '视觉透明卡vol.6全套BOX', '随机视觉透明卡vol.7（12种）', '视觉透明卡vol.7全套BOX', '倉本千奈发夹', '卡片收纳袋', '刺绣徽章13种全套', '随机刺绣徽章（13种）', '在线受注BIG立牌', '在线受注等身板']
categories = ['立牌', '立牌', '立牌', '徽章', '徽章', '卡片 / 文具', '卡片 / 文具', '卡片 / 文具', '卡片 / 文具', '卡片 / 文具', '卡片 / 文具', '卡片 / 文具', '服饰', '生活 / 应援', '徽章', '徽章', '立牌', '海报 / 摆件']
ouen = read('ouenbu-products.json')
assert len(ouen) == 18
for i, row in enumerate(ouen):
    product = next(v for v in row['ld'] if v.get('@type') == 'Product')
    offers = product['offers']
    offers = offers if isinstance(offers, list) else [offers]
    description = product['description']
    assert '2026年11月6日(金)10:00' in description
    variants = row['variants']
    for v in variants:
        offer = next(o for o in offers if parse_qs(urlparse(o['url']).query).get('variant') == [str(v['id'])])
        price = int(v['price']) // 100 if 'price' in v else int(float(offer['price']))
        assert float(offer['price']) == price and offer['priceCurrency'] == 'JPY'
        role = norm(v['title']) if len(variants) > 1 else '系列多角色（款式与数量见详情）'
        if 'hanamisaki' in row['url']:
            role = '花海咲季'
        if 'barrette_kuramotochina' in row['url']:
            role = '倉本千奈'
        image = (v.get('featured_image') or {}).get('src') or row['image'][0]
        image = 'https:' + image if image.startswith('//') else image
        if image.startswith('http://hatsuboshi.store.mynavi.jp/'):
            image = 'https://' + image[len('http://'):]
        name = '初星商店 · 应援部 · ' + product_names[i] + (' / ' + role if len(variants) > 1 else '')
        factual = description.split('販売開始')[0]
        notes = ['官方标注11月6日10:00开始销售；发货安排在开售时另行公布。', '价格来自对应款式的官方公开商品资料，不把通用模板中的售罄/在库标签当作本批实际状态。']
        if i in [16, 17]:
            notes.append('该在线受注款不在实体店售卖；不要与店头普通立牌混为同规格。')
        if 'コンプリート' in row['title']:
            notes.append('来源将其列为全套/完整BOX；与随机单包分别建档，避免直接比较单包和整套价格。')
        elif 'ランダム' in row['title']:
            notes.append('随机单包不可指定；购买种数相同的包数也不保证集齐全部款式。')
        if 'H1100mm' in factual:
            notes.append('立体立牌的枠パーツ原文写H1100mm，可能存在笔误；此数值尚待店铺确认，未擅自修正。')
        notes.append('配送：通常一单900日元，北海道/冲绳1,200日元；等身板商品页单列3,000日元。日本境外不直送，具体以对应商品规则为准。')
        g = {'id': 'official-ouenbu-' + str(v['id']), 'kind': 'merch', 'name': name, 'originalName': row['title'] + (' / ' + v['title'] if len(variants) > 1 else ''),
             'category': categories[i], 'originalType': '应援部,ハツボシストア応援部,' + product_names[i], 'characters': role,
             'manufacturer': '商品页未单列制造商', 'acquisitionType': '官方预告 / 定期受注' if i in [16, 17] else '官方店铺销售预告',
             'price': f'官方标价：{price:,}円（含税；按该款式或套装计价）', 'releaseDate': '2026年11月6日10:00开售；本批发货日期另行公布',
             'size': '详见下方官方尺寸、材质与套装说明', 'description': '10月20日直播公开应援部视觉。本档案按可指定角色、随机单包和完整套装拆分；当前记录为11月6日销售预告。',
             'image': image, 'imageSource': image, 'sourceUrl': row['url'], 'sourceName': 'ハツボシストアONLINE · 官方商品资料',
             'specifications': ['来源规格：' + clean(factual), *notes, '来源商品识别号：' + (v.get('barcode') or v.get('sku') or '未标注')],
             'channels': [{'name': 'ハツボシストア', 'url': offer['url'], 'linkType': '官方商品页（已定位对应角色/款式）', 'sourceNote': '销售前资料快照；11月6日10:00开售，发货待后续公告。'}],
             'availability': '核查时属于销售前预告；不能依据页面模板的通用库存文字判断已售罄或有现货。'}
        add(g)

music = read('music-products.json')
for row in music:
    if 'Agitato' in row['name']:
        g = byid['gakumas-19']
        history(g)
        g['releaseDate'] = '2027年1月20日预计发行；ASOBI STORE预约至2026年11月8日'
        g['specifications'] = specs(row) + ['三人合唱版与13名角色的完整独唱版；预约赠贴纸以库存和店铺规则为准。']
        g['verificationUrl'] = row['url']
        g['checkedAt'] = DATE
        g['originalType'] = g.get('originalType', 'CD') + ',10月20日专题'
        g.setdefault('sourceObservations', []).append({'sourceName': 'ASOBI STORE · 官方发行资料', 'sourceUrl': row['url'], 'releaseDate': '2027年1月20日', 'price': '3,500円（含税）', 'size': table(row).get('仕様', '见商品页'), 'checkedAt': DATE})
    else:
        assert row['priceYen'] in [3000, 11000]
        vol = None if 'コンプリート' in row['name'] else re.search(r'Vol\.([123])$', row['name'])
        chars = ','.join(idols)
        if vol:
            chars = {1: '有村麻央,葛城リーリヤ,姫崎莉波,花海佑芽', 2: '花海咲季,月村手毬,藤田ことね,篠澤広,雨夜燕', 3: '倉本千奈,紫雲清夏,秦谷美鈴,十王星南'}[int(vol[1])]
        g = core(row, 'official-conceptual-' + row['url'].rsplit('/', 1)[-1], '音乐', chars)
        g['originalType'] = 'CD,Conceptual Single Collection'
        g['description'] += ' 本企划于9月23日已发表，10月20日直播更新曲目信息并提醒11月15日预约截止；不能算作10月20日首次开启。'
        if vol and vol[1] == '2':
            g['specifications'].append('Vol.2：nazonozo、ORDER FAKE、神かわいい、め、滞羽色の薄明与五曲伴奏。')
        if not vol:
            g['specifications'].append('完整特别套装包含3张CD、巡演视觉纸艺盒及「標」标志钥匙扣；ASOBI预约贴纸按渠道规则附赠。')
        add(g)

keyvisual = next(r['officialImage'] for r in read('official-slide-matches.json') if r['slide'].endswith('-11-1280x720.jpg'))
for role in ['葛城リーリヤ', '紫雲清夏', '姫崎莉波']:
    g = {'id': 'official-kuji-part7-' + hashlib.sha256(role.encode()).hexdigest()[:10], 'kind': 'merch',
         'name': '一番赏Part7 · ' + role + ' 1/7 Gracemaster手办（预告）', 'originalName': '一番くじ 学園アイドルマスター Part7 / ' + role,
         'category': '手办', 'originalType': '一番くじ,Part7,1/7 Gracemaster,预告', 'characters': role,
         'manufacturer': 'BANDAI SPIRITS（一番赏）', 'acquisitionType': '一番赏抽选（未开售）',
         'price': '系列每抽850円（含税）；不是指定手办的售价，不保证抽中该角色', 'releaseDate': '2026年12月12日起依次推出（店铺可能有差异）',
         'size': '1/7比例；具体高度尚未公开', 'description': '10月20日官方确认三名角色的1/7 Gracemaster手办与圣歌队×星座主题。当前图片为系列绘图预告，不能作为该手办实物造型。',
         'image': keyvisual, 'imageSource': keyvisual, 'imagePlaceholder': True, 'sourceUrl': 'https://1kuji.com/products/gkmas07',
         'sourceName': '一番赏官方商品页 / 10月20日官方总公告', 'specifications': ['官方确认角色：葛城リーリヤ、紫雲清夏、姫崎莉波。', '本次未确认各奖等级、数量、全奖项内容与手办单独成品图，后续补充。', '取扱店列罗森等；具体各店销售时间不同，非全部门店保证上架。'],
         'channels': [{'name': '官方商品资料', 'url': 'https://1kuji.com/products/gkmas07', 'linkType': '官方抽赏资料页（非指定角色单买入口）'}],
         'availability': '12月12日起推出的预告；尚未据此确认开售库存或各奖剩余数量。'}
    add(g)

events = read('curated-events.json')
assert len(events) == 27
events[-1]['pending'] += ['来源列出的楽天ブックス两条直达页核查时返回「页面不存在」；未将其作为已验证的购买入口。']
w['events'] = events
w['eventAsOf'] = DATE + '（日本时间；重点调查10月20日公告）'
w['eventSources'] = {'oct20': ['10月20日官方直播总公告', OFFICIAL]}
w['eventJournal'] = {'eyebrow': 'GAKUMAS / NEWS JOURNAL · 2026.10.20', 'title': '10月20日公告，逐条收进档案。',
                     'summary': '27条活动与提醒 · 首次公告、截止提醒、在售与游戏活动分别注明。所有时刻为日本时间。',
                     'credit': '官方门户、ASOBI STORE、初星商店与一番赏逐项核查 ·', 'placeholder': '转售、罗森、应援部、初星FES…',
                     'links': [{'name': '10月20日官方总公告', 'url': OFFICIAL}, {'name': '完走纪念官方商品目录', 'url': THIRD}, {'name': '阅读完整调查报告', 'url': 'https://anime-museum-yijie.workspace-007182.chatgpt.site/reports/gakumas-2026-10-20.html'}]}
w['officialResearch'] = {'checkedAt': DATE, 'announcementDate': '2026-10-20', 'newProducts': len(newids), 'changedProducts': len(changed), 'eventRecords': len(events), 'primaryProductPagesRead': 108, 'newIds': newids, 'changedIds': sorted(changed),
                        'limits': ['广播总公告的日期和21/22点表述互相矛盾，等待独立节目确认。', 'Animate自动读取受限；新增ASOBI官方页已补足本渠道规格，不推断Animate批次。', 'GOLD RUSH8的楽天ブックス来源页返回未找到，仅保留其资料线索。', '罗森完整商品目录、应援团服详情和Part7完整奖项尚待公布。']}
assert len(newids) == 103 and len(changed) == 44, (len(newids), len(changed))
assert len(w['merch']) == 5516
assert [g['id'] for g in w['merch'][:len(old['merch'])]] == [g['id'] for g in old['merch']]
for prev, now in zip(old['merch'], w['merch']):
    for k in ['id', 'name', 'image', 'sourceUrl']:
        assert now.get(k) == prev.get(k), (prev['id'], k)
    assert now['channels'][:len(prev['channels'])] == prev['channels']
    if prev['id'] not in changed:
        assert now == prev
    else:
        assert now['history'][-1]['price'] == prev['price']
assert w['articleIndex'] == old['articleIndex']
channels = {c['name'] for c in w['channelSummary']}
for g in w['merch']:
    for c in g['channels']:
        if c['name'] not in channels:
            w['channelSummary'].append({'name': c['name'], 'description': '官方商品页；具体角色、款式、销售期与发货说明见详情。', 'examples': list(dict.fromkeys(x['category'] for x in w['merch'] if any(v['name'] == c['name'] for v in x['channels']))), 'sourceUrl': OUEN})
            channels.add(c['name'])
report = w['collectionReport']
report.update({'checkedAt': DATE, 'products': len(w['merch']), 'categories': dict(Counter(g['category'] for g in w['merch'])),
               'latestUpdate': {'checkedAt': DATE, 'newProducts': len(newids), 'changedProducts': len(changed), 'newArticles': 0, 'changedArticles': 0, 'newEvents': len(events), 'scope': '10月20日官方公告深入调查'}})
w['retrievedAt'] = DATE

path.write_text('window.MUSEUM_ADDITIONS = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
(ROOT / 'data/gakumas-collection-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
with (ROOT / 'data/gakumas-products.csv').open('w', encoding='utf-8-sig', newline='') as fp:
    writer = csv.writer(fp)
    writer.writerow(['商品ID', '商品名', '分类', '角色', '原始类型', '发售月份(来源)', '参考价(来源)', '尺寸', '渠道及链接', '来源', 'DB原编号', '其他同名记录', '整理日期'])
    for g in w['merch']:
        values = [g['id'], g['name'], g['category'], g.get('characters', ''), g.get('originalType', ''), g.get('releaseDate', ''), g['price'], g.get('size', ''), json.dumps(g['channels'], ensure_ascii=False), g['sourceUrl'], '/'.join(g.get('sourceRecordIds', [])), json.dumps(g.get('variants', []), ensure_ascii=False), g['checkedAt']]
        writer.writerow(["'" + str(v) if str(v).startswith(('=', '+', '-', '@')) else v for v in values])
(ROOT / 'data/gakumas-oct20-research.json').write_text(json.dumps(w['officialResearch'], ensure_ascii=False, indent=2), encoding='utf-8')

reports = ROOT / 'reports'
reports.mkdir(exist_ok=True)
lines = ['# 学园偶像大师：2026年10月20日活动与周边深入调查', '', '核查：2026年10月21日，日本时间。重点覆盖10月20日20:00官方直播及关联商店。', '',
         f'本次新增103条商品/系列档案，补全44条已有记录，加入27条活动与提醒；完整周边库现为5,516条。原1,427部作品库保留。', '',
         '这不是“昨天新增103款商品”的统计：其中包含当日新受注、未来新主题、旧商品的截止提醒及档案补漏。', '',
         '## 应优先关注的日期', '', '- 10月25日：刺猬暖水袋系列受注截止。', '- 10月28日09:59：终场官方转售截止。', '- 11月6日10:00：初星商店应援部开售。', '- 11月8日：Agitato的ASOBI预约截止。', '- 11月10日：罗森联动开始，完整商品与规则待公布。', '- 11月15日：完走纪念周边与Conceptual CD的ASOBI预约截止。', '- 11月23日18:00：终场线上票销售截止。', '- 12月12日：一番赏Part7起售预告。', '',
         '## 27条活动与提醒', '', '| 条目 | 类型 | 开始 / 截止（日本时间） | 重点 | 来源 |', '|---|---|---|---|---|']
for e in events:
    lines.append('| ' + ' | '.join([e['name'], e['announcementType'], e['start'] + (' → ' + e['end'] if e['end'] else ''), e['reward'], '[原公告](' + e['sourceUrl'] + ')']) + ' |')
lines += ['', '## 关键商品整理', '', '| 系列 | 档案处理 | 价格与交付 |', '|---|---|---|',
          '| 3rd Single完走纪念 | 新补39款B2挂画；原39款立牌和3组钥匙扣补官方渠道与规格 | 挂画5,000；立牌2,200；钥匙扣1,100日元/包。ASOBI批次2027年3月上旬起发货。 |',
          '| 初星商店应援部 | 官方18个商品页拆为54条可指定角色/随机系列/全套记录 | 普通立牌1,900、BIG立牌4,950、等身板36,300日元；11月6日10:00开售，发货待公布。 |',
          '| 刺猬暖水袋 | 3条补档，1条旧手毬暖水袋保留首发记录并补再受注 | 暖水袋7,800、立牌1,900日元；本轮2027年2月中旬起发货。 |',
          '| Conceptual Single Collection | 补Vol.1～3及完整特别套装4条 | 单卷3,000、特别套装11,000日元；2027年1月27日发行。9月已发表，10月20日是曲目/截止提醒。 |',
          '| Agitato | 补全原有记录的官方发行、截止和特典信息 | 3,500日元；2027年1月20日发行，ASOBI预约至11月8日。 |',
          '| 一番赏Part7 | 三名角色的手办预告分别建档 | 每抽850日元不是手办单买价；12月12日起，完整奖项/成品图待公布。 |', '',
          '## 需要继续核查', '', *['- ' + v for v in w['officialResearch']['limits']],
          '- 应援部立体立牌的框件尺寸原文有H1100mm，可能笔误；保留来源说明，不擅自改数。',
          '- 普通随机包与完整BOX分开；不能把“出率提高”写成保证，也不能将预告状态当作现货。', '',
          '## 本次新增103条商品/系列及购买资料', '', '| 商品 | 来源价 | 交付 / 发售 | 对应入口 |', '|---|---|---|---|']
for gid in newids:
    g = byid[gid]
    lines.append('| ' + ' | '.join([g['name'], g['price'], g['releaseDate'], '[商品/资料页](' + g['channels'][0]['url'] + ')']) + ' |')
lines += ['', '## 逐项活动规则', '']
for e in events:
    lines += ['### ' + e['name'], '', e['summary'], '', '费用/门槛：' + e['cost'], '', *['- ' + v for v in e['media']['verifiedFacts']], *['- 待确认：' + v for v in e['pending']], '', '[查看原始公告](' + e['sourceUrl'] + ')', '']
(reports / 'gakumas-2026-10-20.md').write_text('\n'.join(lines), encoding='utf-8')
audit = {'checkedAt': DATE, 'scope': '2026年10月20日官方公告深入调查', 'newProducts': len(newids), 'changedProducts': len(changed), 'eventRecords': len(events), 'primaryProductPagesRead': 108, 'productTotal': len(w['merch']), 'articleIndexPreserved': 285, 'originalWorksPreserved': 1427, 'newProductIds': newids, 'changedProductIds': sorted(changed), 'publication': 'pending'}
(RESEARCH / 'merge-report.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in audit.items() if k not in ['newProductIds', 'changedProductIds']}, ensure_ascii=False))
