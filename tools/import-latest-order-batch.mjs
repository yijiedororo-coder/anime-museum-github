// Append the 2026-11-06 public-source batch for the first five works in 最新 order.
// Does not rewrite 海贼王 / 学园默示录, work order, or the first-round progress date.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import assert from 'node:assert/strict';
import vm from 'node:vm';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const checkedAt='2026-11-06';
const batch='2026-11-06-latest-order-5';
const doc='官方资料页 / 目录（非购买确认）';
const shop='官方目录列出的商品页（目标库存未核查）';
const event='零售活动公告（非实时库存）';
const availability='历史及已公告商品资料，不表示当前有货。原价、投放与发售日期保留为来源记录。未核查实时库存。';
const description='按公开页面登记的商品或系列档案。一条多款系列不拆成未列明的单品。价格、日期和尺寸只保留来源原文。';
const idFor=(key,name)=>'latest-'+createHash('sha256').update(key+'|'+name).digest('hex').slice(0,18);
const src=(url,checkedAtJST,sha256,bytes)=>({url,checkedAtJST,sha256,bytes});

const sources={
  ojikawaHome:src('https://ojikawa.com/','2026-11-06T13:57:06.007751+09:00','1122628bb4a56c7f2b2acfde66a307ef001c3872e3c4830277b5d24c80a092c6',79355),
  ojikawaOnair:src('https://ojikawa.com/onair/','2026-11-06T13:58:14.627935+09:00','00b12c730708ed8fad3923f068545a334de3de915070b0a9ef7e54ac9333b720',27217),
  ytvGoods:src('https://www.ytv.co.jp/ojikawa/goods/','2026-11-06T13:57:06.549514+09:00','574ec19a30025d4e382f51a01a96b780fa05624206c0eb88cb5b8025ee45ec57',6561),
  tsutaya:src('https://shibuyatsutaya.tsite.jp/article/2844.html','2026-11-06T13:57:07.697764+09:00','f81323561b92bd2eb47746799d534cbefe640dd76a9d57e71cd40648f63ac49b',91682),
  fod:src('https://news.fod.fujitv.co.jp/article/14476','2026-11-06T13:57:08.832967+09:00','9bc88fda0698f545c953a0de339adcec99ca896f34080ac6b21bac9c04ced380',74504),
  yowakiHome:src('https://yowaki-max-anime.com/','2026-11-06T13:57:08.918563+09:00','4f25261d378eacbd42ccbc555a56ef0c5ac86bfb85c032a7cf0f301c96c14b54',36485),
  yowakiOnair:src('https://yowaki-max-anime.com/onair/','2026-11-06T13:57:09.524110+09:00','c0ae4be93f329714a43ea472c0721414ae789523cad0fa7b3552fa1c58b56c16',21955),
  yowakiBd:src('https://yowaki-max-anime.com/bddvd/','2026-11-06T13:57:10.217016+09:00','9e957fa282a17a5056c38bfc99b19d857f4636c030f252d31016d01fd0348b6a',29150),
  yowakiMusic:src('https://yowaki-max-anime.com/music/','2026-11-06T13:58:13.731520+09:00','843ebc3039cfffda79dc5971b030a3a722856fce49c72e53768348f19f6a48ef',18432),
  kadoBd1:src('https://store.kadokawa.co.jp/shop/g/g302607005930/','2026-11-06T13:57:11.228429+09:00','b5d1a69f01312ae237c98d4713f6b5d9660ba9f571753da4caf02a628cd87574',149624),
  kadoAcrylic:src('https://store.kadokawa.co.jp/shop/g/g302608002673/','2026-11-06T13:57:12.202071+09:00','5c79c54a1a4d11d66f286227a6d67bc5b16f0dba9bc32c6b74c603a0c4cb41a5',129746),
  kadoList:src('https://store.kadokawa.co.jp/shop/e/ekanm0140/','2026-11-06T13:58:15.278950+09:00','ad626e7fb61c353ccf4c94c6835e052ed6262f998b40e6a0053cb8b1eba997b5',130322),
  namaHome:src('https://nama-anaru.com/','2026-11-06T13:57:13.006833+09:00','6bfe7a2cfae87968065d2efafd187b915476928099b062cef0f510c358b15cdc',68684),
  namaOnair:src('https://nama-anaru.com/onair/','2026-11-06T13:58:11.328296+09:00','f5056bec0e476ebeee90216e12c7930d0c46b90e817a330a86e33df72edc16ad',51261),
  namaBd:src('https://nama-anaru.com/bddvd/','2026-11-06T13:58:10.505888+09:00','c8143a1d53d0230156556dd3d72d01726fb9d3516a828fd29e0da0339eca12d7',24219),
  namaBd2:src('https://nama-anaru.com/bddvd/?pk=02','2026-11-06T13:58:28.323708+09:00','9495ce072d5695e06274c62e6a11bc0c1e37b353941a0c6eb6e35641d7042c0d',22765),
  namaBd3:src('https://nama-anaru.com/bddvd/?pk=03','2026-11-06T13:58:28.987636+09:00','34110e0f1f7f73e601013b70103eb2e31cdfe62cbbefeb654d0e384e7b34a219',22233),
  namaBd4:src('https://nama-anaru.com/bddvd/?pk=04','2026-11-06T13:58:29.636895+09:00','0bdd4879b3c89565cae57c99cf74fb82ed7820ea44f2998e3b6e462f0df8befe',22282),
  namaBd5:src('https://nama-anaru.com/bddvd/?pk=05','2026-11-06T13:58:29.869035+09:00','1aaf03e67120dc3fda5d89cd9ba20fcf7ff9661183cfa3f560b00828a4b2e683',21592),
  namaBd6:src('https://nama-anaru.com/bddvd/?pk=06','2026-11-06T13:58:30.088313+09:00','6b651fa7cfa216f06be8cb256f16efc4f6d9b97a4656da696b50f71c7c627c05',21494),
  aniplexNews:src('https://news.aniplex.co.jp/detail.html?id=71254','2026-11-06T13:57:13.743167+09:00','884d322732947917bbc4550940f02d4f7496225c0c35c990e1c460d5e210b227',26011),
  medicos:src('https://www.medicos-e.net/newsdetail/seitokai/','2026-11-06T13:57:24.413125+09:00','8e894b3bb77400c8970a5c5f7597d6af5516f921f7f672e27baa648eaabdfadf',38967),
  hakoHome:src('https://aonohako-anime.com/','2026-11-06T13:57:15.144060+09:00','680dadc548398180ca8212ff11eccae51840b3d7de6dd44eb334c5a0091f7e04',74385),
  hako1:src('https://aonohako-anime.com/bddvd/s2-vol1.html','2026-11-06T13:57:15.868739+09:00','8e34d7393fa5f65b63d297a456f9a2998adf138964d0cdb7f09064fcd36071c8',6418),
  hako2:src('https://aonohako-anime.com/bddvd/s2-vol2.html','2026-11-06T13:57:16.582236+09:00','2a39a274bb1179240387da52c02ddbe92e821be63ae1489164c06cb08f767dbc',6061),
  hako3:src('https://aonohako-anime.com/bddvd/s2-vol3.html','2026-11-06T13:57:17.159622+09:00','825fd4718056e9612edfcebae142cda53bfb9d3ebca1c8522c5c6b372c95abe6',6064),
  hakoBonus:src('https://aonohako-anime.com/bddvd/s2-tokuten.html','2026-11-06T13:57:17.746076+09:00','fb45a1a2c1d43ada371ec62d463835707d29e6b43a6872b9113acdc08731035f',11795),
  tmsList:src('https://www.tmsshop.jp/dp/aonohako_season2/','2026-11-06T13:57:18.664313+09:00','fe11ceee1feb22f5db67ad52ddd13338fe90381f06ae817e5dd8cd3ab4b8d946',17565),
  tmsFile:src('https://www.tmsshop.jp/fs/tmsshop/aonohako_0097','2026-11-06T13:58:12.182634+09:00','9d7c28d5b367bc9826af099f7afc5763f419349707b05703956000f46e0c2b82',32364),
  tmsStand:src('https://www.tmsshop.jp/fs/tmsshop/aonohako_0098','2026-11-06T13:58:13.139725+09:00','0b17bef031132f8934835d196452ab0551eb0b3b2496928e46b3f1194f9595c6',32139),
  tmsEvent:src('https://www.tms-e.co.jp/release/event/entry-26246.html','2026-11-06T13:57:19.760218+09:00','5233f6d3f8a41272be6bb813b40e7bbc8398389f061c11500014e95124618a20',50834),
  aoashiHome:src('https://aoashi-pr.com/','2026-11-06T13:57:20.893382+09:00','9edb83789109de949bac475b3ca7e9dcbd373b50e3c469e49f33098a66bedc20',90716),
  bridge:src('https://prtimes.jp/main/html/rd/p/000000054.000157042.html','2026-11-06T13:57:21.217679+09:00','5608162692ea2a836bafec1b335ab4e00baaecf6f16d9eb56fd642b5c47eff1d',266932),
  tomo:src('https://tomostore-online.com/shops/aoashi','2026-11-06T13:57:23.036195+09:00','e199e77481df99e9e29f78661ab9f819fd08178efcac3c4c3536565eaa7747fc',550164),
};

