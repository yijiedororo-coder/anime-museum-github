import json,csv,re,hashlib,urllib.request,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin,urlparse
from lxml import html
root=Path(__file__).resolve().parent.parent;cache=root/'tools/aobuta-research';date='2026-10-13'
def get(u):
 p=cache/(hashlib.sha256(u.encode()).hexdigest()+'.html')
 if not p.exists():p.write_text(urllib.request.urlopen(u,timeout=35).read().decode('utf-8'),encoding='utf-8')
 return html.fromstring(p.read_text(encoding='utf-8'))
def clean(s):return re.sub(r'\s+',' ',s).strip()
def category(n):
 for keys,val in [(['ぬい','ちびぐるみ'],'娃娃 / 毛绒'),(['フィギュア','ねんどろいど','POP UP PARADE'],'手办'),(['アクリルスタンド','アクリルフィギュア'],'立牌'),(['バッジ'],'徽章'),(['キーホルダー','チャーム','ストラップ'],'挂件'),(['シャツ','パーカー','衣装'],'服饰'),(['タペストリー','ポスター','グラフ','アクリルブロック'],'海报 / 摆件'),(['パンフレット','イラストブック','書籍'],'书籍 / 场刊'),(['CD','Blu-ray','DVD'],'音乐 / 影像'),(['ファイル','ノート','ペン','日記','カード','色紙'],'卡片 / 文具')]:
  if any(k in n for k in keys):return val
 return '生活 / 收藏'
names=['桜島麻衣','古賀朋絵','双葉理央','豊浜のどか','梓川かえで','梓川花楓','牧之原翔子','美東美織','岩見沢寧々','赤城郁実','姫路紗良','広川卯月','梓川咲太']
goods=[];stats={};failures=[]
def add(u,n,box,series,origin):
 title=clean(n);text=clean(box.text_content());imgs=box.xpath('.//img/@data-src|.//img/@src');imgs=[urljoin(u,x) for x in imgs if x and not any(k in x for k in ['btn_play','icon','logo'])];priceNodes=box.xpath('.//*[contains(@class,"price")]');price=clean(priceNodes[0].text_content()) if priceNodes else ''
 if not price:
  m=re.search(r'(?:各)?[¥￥]\s*[\d,]+(?:\s*[(（][^）)]*[）)])?|(?:各)?[\d,]+円(?:[+＋]税)?',text);price=m.group() if m else '来源未标价'
 facts=[]
 for el in box.xpath('.//br'):el.tail='\n'+(el.tail or '')
 for line in box.text_content().splitlines():
  line=clean(line)
  if line and len(line)<230 and any(k in line for k in ['サイズ','材質','素材','スケール','全高','発売日','発売元','販売価格','会計','購入制限','受注','予約期間']):facts.append(line)
 dims=' / '.join(f for f in facts if any(k in f for k in ['サイズ','全高','スケール']))
 release=next((f for f in facts if '発売日' in f),'来源未标注商品发售日期')
 channel=[]
 for a in box.xpath('.//a[@href]'):
  v=urljoin(u,a.get('href'));h=urlparse(v).netloc
  if not v.startswith(('http://','https://')) or h in ['ao-buta.com','tenji.ao-buta.com'] or any(k in h for k in ['youtube','youtu.be','twitter','x.com']):continue
  v=v.replace('http://','https://',1);label=clean(a.text_content()) or h
  if not any(c['url']==v for c in channel):channel.append({'name':h,'url':v,'linkType':'来源销售链接（商品页或系列入口，请核对）','sourceNote':label[:100]})
 channel.insert(0,{'name':'动画官方 / 青ブタ展','url':u,'linkType':'官方商品资料（非实时库存）'})
 g={'id':'aobuta-goods-'+hashlib.sha256((u+'|'+title).encode()).hexdigest()[:16],'name':title,'kind':'merch','category':category(title),'originalType':series,'series':series,'characters':'、'.join(n for n in names if n in title) or '系列商品 / 角色见官方图片','price':price,'releaseDate':release,'size':dims,'description':'官方公开商品档案；'+('属于历史目录，价格和发售安排保留为当时记录。' if origin!='2026剧场版' else '2026剧场版公开目录，是否销售及限购以影院公告为准。')+' 角色款数与随机销售方式按原商品名保留。','specifications':list(dict.fromkeys(facts)),'image':imgs[0] if imgs else 'assets/aobuta-autumn-poster.png','images':list(dict.fromkeys(imgs)),'sourceUrl':u,'sourceName':origin+' · 官方公开目录','checkedAt':date,'channels':channel,'availability':'官方资料页仍可查询，不代表商店有货；历史商品可能已结束销售，预约、库存、税费与渠道请再次核对。'}
 if any(x['id']==g['id'] for x in goods):return
 goods.append(g);stats[origin]=stats.get(origin,0)+1
sources=[('https://ao-buta.com/yumemiru/m_goods/','怀梦美少女（2019剧场版）','2019剧场版'),('https://ao-buta.com/odekake/goods_odekake/','娇怜外出妹（2023剧场版）','2023外出妹剧场版'),('https://ao-buta.com/knapsack/goods/','红书包女孩（2023剧场版）','2023书包剧场版'),('https://ao-buta.com/dearfriend/goods/','Dear Friend（2026剧场版）','2026剧场版')]
for u,series,origin in sources:
 d=get(u);titles=d.xpath('//p[@class="name"]|//p[@class="ttl"]|//h3[contains(@class,"title")]')
 for h in titles:
  par=h.getparent()
  while par is not None and not par.xpath('.//img'):par=par.getparent()
  if par is not None:add(u,h.text_content(),par,series,origin)
