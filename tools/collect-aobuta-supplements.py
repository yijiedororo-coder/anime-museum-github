"""Supplement observed official catalogs, plus the operator's own prize archive."""
import importlib.util, json, re
from pathlib import Path
spec = importlib.util.spec_from_file_location('makers',Path(__file__).with_name('collect-aobuta-makers.py'))
m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fetch, clean, add, parallel = m.fetch, m.clean, m.add, m.parallel

def dmm():
    queue={'https://onkure.dmm.com/media/ip/ip-710/'}; seen=set(); urls=set()
    while queue:
        batch=queue-seen;seen.update(batch);queue=set()
        for u,d in parallel(batch):
            if d is None:continue
            for a in d.xpath('//a[@href]'):
                v=a.get('href')
                if re.search(r'/media/prize/\d+/$',v) and '青春ブタ' in a.text_content():urls.add(v)
                if '/media/ip/ip-710/page/' in v and v not in seen:queue.add(v)
        if len(seen)>5:break
    for u,d in parallel(urls):
        if d is None:continue
        title=d.xpath('//h1'); tables=d.xpath('//table[contains(@class,"p-prize-summary__table")]')
        if not title or not tables:continue
        facts={}
        for row in tables[0].xpath('.//tr'):
            cells=row.xpath('./th|./td')
            if len(cells)==2:facts[clean(cells[0].text_content())]=clean(cells[1].text_content())
        maker=facts.get('発売元','')
        if maker not in ['フリュー','エルココ','セガ']:continue
        full_name=clean(title[0].text_content()); name=re.sub(r'^(?:【[^】]+】)+','',full_name)
        labels=[s for s in re.findall(r'【([^】]+)】',full_name) if re.match(r'^[A-Z][^a-z]',s)]
        if labels:name+=' / '+ '、'.join(labels)
        date=d.xpath('//dl[contains(@class,"p-prize-detail__date")]'); specs=['サイズ：'+facts['サイズ']] if facts.get('サイズ') else []
        channels=[{'name':'DMM 景品档案','url':u,'linkType':'运营商历史景品资料'}]
        # Only expose the exact operator prize links that actually occur in the article.
        links=d.xpath('//a[contains(@href,"onkure.dmm.com/prize/") or contains(@href,"dmm-onkure.onelink.me") and contains(.,"このプライズ")]/@href')
        for v in dict.fromkeys(links):channels.append({'name':'DMM 在线抓娃娃','url':v,'linkType':'运营商对应景品入口（可能跳转应用，非商品直购）'})
        brand=next((b for b in ['BiCute Bunnies','Trio-Try-iT','ぬーどるストッパー','Luminasta','ちょこのせ','ココぎゅっと','でふぉるむぷらす'] if b in name),maker+' 景品')
        add(u,name,{'フリュー':'FuRyu','エルココ':'elCOCO','セガ':'SEGA'}[maker],d.xpath('//meta[@property="og:image"]/@content'),clean(date[0].text_content()) if date else '',specs,brand=brand,prize=True,variant='、'.join(labels) if labels else '来源正式产品款式',channels=channels)
        m.PRODUCTS[-1]['originalName']=full_name
        m.PRODUCTS[-1]['sourceName']='DMM 在线抓娃娃 · 运营商历史景品档案'
        m.PRODUCTS[-1]['description']='运营商公开的历史投放档案，厂商、尺寸和日期按其记录保存。不同运营商的入荷时间可能不同。'
    print('DMM archive pages:',len(seen),'entries:',len(urls),flush=True)