function item(key,fields){
  const channels=fields.channels.map(pair=>{
    const [name,url,linkType]=pair;
    assert(url.startsWith('https://'),url);
    return {name,url,linkType};
  });
  return {
    id:idFor(key,fields.name),name:fields.name,kind:'merch',category:fields.category,
    originalType:fields.productBrand,series:fields.productBrand,characters:fields.characters,
    manufacturer:fields.manufacturer,productBrand:fields.productBrand,acquisitionType:fields.acquisitionType,
    price:fields.price,releaseDate:fields.releaseDate,size:fields.size||'来源目录未标尺寸；请核对商品详情',
    description:fields.description||description,specifications:fields.specifications||[],
    image:fields.image||'',images:fields.images||[],sourceUrl:fields.sourceUrl,sourceName:fields.sourceName,
    checkedAt,channels,addedInBatch:batch,availability,imagePlaceholder:Boolean(fields.imagePlaceholder),
  };
}

const tsutayaUrl=sources.tsutaya.url;
const ojikawaGoods=[
  ['トレーディングミニアクリルブロック 全5種','立牌','880円（税込）','会期 2026年10月30日（金）～11月15日（日）','来源目录未标尺寸；请核对商品详情',['SHIBUYA TSUTAYA先行销售','全5种，页面未拆出单款名称']],
  ['ダイカットアクリルキーホルダー 全5種','挂件','880円（税込）','会期 2026年10月30日（金）～11月15日（日）','来源目录未标尺寸；请核对商品详情',['全5种，页面未拆出单款名称']],
  ['クリアファイル 全2種','卡片 / 文具','660円（税込）','会期 2026年10月30日（金）～11月15日（日）','来源目录未标尺寸；请核对商品详情',['全2種，页面未拆出单款名称']],
  ['おでかけぬいぐるみポシェット','生活 / 收藏','3,300円（税込）','会期 2026年10月30日（金）～11月15日（日）；11月上旬入荷予定','来源目录未标尺寸；请核对商品详情',['页面写11月上旬入荷予定']],
  ['パグ太郎ぬいぐるみ','娃娃 / 毛绒','4,950円（税込）','会期 2026年10月30日（金）～11月15日（日）','来源目录未标尺寸；请核对商品详情',[]],
  ['パグ太郎 もっちりマスコット','娃娃 / 毛绒','1,540円（税込）','会期 2026年10月30日（金）～11月15日（日）','来源目录未标尺寸；请核对商品详情',[]],
].map(([name,category,price,releaseDate,size,specifications])=>item('ojikawa',{
  name,category,manufacturer:'来源页未标注厂商',productBrand:'SHIBUYA TSUTAYA POP UP SHOP',acquisitionType:'零售周边',
  price,releaseDate,size,specifications,characters:name.includes('パグ太郎')?'パグ太郎':'パグ太郎＆フレンズ / 见官方配图',
  sourceUrl:tsutayaUrl,sourceName:'SHIBUYA TSUTAYA · 公开活动页',
  channels:[['SHIBUYA TSUTAYA 活动页',tsutayaUrl,event],['TV动画官网',sources.ojikawaHome.url,doc]],
}));