u='https://tenji.ao-buta.com/goods/';d=get(u)
for box in d.xpath('//li[contains(@class,"p-goods-list__item")]'):
 n=box.xpath('.//p[contains(@class,"p-goods-name")]')
 if n:add(u,n[0].text_content(),box,'青ブタ展 / 系列展览','青ブタ展')
for u in ['https://ao-buta.com/tv/goods/','https://ao-buta.com/tv/goods/?p=2','https://ao-buta.com/tv/goods/?p=3']:
 d=get(u)
 for a in d.xpath('//ul[contains(@class,"goods_list")]//a'):
  detail=urljoin(u,a.get('href'));b=get(detail).xpath('//div[@class="goods_detail"]')
  if b:add(detail,b[0].xpath('.//h3')[0].text_content(),b[0],'早期TV / 2019剧场商品目录','早期官方商品目录')
manufacturer=[('https://www.goodsmile.info/ja/product/13882/','POP UP PARADE 桜島麻衣','手办','4,800円（税込）','2023年6月','全高约205mm / 无比例','Good Smile Company'),('https://www.goodsmile.info/ja/product/8126/','ねんどろいどぷらす アクリルスタンド（12角色图案款）','立牌','','','','Good Smile Company'),('https://www.taito.co.jp/en/taito-prize/0452106100','Coreful 桜島麻衣 ～バニーver.～','手办','景品 / 无零售定价','来源日期需核对','','TAITO')]
for u,n,cat,price,release,size,brand in manufacturer:
 d=get(u);og=d.xpath('//meta[@property="og:image"]/@content');add(u,n,d,'系列商品',brand);g=goods[-1];g['category']=cat;g['characters']='桜島麻衣' if cat=='手办' else '桜島麻衣、古賀朋絵、双葉理央、豊浜のどか、梓川かえで、牧之原翔子';g['image']=og[0].replace('http://','https://',1) if og else g['image'];g['images']=[g['image']];g['price']=price or g['price'];g['releaseDate']=release or g['releaseDate'];g['size']=size or g['size'];g['description']='制造商公开产品档案；参数按官方记录，历史报价不代表实时成交价。';g['specifications']=[g['size']] if g['size'] else [];g['channels']=[{'name':brand,'url':u,'linkType':'制造商产品资料'}]
for u,series,origin in [('https://event.amnibus.com/aobuta-tower-2026/','系列 / 2026吉他演奏联名','AMNIBUS 2026'),('https://event.amnibus.com/aobuta-0101-2023/','娇怜外出妹 / 浴衣联名','AMNIBUS 2023浴衣'),('https://store.amnibus.com/aobuta-magnetbyshibuya109-2023/','TV兔女郎篇 / 万圣节联名','AMNIBUS 2023万圣节'),('https://event.amnibus.com/aobuta-animate/','TV兔女郎篇 / 冬服联名','AMNIBUS 2019冬服')]:
 d=get(u)
 for box in d.xpath('//li[./dl/dt and .//img]'):
  n=box.xpath('./dl/dt')[0].text_content();add(u+'#'+(box.get('id') or hashlib.sha256(n.encode()).hexdigest()[:8]),n,box,series,origin);g=goods[-1];quotes=[clean(x.text_content()) for x in box.xpath('./dl/dd') if re.search(r'[0-9,]+円',x.text_content())];g['price']=' / '.join(quotes) or g['price'];g['specifications']=list(dict.fromkeys(g['specifications']+[clean(x.text_content()) for x in box.xpath('./dl/dd/small')]));g['channels']=[{'name':'AMNIBUS / 联名官方','url':u,'linkType':'联名官方商品目录（历史）'}]
for u,n,cat,price,release,size in [('https://www.goodsmile.com/ja/product/34665/','ねんどろいど 桜島麻衣 バニーガールVer.（No.2417）','手办','6,500日元（来源历史价格）','2024年8月','全高约100mm / 无比例可动'),('https://www.taito.co.jp/taito-prize/0000003791','原创毛绒 / オリジナルぬいぐるみ（怀梦美少女）','娃娃 / 毛绒','景品 / 无零售定价','来源未标注完整日期','')]:
 d=get(u);add(u,n,d,'系列商品','制造商补充');g=goods[-1];og=d.xpath('//meta[@property="og:image"]/@content');g.update(category=cat,price=price,releaseDate=release,size=size,image=og[0].replace('http://','https://',1) if og else g['image'],specifications=[size] if size else [],description='制造商官方产品档案；含历史产品，价格及发售记录不代表现在有货。',channels=[{'name':'Good Smile Company' if 'goodsmile' in u else 'TAITO','url':u,'linkType':'制造商产品资料'}])
Path(root/'data/aobuta-goods.json').write_text(json.dumps({'checkedAt':date,'products':goods,'sourceCounts':stats,'failures':failures},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'goods':len(goods),'sourceCounts':stats,'sample':[{'name':g['name'],'image':g['image'],'price':g['price'],'spec':g['specifications'][:2]} for g in goods[:3]]},ensure_ascii=False))