def retail():
    for u,d in parallel(['https://taito-goods.jp/shop/g/g50101260/','https://taito-goods.jp/shop/g/g50101160/']):
        if d is None:continue
        facts={}
        for li in d.xpath('//ul[@class="block-dab-spec-list"]/li'):
            cells=li.xpath('./dl/dt|./dl/dd|./dt|./dd')
            if len(cells)>=2:facts[clean(cells[0].text_content())]=clean(cells[1].text_content())
        if not facts:
            for dt in d.xpath('//ul[@class="block-dab-spec-list"]//dt'):
                if dt.getnext() is not None:facts[clean(dt.text_content())]=clean(dt.getnext().text_content())
        name=facts.get('商品名','');specs=[k+'：'+v for k,v in facts.items() if k not in ['商品名','権利表記'] and v]
        add(u,name,'TAITO',d.xpath('//meta[@property="og:image"]/@content'),facts.get('発売月',''),specs,facts.get('価格',''),brand='spiritale',variant='白色旗袍版' if '白チャイナ' in name else '旗袍版',channels=[{'name':'TAITO GEAR & GOODS','url':u,'linkType':'制造商直营商品页（历史预约）'}])
    urls=['https://store.kadokawa.co.jp/shop/g/g'+i+'/' for i in ['302208004623','302208004624','302509001021','302509001023','302201009340']]
    for u,d in parallel(urls):
        if d is None:continue
        h=d.xpath('//h1[contains(@class,"block-goods-name")]');name=clean(h[0].text_content()) if h else '';dates=d.xpath('//dt[contains(text(),"発売日")]/following-sibling::dd[1]');price=d.xpath('//*[contains(@class,"js-enhanced-ecommerce-goods-price")]');facts=[]
        for x in d.xpath('//*[contains(@class,"block-goods-comment")]'):
            for node in x.xpath('.//script|.//style'):node.drop_tree()
            for br in x.xpath('.//br'):br.tail='\n'+(br.tail or '')
            for line in x.text_content().splitlines():
                line=clean(line)
                if line and line not in ['JANコード','■商品内容'] and len(line)<180 and any(k in line for k in ['■','サイズ','素材','材質','全高','特典','JAN','2体']):facts.append(line)
        add(u,name,'KADOKAWA',d.xpath('//meta[@property="og:image"]/@content'),clean(dates[0].text_content()) if dates else '',list(dict.fromkeys(facts)),clean(price[0].text_content()) if price else '',brand='KADOKAWA PLASTIC MODEL SERIES' if 'MODEL SERIES' in name else 'KDcolle',channels=[{'name':'KADOKAWA カドスト','url':u,'linkType':'官方商店商品页（预约 / 历史资料）'}])
        if 'MODEL SERIES' in name:m.PRODUCTS[-1]['category']='塑料模型'
    u='https://coco-store.jp/products/64';d=fetch(u);p=json.loads(d.xpath('//script[@id="ProductJson-product-template"]/text()')[0]);facts=[]
    for row in d.xpath('//table//tr'):
        cells=row.xpath('./th|./td')
        if len(cells)==2 and clean(cells[0].text_content()) not in ['商品名','コピーライト']:facts.append(clean(cells[0].text_content())+'：'+clean(cells[1].text_content()))
    reserve=d.xpath('//p[contains(text(),"予約期間")]|//p[contains(text(),"発送予定")]|//p[contains(text(),"個数制限")]');facts+=list(dict.fromkeys(clean(x.text_content()) for x in reserve))
    add(u,p['title'],'Design COCO',p['images'],'2026年8月顺次発送（来源计划）',facts,f'{p["price"]//100:,}日元（含税，来源记录）',brand='Design COCO',channels=[{'name':'COCOストア','url':u,'linkType':'制造商直营商品页（历史预约）'}])
    u='https://furyu-hm.com/products/tnl-viihrluv';d=fetch(u);facts=['全高：約310mm（含台座）','材质：ATBC-PVC、ABS','SKU：AMU-TNL0110','直营店特典：可替换眨眼表情零件','预约：2024-10-31 至 2025-01-07；来源历史预约记录','来源注明每人最多6个 / 完全受注生产'];add(u,'TENITOL TALL 桜島麻衣','FuRyu',d.xpath('//meta[@property="og:image"]/@content'),'2025年7月発送予定（来源计划）',facts,'10,450日元（含税，来源记录）',brand='TENITOL TALL',channels=[{'name':'FURYU HOBBY MALL','url':u,'linkType':'制造商直营商品页（历史预约）'}])
    for u,d in parallel(['https://www.cospa.com/nijigencospa/detail/id/00000092433','https://www.cospa.com/nijigencospa/detail/id/00000092872']):
        if d is None:continue
        name=clean(d.xpath('//head/title/text()')[0].split(' | ')[0]);og=d.xpath('//meta[@property="og:image"]/@content');text=clean(d.text_content());p=re.search(r'販売価格\s*(¥[\d,]+)[（(]税込',text);s=d.xpath('//div[@class="s_standard"]');facts=[clean(x.text_content()) for x in s];add(u,name,'COSPA',og,'来源产品页未标注初次发售日期',facts,p[1]+'（含税，来源记录）' if p else '',brand='二次元COSPA',channels=[{'name':'COSPA','url':u,'linkType':'制造商直营商品页（历史目录）'}]);m.PRODUCTS[-1]['size']=' / '.join(facts)