const yowakiVolumes=[
  [1,'2027年1月27日(水)','第1话～第4话','ZMXZ-20004','ZMBZ-20001','https://store.kadokawa.co.jp/shop/g/g302607005930/','https://store.kadokawa.co.jp/shop/g/g302607005933/'],
  [2,'2027年2月26日(金)','第5话～第8话','ZMXZ-20005','ZMBZ-20002','https://store.kadokawa.co.jp/shop/g/g302607005931/','https://store.kadokawa.co.jp/shop/g/g302607005934/'],
  [3,'2027年3月26日(金)','第9话～第12话','ZMXZ-20006','ZMBZ-20003','https://store.kadokawa.co.jp/shop/g/g302607005932/','https://store.kadokawa.co.jp/shop/g/g302607005935/'],
];
const yowakiGoods=[];
for(const [volume,date,episodes,bdCode,dvdCode,bdUrl,dvdUrl] of yowakiVolumes){
  const base=`弱気MAX令嬢なのに、辣腕婚約者様の賭けに乗ってしまった 第${volume}巻`;
  for(const [format,code,price,url] of [['Blu-ray',bdCode,'14,300円（税込）',bdUrl],['DVD',dvdCode,'12,100円（税込）',dvdUrl]]){
    yowakiGoods.push(item('yowaki',{
      name:`${base} ${format}`,category:'音乐 / 影像',manufacturer:'KADOKAWA',productBrand:'TV动画卷装影像',acquisitionType:'零售周边',
      price,releaseDate:`${date}発売`,characters:'ピア・ロックウェル / ルーファス・スタン',
      specifications:[`品番：${code}`,`収録：${episodes}`,'初回生产特典：特制外盒、动画绘制デジパック、特制小册子'],
      sourceUrl:sources.yowakiBd.url,sourceName:'TV动画官网 · Blu-ray＆DVD',
      channels:[['TV动画官网 Blu-ray＆DVD',sources.yowakiBd.url,doc],['KADOKAWA官方商店',url,shop],['KADOKAWA映像商品目录',sources.kadoList.url,doc]],
    }));
  }
}
yowakiGoods.push(item('yowaki',{
  name:'ビーズログ文庫創刊20周年フェア アクリルフィギュア 『弱気MAX令嬢なのに、辣腕婚約者様の賭けに乗ってしまった』ピア',
  category:'立牌',manufacturer:'KADOKAWA',productBrand:'ビーズログ文庫',acquisitionType:'零售 / 受注商品',
  price:'1,870円（价格节点未写税込）',releaseDate:'2027年2月発売予定',size:'プレート状態：約 縦150×横100mm',
  characters:'ピア・ロックウェル',specifications:['素材：アクリル树脂','生产国：日本','预约至2026年11月17日(火) 23:59','product:price:amount 为 1870 JPY'],
  description:description+' 价格按页面可见文字保留为1,870円；该价格节点没有写出税込。',
  sourceUrl:sources.kadoAcrylic.url,sourceName:'KADOKAWA官方商店',
  channels:[['KADOKAWA官方商店',sources.kadoAcrylic.url,shop]],
}));
yowakiGoods.push(item('yowaki',{
  name:'鈴木このみ「強気MAX宣言」オープニングテーマ（配信）',category:'音乐 / 影像',manufacturer:'官方音乐页未标注厂商',productBrand:'TV动画主题歌',acquisitionType:'配信',
  price:'来源未标注实体价格',releaseDate:'2026年10月5日（月）0:00より各种音乐服务配信',characters:'系列商品 / 角色见官方配图',
  specifications:['作词：烏屋茶房','作曲：金崎真士','编曲：鎌田瑞輝'],
  sourceUrl:sources.yowakiMusic.url,sourceName:'TV动画官网 · MUSIC',
  channels:[['TV动画官网 MUSIC',sources.yowakiMusic.url,doc]],
}));
yowakiGoods.push(item('yowaki',{
  name:'伊藤美来 5th Album「39rpm」限定盤（CD+エムカード）',category:'音乐 / 影像',manufacturer:'官方音乐页未标注厂商',productBrand:'TV动画主题歌所收录专辑',acquisitionType:'零售周边',
  price:'￥6,050（税込）',releaseDate:'2026年10月7日（水）発売',characters:'ピア・ロックウェル',
  specifications:['收录ED「夜明けまでに」','全11曲','页面未标注品番与唱片公司'],
  sourceUrl:sources.yowakiMusic.url,sourceName:'TV动画官网 · MUSIC',
  channels:[['TV动画官网 MUSIC',sources.yowakiMusic.url,doc]],
}),item('yowaki',{
  name:'伊藤美来 5th Album「39rpm」通常盤（CD）',category:'音乐 / 影像',manufacturer:'官方音乐页未标注厂商',productBrand:'TV动画主题歌所收录专辑',acquisitionType:'零售周边',
  price:'￥4,400（税込）',releaseDate:'2026年10月7日（水）発売',characters:'ピア・ロックウェル',
  specifications:['收录ED「夜明けまでに」','全11曲','页面未标注品番与唱片公司'],
  sourceUrl:sources.yowakiMusic.url,sourceName:'TV动画官网 · MUSIC',
  channels:[['TV动画官网 MUSIC',sources.yowakiMusic.url,doc]],
}));

const namaVolumes=[
  [1,'2026年12月23日(水)','第1话～第2话（2话）','古都吹寿子','ANZX-18531〜18533','ANZX-18534〜18535','ANZB-18534〜18535',sources.namaBd.url,'页面写【10月18日(日)まで】，未写年份'],
  [2,'2027年1月27日(水)','第3话～第4话（2话）','陸奥こまろ','ANZX-18536〜18538','ANZX-18539〜18540','ANZB-18539〜18540',sources.namaBd2.url,'2026年11月8日(日)'],
  [3,'2027年2月24日(水)','第5话～第6话（2话）','尾鳥たん','ANZX-18541〜18543','ANZX-18544〜18545','ANZB-18544〜18545',sources.namaBd3.url,'2026年12月6日(日)'],
  [4,'2027年3月31日(水)','第7话～第8话（2话）','照井有栖','ANZX-18546〜18548','ANZX-18549〜18550','ANZB-18549〜18550',sources.namaBd4.url,'2026年12月20日(日)'],
  [5,'2027年4月28日(水)','第9话～第10话（2话）','平塚敏深','ANZX-18551〜18553','ANZX-18554〜18555','ANZB-18554〜18555',sources.namaBd5.url,'2027年1月24日(日)'],
  [6,'2027年6月30日(水)','第11话～第12话（2话）','页面原文「？？？」','ANZX-18556〜18558','ANZX-18559〜18560','ANZB-18559〜18560',sources.namaBd6.url,'2027年4月18日(日)'],
];
const namaGoods=[];
for(const [volume,date,episodes,character,specialCode,bdCode,dvdCode,url,reserve] of namaVolumes){
  const shared=['2枚组（BD/DVD＋CD）','收录TV放送版与规制解除版',`収録：${episodes}`];
  namaGoods.push(item('nama',{
    name:`生徒会にも穴はある！ ${volume} 抱き枕カバー付き特装版 Blu-ray`,category:'音乐 / 影像',manufacturer:'アニプレックス',productBrand:'TV动画卷装影像',acquisitionType:'零售周边',
    price:'￥20,900（税込）',releaseDate:`${date}発売`,size:'抱き枕カバー 約H1,600mm×W500mm',characters:character,
    specifications:[`品番：${specialCode}`,...shared,`抱き枕カバー：${character}`,'生地：2wayトリコット',`页面建议预约期限：${reserve}`],
    sourceUrl:url,sourceName:'TV动画官网 · Blu-ray＆DVD',
    channels:volume===1?[['TV动画官网 Blu-ray＆DVD',url,doc],['ANIPLEX NEWS BOX',sources.aniplexNews.url,doc]]:[['TV动画官网 Blu-ray＆DVD',url,doc]],
  }));
  namaGoods.push(item('nama',{
    name:`生徒会にも穴はある！ ${volume} 完全生産限定版 Blu-ray`,category:'音乐 / 影像',manufacturer:'アニプレックス',productBrand:'TV动画卷装影像',acquisitionType:'零售周边',
    price:'￥7,700（税込）',releaseDate:`${date}発売`,characters:'系列商品 / 角色见官方配图',
    specifications:[`品番：${bdCode}`,...shared],
    sourceUrl:url,sourceName:'TV动画官网 · Blu-ray＆DVD',
    channels:[['TV动画官网 Blu-ray＆DVD',url,doc]],
  }));
  namaGoods.push(item('nama',{
    name:`生徒会にも穴はある！ ${volume} 完全生産限定版 DVD`,category:'音乐 / 影像',manufacturer:'アニプレックス',productBrand:'TV动画卷装影像',acquisitionType:'零售周边',
    price:'￥6,600（税込）',releaseDate:`${date}発売`,characters:'系列商品 / 角色见官方配图',
    specifications:[`品番：${dvdCode}`,...shared],
    sourceUrl:url,sourceName:'TV动画官网 · Blu-ray＆DVD',
    channels:[['TV动画官网 Blu-ray＆DVD',url,doc]],
  }));
}