def saved_dom():
    for key,slug,release,brand in [('maid','prize_aobuta_mai_maid','2025年7月10日','elCOCO 1/7 景品'),('gem','prize_aobuta_mai','2025年1月（制作方记录）','elCOCO 1/7 景品'),('deform','deform_aobuta_mai','2024年5月30日','でふぉるむぷらす')]:
        x=json.loads((m.CACHE/f'coco-{key}-dom.json').read_text(encoding='utf-8'));text=x['text'].split('RELATED ITEMS')[0];facts=[clean(s) for s in text.splitlines() if s.startswith(('全高','原型','発売元','開発','※製品'))];links=[a['url'] for a in x['links'] if 'elcocoland.com/shop/g/' in a['url']];channels=[{'name':'Design COCO 制作档案','url':'https://www.dcoco.co.jp/products/'+slug,'linkType':'制作方产品资料'}]+[{'name':'elCOCO 产品档案','url':v,'linkType':'制造商景品资料（访问可能受限）'} for v in dict.fromkeys(links)]
        add('https://www.dcoco.co.jp/products/'+slug,x['title'],'elCOCO',[i for i in x['images'] if i.startswith('https://')],release,facts,brand=brand,prize=True,channels=channels)
    for x in json.loads((m.CACHE/'coco-extra-dom.json').read_text(encoding='utf-8')):
        text=x['text'];facts=[clean(s) for s in text.splitlines() if s.startswith(('サイズ','大きさ','原型','彩色','製造','販売元'))];p=re.search(r'価格：(.*)',text);channels=[{'name':'Design COCO 制作档案','url':x['url'],'linkType':'制作方产品资料'}]+[{'name':'SHIBUYA SCRAMBLE FIGURE','url':v,'linkType':'官方商品页（历史受注）'} for v in dict.fromkeys(a['url'] for a in x['links'] if 'shibuya-scramble-figure.com/scale-figure/items' in a['url'])]
        add(x['url'],x['title'],'eStream',[i for i in x['images'] if i.startswith('https://')],'制作年份：2021；本来源未注明发货日期',facts,p[1] if p else '',brand='SHIBUYA SCRAMBLE FIGURE',channels=channels)
    x=json.loads((m.CACHE/'kotobukiya-dom.json').read_text(encoding='utf-8'));facts=[clean(s) for s in x['tables']];u='https://www.kotobukiya.co.jp/product/detail/p4934054006106/'
    shop=json.loads((m.CACHE/'kotobukiya-shop-dom.json').read_text(encoding='utf-8'))
    add(u,'桜島麻衣 1/8（寿屋 / KOTOBUKIYA）','KOTOBUKIYA',shop['images'],'2019年4月11日（直营店记录；厂商目录标注2019年4月）',['スケール：1/8','全高：約200mm（含台座）','材质：PVC（非邻苯二甲酸）、ABS','原型：白髭創','品番：PP785',shop['note'],'商品图采用寿屋直营店公开图集'],'12,100日元（含税，来源记录）',brand='KOTOBUKIYA',channels=[{'name':'KOTOBUKIYA','url':u,'linkType':'制造商产品资料'},{'name':'寿屋直营店','url':x['shop'][0],'linkType':'官方商店商品页（历史）'}])

if __name__=='__main__':
    dmm();retail();saved_dom()
    (m.CACHE/'maker-supplements.json').write_text(json.dumps({'checkedAt':m.DATE,'products':m.PRODUCTS,'failures':m.FAILURES},ensure_ascii=False,indent=2),encoding='utf-8')
    from collections import Counter
    print(json.dumps({'count':len(m.PRODUCTS),'makers':dict(Counter(g['manufacturer'] for g in m.PRODUCTS)),'failures':m.FAILURES},ensure_ascii=False))