const hakoVolumes=[
  [1,'2027年1月20日（水）','TBR37019D','4988104188199','约94分（#1～4）＋映像特典',sources.hako1.url,['音频特典：第29话（2期第4话）「好きは最強の感情」','出演：上田麗奈（鹿野千夏役）、青山吉能（木戸夢佳役）','映像特典含无字幕OP/ED、PV集、ワールドプレミア映像']],
  [2,'2027年2月17日（水）','TBR37020D','4988104188205','约94分（#5～8）',sources.hako2.url,['音频特典：キャストオーディオコメンタリー']],
  [3,'2027年3月17日（水）','TBR37021D','4988104188212','约94分（#9～12）',sources.hako3.url,['音频特典：キャストオーディオコメンタリー']],
];
const hakoGoods=hakoVolumes.map(([volume,date,code,pos,runtime,url,extra])=>item('hako',{
  name:`TVアニメ「アオのハコ」Season2 Blu-ray Vol.${volume} 初回生産限定版`,category:'音乐 / 影像',manufacturer:'官方商品页未标注发行公司',productBrand:'TV动画 Season2 Blu-ray',acquisitionType:'零售周边',
  price:'11,000円（税抜价格 10,000円）',releaseDate:`${date}発売`,characters:'猪股大喜 / 鹿野千夏',
  specifications:[`品番：${code}`,`POS：${pos}`,'2层（BD50G）／1080p／线性PCM 2.0ch','字幕：无障碍日语字幕',runtime,'DISC 1枚',...extra],
  sourceUrl:url,sourceName:'TV动画官网 · Season2 Blu-ray',
  channels:[['TV动画官网 Season2 Blu-ray',url,doc],['Season2法人特典说明',sources.hakoBonus.url,doc]],
}));
hakoGoods.push(item('hako',{
  name:'Season2ティザービジュアル クリアファイル＆ブロマイドセット',category:'卡片 / 文具',manufacturer:'トムス・エンタテインメント',productBrand:'トムスショップ',acquisitionType:'零售周边',
  price:'990円（税込）',releaseDate:'销售期间 2026年9月11日(金)12:00～',size:'クリアファイル A4／ブロマイド L版',characters:'系列商品 / 角色见官方配图',
  specifications:['素材：クリアファイル PP／ブロマイド 纸','原产国：日本','数量限定；页面写明库存显示不是实时'],
  image:'https://tmsshop.fs-storage.jp/fs2cabinet/aon/aonohako_0097/aonohako_0097-s-01-pl.jpg',
  images:['https://tmsshop.fs-storage.jp/fs2cabinet/aon/aonohako_0097/aonohako_0097-s-01-pl.jpg'],imagePlaceholder:false,
  sourceUrl:sources.tmsFile.url,sourceName:'トムスショップ',
  channels:[['トムスショップ商品页',sources.tmsFile.url,shop],['トムスショップ Season2特设',sources.tmsList.url,doc]],
}),item('hako',{
  name:'Season2ティザービジュアル ショーウィンドウ風アクリルスタンド',category:'立牌',manufacturer:'トムス・エンタテインメント',productBrand:'トムスショップ',acquisitionType:'零售周边',
  price:'2,200円（税込）',releaseDate:'销售期间 2026年9月11日(金)12:00～',size:'约W123×H210×D3mm',characters:'系列商品 / 角色见官方配图',
  specifications:['素材：亚克力','原产国：日本','实用新案登录第3251950号','数量限定；页面写明库存显示不是实时'],
  image:'https://tmsshop.fs-storage.jp/fs2cabinet/aon/aonohako_0098/aonohako_0098-s-01-pl.jpg',
  images:['https://tmsshop.fs-storage.jp/fs2cabinet/aon/aonohako_0098/aonohako_0098-s-01-pl.jpg'],imagePlaceholder:false,
  sourceUrl:sources.tmsStand.url,sourceName:'トムスショップ',
  channels:[['トムスショップ商品页',sources.tmsStand.url,shop],['トムスショップ Season2特设',sources.tmsList.url,doc]],
}));

const aoashiOrder='受注期间：正文写2026年10月23日（金）18时起，概要栏写2026年10月23日（金）10:00～2026年11月24日（火）23:59。两处并存，未改写。';
const aoashiLines=[
  ['オリジナルTシャツ（全2種）','服饰','各4,400円（税込）','L／XL',['动画主视觉，以及エスペリオン标志加アシト背号，两种']],
  ['ぬいぐるみキーホルダー（全2種）','挂件','各2,200円（税込）','本体約Ｈ800mm',['アシト与栗林','尺寸按新闻稿原文「本体約Ｈ800mm」保留，未改写成其他数值']],
  ['ハンドタオル（全4種）','生活 / 收藏','各880円（税込）','W200mm×H200mm',['各选手背号']],
  ['刺繍ワッペン（全1種）','生活 / 收藏','1,320円（税込）','W约70mm×H约70mm',['エスペリオンユース标志']],
  ['クリアファイル（全2種）','卡片 / 文具','各550円（税込）','W约220mm×H约313mm',['主视觉与预告视觉']],
  ['フライトタグ（全8種）','生活 / 收藏','各770円（税込）','W140mm×H30mm',['选手名与背号']],
  ['缶バッジ（全8種）','徽章','各550円（税込）','直径57mm',[]],
  ['ステッカー（全8種）','生活 / 收藏','440円（税込）','W60mm×H70mm以内',['价格原文没有写「各」']],
];
const aoashiGoods=aoashiLines.map(([name,category,price,size,specifications])=>item('aoashi',{
  name:`アオアシ Season2 ${name}`,category,manufacturer:'株式会社ブリッジ（ともすと）',productBrand:'ともすと受注生产',acquisitionType:'零售 / 受注商品',
  price,releaseDate:'2026年10月23日～2026年11月24日受注',size,characters:'青井葦人 / 系列选手见官方配图',
  specifications:[...specifications,aoashiOrder,'另计发送手续费','新闻稿写共39种，本档按已标价的系列行登记，没有把未列名单款拆开'],
  description:description+(name.startsWith('ぬいぐるみ')?' 挂件尺寸保留新闻稿原文约Ｈ800mm。':''),
  sourceUrl:sources.bridge.url,sourceName:'株式会社ブリッジ · 公开新闻稿',
  channels:[['ブリッジ新闻稿',sources.bridge.url,doc],['ともすと商店入口',sources.tomo.url,'官方商店入口（页面脚本渲染，未逐条核对SKU库存）']],
}));
aoashiGoods.push(item('aoashi',{
  name:'アオアシ Season2 【特典】ポストカード（全4種）',category:'卡片 / 文具',manufacturer:'株式会社ブリッジ（ともすと）',productBrand:'ともすと购买特典',acquisitionType:'购买特典',
  price:'非单品标价；1会计满3,300円（税込）赠1枚',releaseDate:'2026年10月23日～2026年11月24日受注期间',size:'W100mm×H148mm',characters:'系列商品 / 角色见官方配图',
  specifications:['随机4种中的1枚',aoashiOrder],
  sourceUrl:sources.bridge.url,sourceName:'株式会社ブリッジ · 公开新闻稿',
  channels:[['ブリッジ新闻稿',sources.bridge.url,doc],['ともすと商店入口',sources.tomo.url,'官方商店入口（页面脚本渲染，未逐条核对SKU库存）']],
}));

const targets=[
  {
    key:'ojikawa',id:'ole-73acd87f49ee',originalTitle:'おじさんはカワイイものがお好き。',site:sources.ojikawaHome.url,source:tsutayaUrl,
    label:'大叔喜欢可爱小玩意 · 动画官网与SHIBUYA TSUTAYA快闪',
    scope:'登记动画官网播出信息，以及SHIBUYA TSUTAYA 6楼IP书店2026年10月30日至11月15日快闪页上写明价格的6条商品或系列。读卖电视台商品页只列出店铺，没有单品和价格，所以没有编成商品。官网导航未见影像商品页。不是全市场收集。',
    yearSource:sources.ojikawaOnair.url,yearNote:'动画官网ON AIR记2026年10月4日（日）起于TOKYO MX、读卖电视台、BS朝日等播出。',
    sources:[sources.ojikawaHome,sources.ojikawaOnair,sources.ytvGoods,sources.tsutaya,sources.fod],
    notes:['快闪价格按活动页原文，不表示会期结束后仍可购买。','读卖电视台商品页与FOD报道只作播出和渠道交叉核对，没有从中补写单品。'],
    goods:ojikawaGoods,
  },
  {
    key:'yowaki',id:'ole-b5f3972beab5',originalTitle:'弱気MAX令嬢なのに、辣腕婚約者様の賭けに乗ってしまった',site:sources.yowakiHome.url,source:sources.yowakiBd.url,
    label:'弱气MAX的大小姐 · 动画官网、KADOKAWA商店与音乐页',
    scope:'登记官网Blu-ray与DVD各3卷、KADOKAWA商店列出的对应商品入口、20周年亚克力立牌，以及音乐页上的OP配信和ED所收录专辑两种形态。小说与漫画单行本未纳入。',
    yearSource:sources.yowakiOnair.url,yearNote:'动画官网ON AIR记2026年10月4日（日）起于TOKYO MX、BS朝日、AT-X、SUN电视台等23局播出。',
    sources:[sources.yowakiHome,sources.yowakiOnair,sources.yowakiBd,sources.yowakiMusic,sources.kadoBd1,sources.kadoAcrylic,sources.kadoList],
    notes:['第2、3卷的商店链接来自已获取的KADOKAWA映像目录页标题，价格与品番来自动画官网。','亚克力立牌价格节点只显示1,870円，没有在该节点写税込。','OP只有配信日期，没有实体标价。'],
    goods:yowakiGoods,
  },
  {
    key:'nama',id:'ole-cb17d1062ff3',originalTitle:'生徒会にも穴はある！',site:sources.namaHome.url,source:sources.namaBd.url,
    label:'学生会也有洞！ · 动画官网与Aniplex公告',
    scope:'按官网Blu-ray＆DVD第1至第6卷页面，分别登记特装版Blu-ray、完全生产限定版Blu-ray和DVD。第6卷抱枕角色保留页面原文问号。Medicos的唐吉诃德活动页没有单品名称和价格，没有编成商品。',
    yearSource:sources.namaOnair.url,yearNote:'动画官网ON AIR记2026年10月3日（土）24:30起于TOKYO MX、BS11等播出。',
    sources:[sources.namaHome,sources.namaOnair,sources.namaBd,sources.namaBd2,sources.namaBd3,sources.namaBd4,sources.namaBd5,sources.namaBd6,sources.aniplexNews,sources.medicos],
    notes:['第2至第6卷的特典CD曲目在静态页面中没有逐条展开，规格只保留页面已写出的共同项目。','Medicos新闻确认2026年11月7日起唐吉诃德活动及满2,000円（税込）赠卡，但商品表没有名称和单价。'],
    goods:namaGoods,
  },
  {
    key:'hako',id:'ole-91ad750080fb',originalTitle:'アオのハコ Season2',site:sources.hakoHome.url,source:sources.hako1.url,
    label:'青之箱 第二季 · 动画官网与トムスショップ',
    scope:'只登记标明Season2的Blu-ray Vol.1至Vol.3，以及トムスショップ两件预告视觉商品。第一季影像、法人店铺赠品和SHIBUYA109快闪里未标单价的新品没有拆成商品。官网商品页没有写出发行公司。',
    yearSource:sources.hakoHome.url,yearNote:'动画官网记Season2自2026年10月4日（日）起于TBS系全国同步播出。',
    sources:[sources.hakoHome,sources.hako1,sources.hako2,sources.hako3,sources.hakoBonus,sources.tmsList,sources.tmsFile,sources.tmsStand,sources.tmsEvent],
    notes:['Blu-ray价格按官网原文同时保留11,000円与税抜价格10,000円。','トムス・エンタテインメント2026年10月21日新闻确认SHIBUYA109快闪，但没有逐件标价。','商店页写明库存显示不是实时库存。'],
    goods:hakoGoods,
  },
  {
    key:'aoashi',id:'ole-861abb65641d',originalTitle:'アオアシ Season2',site:sources.aoashiHome.url,source:sources.bridge.url,
    label:'青之芦苇 第二季 · 动画官网与ともすと运营方新闻',
    scope:'按株式会社ブリッジ2026年10月22日新闻稿，登记已写明价格或赠品条件的系列行。39种没有拆成页面未列出的单款。商店HTML未包含SKU价格。其他厂商商品未在本批逐页核对。',
    yearSource:sources.aoashiHome.url,yearNote:'动画官网记述NHK Eテレ自2026年10月4日（日）起播出。',
    sources:[sources.aoashiHome,sources.bridge,sources.tomo],
    notes:['受注开始时刻在同一新闻稿中出现18时与10:00两处写法，档案同时保留。','ぬいぐるみキーホルダー尺寸保留原文约Ｈ800mm。','ステッカー价格原文没有写「各」。'],
    goods:aoashiGoods,
  },
];

const context={window:{}};
vm.runInNewContext(await readFile(resolve(root,'data/catalog-data.js'),'utf8'),context);
const catalog=context.window.ANIME_CATALOG;
const originalIds=catalog.items.map(work=>work.id);
assert.equal(catalog.items.length,1427);
const untouched=new Set(['ole-ce2cf196c30e','ole-12b781269ea2']);
const tally=(items,key)=>items.reduce((out,row)=>(out[row[key]]=(out[row[key]]||0)+1,out),{});
for(const target of targets){
  assert(!untouched.has(target.id));
  const work=catalog.items.find(row=>row.id===target.id);
  assert(work&&work.name);
  const old=work.merch||[];
  assert(old.every(row=>row.addedInBatch===batch),'只合并本批已追加的记录');
  const positions=new Map(old.map((row,index)=>[row.id,index]));
  for(const original of target.goods){
    const row=structuredClone(original);
    assert(row.name&&row.sourceUrl.startsWith('https://')&&row.channels.length);
    if(!row.image){row.image=work.localPoster;row.images=[];row.imagePlaceholder=true;}
    if(positions.has(row.id)){
      const index=positions.get(row.id),previous=old[index],channels=[...previous.channels];
      for(const channel of row.channels){
        const found=channels.findIndex(item=>item.url===channel.url&&item.name===channel.name);
        if(found>=0)channels[found]={...channels[found],...channel};else channels.push(channel);
      }
      old[index]={...previous,...row,channels:channels.filter((channel,index,all)=>all.findIndex(item=>item.url===channel.url&&item.name===channel.name&&item.linkType===channel.linkType)===index),images:[...new Set([...(previous.images||[]),...(row.images||[])])]};
    }else{positions.set(row.id,old.length);old.push(row);}
  }
  work.merch=old;
  work.originalTitle=target.originalTitle;
  work.retrievedAt=checkedAt;
  work.goodsLibrary=true;
  work.officialSiteUrl=target.site;
  work.goodsSourceUrl=target.source;
  work.goodsSourceLabel=target.label;
  work.goodsResearchScope=target.scope;
  work.goodsExport=`data/chronology-${target.key}-products.csv`;
  work.researchReportUrl='reports/chronology-latest-five.html';
  work.yearSources=[{url:target.yearSource,note:target.yearNote,checkedAt}];
  work.chronologyResearch={batch,checkedAt,products:old.length,sources:target.sources,limits:target.scope};
  work.manufacturerResearch={
    checkedAt,batch,newProducts:target.goods.length,totalProducts:old.length,
    prizeProducts:old.filter(row=>row.acquisitionType==='娃娃机景品').length,
    manufacturerCounts:tally(old,'manufacturer'),
    sourceNotes:[target.scope,...target.notes,'商品页、活动页和商店入口分别标注。没有把来源报价写成实时库存。'],
    limits:target.scope,
  };
  const summary=new Map();
  for(const row of old)for(const channel of row.channels){
    if(!summary.has(channel.name))summary.set(channel.name,{name:channel.name,sourceUrl:channel.url,description:channel.linkType,examples:[]});
    const entry=summary.get(channel.name);
    if(entry.examples.length<3&&!entry.examples.includes(row.name))entry.examples.push(row.name);
  }
  work.channelSummary=[...summary.values()];
}
assert.deepEqual(catalog.items.map(work=>work.id),originalIds);
const research={
  checkedAt,batch,
  scope:'作品清单「最新」顺序的前5部。只采用无需登录的公开页面。不是这5部的全市场收集，也不是后续25部已调查。',
  works:targets.map(target=>({id:target.id,name:catalog.items.find(work=>work.id===target.id).name,originalTitle:target.originalTitle,products:target.goods.length,limits:target.scope,sources:target.sources,goods:target.goods})),
};
await writeFile(resolve(root,'data/latest-order-batch-2026-11-06.json'),JSON.stringify(research,null,2)+'\n');
await writeFile(resolve(root,'data/catalog-data.js'),'window.ANIME_CATALOG = '+JSON.stringify(catalog)+';\n');
const progress=JSON.parse(await readFile(resolve(root,'data/chronology-progress.json'),'utf8'));
const done=new Map(targets.map(target=>[target.id,target]));
for(const row of progress.queue){
  if(!done.has(row.id))continue;
  row.yearVerified=true;
  row.stage='最新顺序第1批目录调查已入库，仍有待补来源';
}
progress.latestOrderBatch={checkedAt,order:'作品清单「最新」',completedWorks:targets.map(target=>target.id),products:targets.reduce((sum,target)=>sum+target.goods.length,0),note:'本批只处理最新顺序前5部。首轮按年份调查仍只有海贼王和学园默示录。'};
await writeFile(resolve(root,'data/chronology-progress.json'),JSON.stringify(progress,null,2)+'\n');
console.log(JSON.stringify({status:'imported',products:targets.map(target=>({key:target.key,count:target.goods.length,id:target.id}))},null,2));
