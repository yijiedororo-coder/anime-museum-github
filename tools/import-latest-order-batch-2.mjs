// Append the 2026-11-06 public-source batch for latest-order works 6–10.
// Does not rewrite 海贼王, 学园默示录, the first five titles, work order, or other merchandise.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import assert from 'node:assert/strict';
import vm from 'node:vm';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const checkedAt='2026-11-06';
const batch='2026-11-06-latest-order-6-10';
const doc='官方资料页 / 目录（非购买确认）';
const shop='官方目录列出的商品页（目标库存未核查）';
const event='零售活动公告（非实时库存）';
const availability='历史及已公告商品资料，不表示当前有货。原价、投放与发售日期保留为来源记录。未核查实时库存。';
const description='按公开页面登记的商品或系列档案。一条多款系列不拆成未列明的单品。价格、日期和尺寸只保留来源原文。';
const idFor=(key,name)=>'latest-'+createHash('sha256').update(key+'|'+name).digest('hex').slice(0,18);
const src=(url,checkedAtJST,sha256,bytes)=>({url,checkedAtJST,sha256,bytes});
const noSize='来源目录未标尺寸；请核对商品详情';

const sources={
  kanataHome:src('https://kanatakara-anime.com/','2026-11-06T15:11:43.044461+09:00','90f926c02ccde42dabf0008de998fff9d759e883f6a32da99a3060cf109f6943',24763),
  kanataOnair:src('https://kanatakara-anime.com/onair/','2026-11-06T15:11:44.446881+09:00','df5c7a7499bfaa97c341c0e9905386240f29b25ced3f06c0da50107ad592a3d8',22782),
  kanataMusic:src('https://kanatakara-anime.com/music/','2026-11-06T15:12:16.201905+09:00','d37d2a93dff6a25507a0cf88cf76141597318f3ebd466161a21280fb50706b8f',20425),
  kanataNews:src('https://www.kanatakara-anime.com/news/','2026-11-06T15:11:45.415353+09:00','6ec9d8d2bca2ac069012b11de920ec6f2a1aaa5f95f955e47ea3f41a4cf1a6c5',13435),
  kanataRakuten:src('https://books.rakuten.co.jp/event/all/kanatakara-anime/?scid=we_rcc_anime_official','2026-11-06T15:12:27.928844+09:00','3aeed493c752f207ed746df20912b544ff9fb7f8d03c6d62dc747b151dd27d73',61046),
  kanataBooks:src('https://www.hakusensha.co.jp/comicslist/42543/','2026-11-06T15:12:30.101696+09:00','777e49fc25cfdf337b4e580951eec3f1c11f5b1f3aebae00b70fef81dc6a54ba',149857),
  hotelHome:src('https://hotel-inhumans.com/','2026-11-06T15:11:46.806466+09:00','be828b8047c78bd73b6c407baad63bc6aa99f3bea297ff232ab207388ae9e609',22698),
  hotelBd:src('https://hotel-inhumans.com/blu-ray.html','2026-11-06T15:11:48.069999+09:00','b371a4743b4941f09ba1dfd6d4e2466724d7248c8ad5e84df7ea19e82bfc7ef2',8975),
  hotelNews99:src('https://hotel-inhumans.com/news/news-99.html','2026-11-06T15:11:49.309070+09:00','9add0141af31412fa35d318802a8cb30b585313a0a1c0ead1419f005dfffcd47',3717),
  hotelNews70:src('https://hotel-inhumans.com/news/news-70.html','2026-11-06T15:15:42.001611+09:00','c034d1e9dffa760ac246a6fd5d165e599a6c9017940d963c33f92f9160d117d8',6260),
  hotelNews71:src('https://hotel-inhumans.com/news/news-71.html','2026-11-06T15:11:50.486668+09:00','f539e2537752e87f47af36d9e912f0e680236d3f73f7d1d24e7a2cb3d1516cc1',7718),
  hotelNews17:src('https://hotel-inhumans.com/news/news-17.html','2026-11-06T15:15:37.918692+09:00','a8ab3d80d6765d8caad69d43192a8199828548dadfc21a2b52624bed890f3865',3679),
  hotelNews78:src('https://hotel-inhumans.com/news/news-78.html','2026-11-06T15:15:39.005981+09:00','4e5b5d727ffcb2b8a4396d0b70035eacad13270b9225ccd570bc2b7dbdf6303d',3249),
  hotelNews87:src('https://hotel-inhumans.com/news/news-87.html','2026-11-06T15:15:39.965116+09:00','aca00c29a213b4c8c5a5b01343a24db85b876554c059333b6276c8d3070b4966',3556),
  hotelNews86:src('https://hotel-inhumans.com/news/news-86.html','2026-11-06T15:15:41.067617+09:00','d9e7299523b043ca17559d295d2fa72f897fa01e75da6c2c720236cc73010390',5508),
  seiHome:src('https://sh-anime.shochiku.co.jp/seihantai_anime/','2026-11-06T15:11:52.206251+09:00','a49101690e39c5bb7f19cd433dcf1ae9500756c65f482e2edb5399dafb370cbe',90976),
  seiOnair:src('https://sh-anime.shochiku.co.jp/seihantai_anime/onair','2026-11-06T15:12:44.603321+09:00','8ecc52d8159d457d97541196c33feb248b4abfdac9dbc75bad4c82c8bd10c62b',55975),
  seiMusic:src('https://sh-anime.shochiku.co.jp/seihantai_anime/music','2026-11-06T15:12:42.491335+09:00','186c1208e5428aa189aec557463285da3fb6a627d35acfe34cf53fe8d2fd2d36',38788),
  seiGoods:src('https://sh-anime.shochiku.co.jp/seihantai_anime/goods','2026-11-06T15:12:37.994048+09:00','c0a5b113a4cbc45f4a6e6683189a2eb9f3225f69bacc191d88bc77c49fc2fe74',31845),
  seiBd1:src('https://sh-anime.shochiku.co.jp/seihantai_anime/blu-ray/bd1','2026-11-06T15:12:48.232166+09:00','8f98e050d0c344484de91c1c6d92cf3bfde280e4cac6bf55478ce164256b39b1',27512),
  seiBd2:src('https://sh-anime.shochiku.co.jp/seihantai_anime/blu-ray/bd2','2026-11-06T15:12:50.096853+09:00','ac21321f8d0359a098c6f05983000c7335bf6411391fb40add288fa9d2db502b',27434),
  seiBd3:src('https://sh-anime.shochiku.co.jp/seihantai_anime/blu-ray/bd3','2026-11-06T15:12:51.663008+09:00','021507a4efd23cfcbaf6590cc20047ca3adb91654f445d26a270078592480cf4',27579),
  seiBd4:src('https://sh-anime.shochiku.co.jp/seihantai_anime/blu-ray/bd4','2026-11-06T15:12:53.581220+09:00','62bef3b5d49a9e0ad1980d50c36a16e5ff95f807fe03331ae9f549c387ccd9b3',27234),
  seiOst:src('https://sh-anime.shochiku.co.jp/seihantai_anime/news/714','2026-11-06T15:15:50.404754+09:00','282a07058e3d950ab73e2def12c5a0a12c6445253eeab338c75308fe640342bb',20301),
  seiPopup:src('https://sh-anime.shochiku.co.jp/seihantai_anime/news/709','2026-11-06T15:15:46.820700+09:00','ea99b6b05b14a8c4e78c4748f93f343e2645a931da4cbb2f9176ed7e8395f643',21807),
  seiEvent:src('https://sh-anime.shochiku.co.jp/seihantai_anime/news/721','2026-11-06T15:15:45.052955+09:00','19bca56dff89450d5800c7134c750b61443a7e603a0e5a81799454a1fac9854f',27253),
  kanHome:src('https://kanteiskill.com/','2026-11-06T15:11:53.487105+09:00','820019a0f6240838607d0733de09c2b42ffcdf619ea738c96516079b5cc8680b',28453),
  kanOnair:src('https://kanteiskill.com/onair/','2026-11-06T15:12:56.253654+09:00','6641a1260085375ff971edac50f066b6a08c68bbc85ef73ad930a941c67f34d6',27185),
  kanBd:src('https://kanteiskill.com/product/bd3','2026-11-06T15:11:54.762153+09:00','cfa028fa1aa108b51eb8dcb0c63a6f6c38c2a2e1580bc7833adbedbd1842a1d8',29224),
  kanOp:src('https://kanteiskill.com/product/op3/','2026-11-06T15:12:57.229394+09:00','1611451e03a80b0113b1aae30759df5d445b78cef740dac30897c7610fd4ac16',35688),
  kanEd:src('https://kanteiskill.com/product/ed3','2026-11-06T15:15:43.193468+09:00','6297cc1717c49e2adb8d6b2357a92d01d6028b583033cda8821590115822c040',33546),
  kanGoods:src('https://kanteiskill.com/goods/','2026-11-06T15:12:55.155134+09:00','90fef5215082d074256d7f3dedb2bbc792ecd881898a0a134bbf3e786a5353cb',31365),
  kanBonus:src('https://kanteiskill.com/product/shop-tokuten3','2026-11-06T15:12:57.928529+09:00','b610588857c7218e23ab781fa755b9167bcee5fcdea0c063c9bd4c1524eb9d6d',38561),
  kanMini:src('https://kanteiskill.com/news/2456','2026-11-06T15:13:05.479016+09:00','547bb5cd31350a91d3436d25daff4fdf15f98d460000d0ef1d3f1bfc6c6dbbf5',25989),
  kanVGoods:src('https://v-storage.jp/bv_news/286600/','2026-11-06T15:13:04.369435+09:00','1521d39c8e981be8d125aa9646ecdc29ea9dca77d71ac9db3b96ff8559317710',75860),
  kanVBd:src('https://v-storage.jp/catalog_news/289600/','2026-11-06T15:17:11.364143+09:00','53d47646d4905bc1ea06fc7bee616ce1193d31299983d4165b5b667e6833bb36',40983),
  saiHome:src('https://saikyosoubi.com/','2026-11-06T15:11:56.301670+09:00','f3f8fe621e22f7dd8eca656873420e67be892bd623cda5e54b1250e9bb62d587',115160),
  saiOnair:src('https://saikyosoubi.com/onair/','2026-11-06T15:13:01.302060+09:00','52a7af322161d69119cb8ba27151b01a87e49ec4cf93ff182c3d7f9b732e99fc',24111),
  saiBd:src('https://saikyosoubi.com/bluray/','2026-11-06T15:12:59.110373+09:00','0b7ea7c8fa43deaeca2ce61d555c379225c9f93db7def9ef518407778c7a86b1',37511),
  saiMusic:src('https://saikyosoubi.com/music/','2026-11-06T15:13:00.290815+09:00','49b9cd008b33a8abc25af12b6c4b7e39c76fc5813e4c88cbc3dbdccb4f32a975',25147),
  saiNews:src('https://saikyosoubi.com/news/?article_id=71279','2026-11-06T15:13:03.557744+09:00','941b987ee21cfd3c27190ae82b4bdbdf386ade51f44cd858fdd1cef936bc7fe1',11077),
  saiCollab:src('https://saikyosoubi.com/news/?article_id=71251','2026-11-06T15:13:02.302753+09:00','8dc8278ce1c8e36797afbc3f39036acd29b50ee7aaad6d7eb0ea8dc8dca0ab57',11167),
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
    price:fields.price,releaseDate:fields.releaseDate,size:fields.size||noSize,
    description:fields.description||description,specifications:fields.specifications||[],
    image:fields.image||'',images:fields.images||[],sourceUrl:fields.sourceUrl,sourceName:fields.sourceName,
    checkedAt,channels,addedInBatch:batch,availability,imagePlaceholder:Boolean(fields.imagePlaceholder),
  };
}

const dmmBox='https://www.dmm.com/mono/dvd/-/detail/=/cid=dmpxa456/';
const dmmBox2='https://www.dmm.com/mono/dvd/-/detail/=/cid=dmpxa489/';
const hotelGoods=[
  item('inhumans',{
    name:'ホテル・インヒューマンズ Blu-ray BOX Ⅱ',category:'音乐 / 影像',manufacturer:'官方商品页未标注发行公司',productBrand:'TV动画 Blu-ray BOX',acquisitionType:'零售周边',
    price:'39,600円（税込）',
    releaseDate:'商品页：2027.2.24（Wed）Release。同站2026.10.04新闻写2027年2月6日（水）。两处并存，未改写。',
    characters:'星生朗 / 灰咲沙羅',
    specifications:['品番：DMPXA-489','収録話：request 14.～request 26.','同梱特典：アニメ描き下ろしジャケット、スペシャルブックレット（原作・田島 青先生描き下ろし漫画収録）','映像特典：ノンクレジットオープニング映像、ノンクレジットエンディング映像','商品页与2026.10.04新闻都没有写发行公司'],
    description:description+' 发售日按商品页与新闻原文并列保留。',
    sourceUrl:sources.hotelBd.url,sourceName:'TV动画官网 · Blu-ray',
    channels:[['TV动画官网 Blu-ray',sources.hotelBd.url,doc],['Blu-ray BOXⅡ发售新闻',sources.hotelNews99.url,doc],['DMM商品页',dmmBox2,shop]],
  }),
  item('inhumans',{
    name:'ホテル・インヒューマンズ Blu-ray BOX',category:'音乐 / 影像',manufacturer:'合同会社DMM.com',productBrand:'TV动画 Blu-ray BOX',acquisitionType:'零售周边',
    price:'39,600円（税込）',releaseDate:'2025.12.24（Wed）Release',characters:'星生朗 / 灰咲沙羅',
    specifications:[
      '品番：DMPXA-456','収録話：request 1.～request 13.',
      '同梱特典：アニメ描き下ろしジャケット、スペシャルブックレット（原作・田島 青先生描き下ろし漫画収録）',
      '映像特典：ノンクレジットオープニング映像、ノンクレジットエンディング映像',
      '可见正文的早期预约特典：原作・田島 青先生描き下ろしミニ色紙（灰咲沙羅）。截止日期写在页面注释中，可见正文没有该日期，未写入。',
      '2025.09.25规格变更公告：Blu-ray Vol.1 19,800円（税込）＜品番：DMPXA-454＞与 Blu-ray Vol.2 19,800円（税込）＜品番：DMPXA-455＞発売中止；变更后为 Blu-ray BOX 39,600円（税込）＜品番：DMPXA-456＞、2025年12月24日（水）発売。中止标题不另建商品。',
      '同日乐天活动页把变更后的应募期间写成「2025年9月25日（木）18:00 ～ 2025年12年23日（火）23:59」，原文「12年」未改。变更前一处写成「2025年7月6日（火） ～ 2025年11年25日（火）23:59」，原文「11年」未改。',
    ],
    description:description+' 发行公司取自规格变更公告落款；商品页本身没有再写公司名。',
    sourceUrl:sources.hotelBd.url,sourceName:'TV动画官网 · Blu-ray',
    channels:[['TV动画官网 Blu-ray',sources.hotelBd.url,doc],['规格变更·再发售公告',sources.hotelNews70.url,doc],['活动对象商品变更公告',sources.hotelNews71.url,event],['DMM商品页',dmmBox,shop]],
  }),
];

const seiDisc='画面サイズ：16：9 フルサイズ〔1080p/Hi-Def〕／ディスクタイプ：BD50G／音声：（オリジナル）日本語 リニアPCM2.0chステレオ／字幕：なし';
const seiVolumes=[
  [1,'2026年4月22日(水)発売','13,200円（税込）','SHBR-0798','本編：約144分＋映像特典 約30分以上','第1话～第6话','ラパントラック描き下ろし特製アウターケース（鈴木・谷）','ABEMAアニメ祭 スペシャルステージ映像、OP映像、PV集、映画「北の魔女とイエティ」予告','イエティ着せ替えカード、Blu-ray風アクリルキーホルダー、オリジナルクリアカード、イエティイベント抽選申込券','鈴木 / 谷',sources.seiBd1.url,'https://store.shochiku.co.jp/shop/g/gSHBR0798/'],
  [2,'2026年5月27日(水)発売','13,200円（税込）','SHBR-0799','本編：約144分＋映像特典 約30分以上','第7话～第12话','ラパントラック描き下ろし特製アウターケース（山田・西）','先行上映会 舞台挨拶映像、ノンクレジットED、マナーCM','Blu-ray風アクリルキーホルダー、オリジナルクリアカード、イエティイベント抽選申込券','山田 / 西',sources.seiBd2.url,'https://store.shochiku.co.jp/shop/g/gSHBR0799/'],
  [3,'2026年10月21日(水)発売','13,200円（税込）','SHBR-0813','本編：約145分＋映像特典約20分以上','第13话～第18话','ラパントラック描き下ろし特製アウターケース(平・東)','AnimeJapanスペシャルステージ映像、2期 OP映像、PV集、映画「北の魔女とイエティ」予告','イエティ着せ替えカード用 着せ替えパーツ(2つ)、Blu-ray風アクリルキーホルダー、オリジナルクリアカード、イエティイベント(第2弾)抽選申込券','平 / 東',sources.seiBd3.url,'https://store.shochiku.co.jp/shop/g/gSHBR0813/'],
  [4,'2026年12月2日(水)発売','13,200円（税込）','SHBR-0814','本編：約169分＋映像特典約30分以上','第19话～第25话','ラパントラック描き下ろし特製アウターケース(鈴木・谷)','第13话先行上映会 みんな大集合トークイベント映像、2期 ノンクレジットED','Blu-ray風アクリルキーホルダー、オリジナルクリアカード、イエティイベント(第2弾)抽選申込券','鈴木 / 谷',sources.seiBd4.url,'https://store.shochiku.co.jp/shop/g/gSHBR0814/'],
];
const seiGoods=seiVolumes.map(([volume,date,price,code,runtime,episodes,outerCase,video,inserts,characters,url,store])=>item('seihantai',{
  name:`正反対な君と僕 第${volume}巻 Blu-ray`,category:'音乐 / 影像',manufacturer:'松竹',productBrand:'TV动画 Blu-ray',acquisitionType:'零售周边',
  price,releaseDate:date,characters,
  specifications:[`品番：${code}`,runtime,seiDisc,`本編：${episodes}`,`映像特典：${video}`,`外装特典：${outerCase}`,`封入特典：${inserts}`,'発売・販売元：松竹','店舗別特典见同页，没有单独标价，未另建商品',
    volume>=3?'2026.10.19新闻将第3卷、第4卷封入抽选券对应的活动写为2027年4月29日(木・祝)「イエティーパーティー」。第3卷应募期间：2026年10月20日(火)10:00～2026年11月17日(火)23:59。第4卷：2026年12月1日(火)10:00～2027年1月13日(水)23:59。':'第1卷、第2卷页面写抽选活动已于2026年6月28日(日)结束，追加生产不再封入抽选券。'],
  sourceUrl:url,sourceName:'TV动画官网 · Blu-ray',
  channels:[['TV动画官网 Blu-ray',url,doc],['松竹官方商店',store,shop]],
}));
seiGoods.push(item('seihantai',{
  name:'『正反対な君と僕』オリジナル・サウンドトラック Vol.02（配信）',category:'音乐 / 影像',manufacturer:'官方新闻未标注厂商',productBrand:'TV动画第2期原声',acquisitionType:'配信',
  price:'来源未标注实体价格',releaseDate:'新闻标题：9/28（月）。新闻日期为2026.09.27，标题没有再写年份。',characters:'系列商品 / 角色见官方配图',
  specifications:['第2期剧伴','tofubeats','全19曲','没有品番','配信链接：https://lnk.to/SEIHANTAI2'],
  sourceUrl:sources.seiOst.url,sourceName:'TV动画官网 · NEWS',
  channels:[['TV动画官网 NEWS',sources.seiOst.url,doc]],
}));

const chV=sources.kanVGoods.url;
const chThe='https://www.the-chara.com/';
const chReserve='报道日期2026.9.17。先行预约原文：本日9月17日(木)18：00～10月1日(木)23:59。系列行没有单款名称，未拆分。';
const kanteiLines=[
  ['カンバッジ(ブラインド)','徽章','単品440円（税込）、セット3,080円（税込）'],
  ['アクリルフィギュア','立牌','各1,650円（税込）'],
  ['両面アクリルフィギュア','立牌','各1,430円（税込）'],
  ['ミニアクリルアート','立牌','2,530円（税込）'],
  ['ミニアクリルスタンド','立牌','各770円（税込）'],
  ['チェンジングキーホルダー','挂件','各1,430円（税込）'],
];
const kanteiGoods=kanteiLines.map(([name,category,price])=>item('kantei3',{
  name:`THEキャラ ${name}`,category,manufacturer:'来源页未标注厂商',productBrand:'THEキャラ',acquisitionType:'零售 / 受注商品',
  price,releaseDate:'2026年9月17日(木)18：00～10月1日(木)23:59先行预约',size:noSize,characters:'系列商品 / 角色见官方配图',
  specifications:[chReserve,'商品名沿用新闻中的系列名，没有写成第3期单品','通贩入口是网站首页，没有逐条SKU页面'],
  sourceUrl:chV,sourceName:'バンダイナムコフィルムワークス · V-STORAGE',
  channels:[['V-STORAGE 第3期新商品新闻',chV,doc],['THEキャラ通贩首页',chThe,'官方新闻给出的通贩入口（未逐条核对SKU库存）']],
}));
kanteiGoods.push(item('kantei3',{
  name:'『転生貴族、鑑定スキルで成り上がる 第3期』Blu-ray BOX（特装限定版）',category:'音乐 / 影像',manufacturer:'バンダイナムコフィルムワークス',productBrand:'TV动画第3期 Blu-ray BOX',acquisitionType:'零售周边',
  price:'41,800円（税込）',releaseDate:'2027年2月26日発売',characters:'アルス・ローベント / リーツ・ミューセス',
  specifications:[
    '品番：BCXA-2100','収録内容：第25話～第36話',
    '官网：約348分＜本編約288分＋特典約60分＞／本編ディスク：ﾘﾆｱPCM（ｽﾃﾚｵ）／AVC／BD50G×2枚／16:9<1080i High Definition>／特典ディスク：ﾘﾆｱPCM（ｽﾃﾚｵ）／AVC／BD25G×1枚／16:9<1080p High Definition>・一部16:9<1080i High Definition>',
    'V-STORAGE目录稿另写：税抜価格：￥38,000　税込価格（10％）：￥41,800。スペック：カラー／（予）348分／（本編ﾃﾞｨｽｸ：約288分+特典ﾃﾞｨｽｸ：約60分）／リニアPCM (ステレオ)／AVC／BD50G／16:9<1080p High Definition>・一部16:9<1080i High Definition。分辨率写法与官网不同，两处并存。',
    '同一目录稿标题和商品名写第3期，正文一处写成「『転生貴族、鑑定スキルで成り上がる 第2期』Blu-ray BOXが2027年2月26日に発売決定」。品番同为BCXA-2100。未把这句改成第3期。',
    '仕様：キャラクターデザイン八尋裕子描き下ろしWブックケース、キャラクター原案jimmy＆漫画原作井上菜摘描き下ろしインナージャケット',
    '特典ディスク：第3期放送直前特番（本編／特典限定パート）、ノンクレジットOP、ノンクレジットED、PV&CM',
    'ドラマCD「傭兵リーツ・ミューセス」：リーツ・ミューセス 坂 泰斗／アルス・ローベント 藤原夏海',
    '店舗別購入特典没有单独标价，未另建商品',
  ],
  sourceUrl:sources.kanBd.url,sourceName:'公式ポータル · 第3期 Blu-ray BOX',
  channels:[['公式ポータル 第3期 Blu-ray',sources.kanBd.url,doc],['V-STORAGE目录稿',sources.kanVBd.url,doc],['第3期店舗別購入特典',sources.kanBonus.url,doc]],
}),item('kantei3',{
  name:'OP主題歌「Still Water 」佐々木李子 アーティスト盤',category:'音乐 / 影像',manufacturer:'Lantis',productBrand:'第3期OP主題歌',acquisitionType:'零售周边',
  price:'【アーティスト盤】3,300円(10%税込)/3,000円(税抜)',releaseDate:'2026年11月11日(水)',characters:'系列商品 / 角色见官方配图',
  specifications:['品番：LACM- 24728 (CD＋BD)','页面品番在连字符后有空格','他新規楽曲2曲','Blu-ray：01.「Still Water」 Music Video、02. Music Video Making','作詞・作曲：Skipjack　編曲：佐藤厚仁','店铺特典没有单独标价，未另建商品'],
  sourceUrl:sources.kanOp.url,sourceName:'公式ポータル · 第3期OP',
  channels:[['公式ポータル 第3期OP',sources.kanOp.url,doc]],
}),item('kantei3',{
  name:'OP主題歌「Still Water 」佐々木李子 アニメ盤',category:'音乐 / 影像',manufacturer:'Lantis',productBrand:'第3期OP主題歌',acquisitionType:'零售周边',
  price:'【アニメ盤】1,500円(10%税込)/1,650円(税抜)',releaseDate:'2026年11月11日(水)',characters:'系列商品 / 角色见官方配图',
  specifications:['品番：LACM- 24729 (CDのみ)','页面把1,500円标为10%税込、把1,650円标为税抜。两数与通常税率方向相反，按原文保留，未改算。','他新規楽曲2曲','作詞・作曲：Skipjack　編曲：佐藤厚仁'],
  description:description+' 动画盘价格节点的税込与税抜数字按页面原样保留。',
  sourceUrl:sources.kanOp.url,sourceName:'公式ポータル · 第3期OP',
  channels:[['公式ポータル 第3期OP',sources.kanOp.url,doc]],
}),item('kantei3',{
  name:'ED主題歌「日々を越えて 」明くる夜の羊 初回限定盤',category:'音乐 / 影像',manufacturer:'UNIERA',productBrand:'第3期ED主題歌',acquisitionType:'零售周边',
  price:'【初回限定盤】4,400円（10％税込）/4,000円（税抜）',releaseDate:'CD：2026年11月18日(水)',characters:'系列商品 / 角色见官方配图',
  specifications:['品番：LAUE-34008 (CD+BD)','曲名页标题为「日々を越えて 」，引号前有空格','デジタルリリース：2026年9月28日(月)～','作詞：カワノユイ　作曲：明くる夜の羊　編曲：明くる夜の羊/大久保友裕','店铺特典没有单独标价，未另建商品'],
  sourceUrl:sources.kanEd.url,sourceName:'公式ポータル · 第3期ED',
  channels:[['公式ポータル 第3期ED',sources.kanEd.url,doc]],
}),item('kantei3',{
  name:'ED主題歌「日々を越えて 」明くる夜の羊 通常盤',category:'音乐 / 影像',manufacturer:'UNIERA',productBrand:'第3期ED主題歌',acquisitionType:'零售周边',
  price:'【通常盤】1,650円（10％税込）/1,500円（税抜）',releaseDate:'CD：2026年11月18日(水)',characters:'系列商品 / 角色见官方配图',
  specifications:['品番：LAUE-4008 (CDのみ)','曲名页标题为「日々を越えて 」，引号前有空格','デジタルリリース：2026年9月28日(月)～','作詞：カワノユイ　作曲：明くる夜の羊　編曲：明くる夜の羊/大久保友裕'],
  sourceUrl:sources.kanEd.url,sourceName:'公式ポータル · 第3期ED',
  channels:[['公式ポータル 第3期ED',sources.kanEd.url,doc]],
}));

const aniplexVol=['https://online.aniplex.co.jp/itemJNmLuqrp01.html','https://online.aniplex.co.jp/itemJNmLuqrp02.html','https://online.aniplex.co.jp/itemJNmLuqrp03.html'];
const saiVolumes=[
  [1,'2027年1月27日（水）','5話（第1話～第5話）','11月8日(日)','ミミ','ANZX-18151','￥29,150（税込）','ANZX-18154','￥18,150（税込）','ANZB-18154','￥14,300（税込）','H 500×W 1,600（㎜）','特典CD（オリジナルサウンドトラックVol.1）','映像特典：予告、ノンクレOP（Ver.1）、ノンクレED','素材:ライクトロンⓇ'],
  [2,'2027年2月24日（水）','4話（第6話～第9話）','12月6日(日)','エルマ','ANZX-18156','￥26,400（税込）','ANZX-18159','￥15,400（税込）','ANZB-18159','￥12,100（税込）',noSize,'特典CD（オリジナルサウンドトラックVol.2）','映像特典：予告、ノンクレOP（Ver.2）',''],
  [3,'2027年3月31日（水）','4話（第10話～第13話）','12月20日(日)','セレナ','ANZX-18161','￥26,400（税込）','ANZX-18164','￥15,400（税込）','ANZB-18164','￥12,100（税込）',noSize,'ミミPETスタンド','映像特典：予告',''],
];
const saiGoods=[];
for(const [volume,date,episodes,reserve,character,specialCode,specialPrice,bdCode,bdPrice,dvdCode,dvdPrice,pillowSize,extra,video,material] of saiVolumes){
  const shared=['描き下ろしスリーブ','原作・リュート書き下ろし小説','ブックレット',extra,video,'※仕様・特典は変更となる可能性がございます。',`収録話数：${episodes}`,`アニプレックスオンライン第${volume}卷三种形态共用一个链接，未再拆库存`];
  const store=aniplexVol[volume-1];
  saiGoods.push(item('saikyo',{
    name:`目覚めたら最強装備と宇宙船持ちだったので、一戸建て目指して傭兵として自由に生きたい ${volume} Blu-ray　${character}抱き枕カバー付き特装版`,
    category:'音乐 / 影像',manufacturer:'官方商品页未标注发行公司',productBrand:'TV动画卷装影像',acquisitionType:'零售周边',
    price:specialPrice,releaseDate:`${date}。页面另写：確実に入手したいお客様は${reserve}までにご予約ください。预约日没有写年份。`,
    size:volume===1?pillowSize:noSize,characters:character,
    specifications:[`品番：${specialCode}`,...shared,volume===1?`抱き枕カバー ${pillowSize}`:`${character}抱き枕カバー。本卷页面没有写尺寸。`,material].filter(Boolean),
    sourceUrl:sources.saiBd.url,sourceName:'TV动画官网 · Blu-ray&DVD',
    channels:[['TV动画官网 Blu-ray&DVD',sources.saiBd.url,doc],[`アニプレックスオンライン 第${volume}卷入口`,store,shop]],
  }));
  saiGoods.push(item('saikyo',{
    name:`目覚めたら最強装備と宇宙船持ちだったので、一戸建て目指して傭兵として自由に生きたい ${volume} Blu-ray　完全生産限定版`,
    category:'音乐 / 影像',manufacturer:'官方商品页未标注发行公司',productBrand:'TV动画卷装影像',acquisitionType:'零售周边',
    price:bdPrice,releaseDate:date,characters:'キャプテン・ヒロ / ミミ / エルマ / セレナ',
    specifications:[`品番：${bdCode}`,...shared],
    sourceUrl:sources.saiBd.url,sourceName:'TV动画官网 · Blu-ray&DVD',
    channels:[['TV动画官网 Blu-ray&DVD',sources.saiBd.url,doc],[`アニプレックスオンライン 第${volume}卷入口`,store,shop]],
  }));
  saiGoods.push(item('saikyo',{
    name:`目覚めたら最強装備と宇宙船持ちだったので、一戸建て目指して傭兵として自由に生きたい ${volume} DVD　完全生産限定版`,
    category:'音乐 / 影像',manufacturer:'官方商品页未标注发行公司',productBrand:'TV动画卷装影像',acquisitionType:'零售周边',
    price:dvdPrice,releaseDate:date,characters:'キャプテン・ヒロ / ミミ / エルマ / セレナ',
    specifications:[`品番：${dvdCode}`,...shared],
    sourceUrl:sources.saiBd.url,sourceName:'TV动画官网 · Blu-ray&DVD',
    channels:[['TV动画官网 Blu-ray&DVD',sources.saiBd.url,doc],[`アニプレックスオンライン 第${volume}卷入口`,store,shop]],
  }));
}
saiGoods.push(item('saikyo',{
  name:'FLOW「UNSTOPPABLE / Sorrow」 VVCL-3000〜1',category:'音乐 / 影像',manufacturer:'SACRA MUSIC / Sony Music Labels',productBrand:'TV动画OP单曲',acquisitionType:'零售周边',
  price:'2,420円(税込)',releaseDate:'先行配信：2026年10月5日（月）。ニューシングル発売日写10月28日（水），该行没有写年份。',characters:'系列商品 / 角色见官方配图',
  specifications:['作詞：KOHSHI ASAKAWA','作曲：TAKESHI ASAKAWA','編曲：FLOW','页面在「期間生産限定盤（CD＋ Blu-ray）」和「※2形態」「※アニメ描きおろしジャケット」之下并列两行，没有再标明哪一行是限定盘'],
  sourceUrl:sources.saiMusic.url,sourceName:'TV动画官网 · MUSIC',
  channels:[['TV动画官网 MUSIC',sources.saiMusic.url,doc],['CD购买链接', 'https://flow.lnk.to/1028_PKG','官方音乐页列出的购买链接（跳转页，未再核对单价）']],
}),item('saikyo',{
  name:'FLOW「Sorrow / UNSTOPPABLE」 VVCL-3002〜3',category:'音乐 / 影像',manufacturer:'SACRA MUSIC / Sony Music Labels',productBrand:'TV动画OP单曲',acquisitionType:'零售周边',
  price:'2,420円(税込)',releaseDate:'与「UNSTOPPABLE / Sorrow」同页并列。ニューシングル発売日写10月28日（水），该行没有写年份。先行配信行写2026年10月5日（月）。',characters:'系列商品 / 角色见官方配图',
  specifications:['页面没有单独写出这一形态的碟片构成','与上一行同属※2形態，未自行判定哪一行是期间生产限定盘'],
  sourceUrl:sources.saiMusic.url,sourceName:'TV动画官网 · MUSIC',
  channels:[['TV动画官网 MUSIC',sources.saiMusic.url,doc],['CD购买链接','https://flow.lnk.to/1028_PKG','官方音乐页列出的购买链接（跳转页，未再核对单价）']],
}),item('saikyo',{
  name:'ASTERISM「MY WAY」コラボレーションEP 初回仕様限定盤',category:'音乐 / 影像',manufacturer:'Sony Music Labels Inc.',productBrand:'TV动画ED所收录EP',acquisitionType:'零售周边',
  price:'来源未标注价格',releaseDate:'先行配信：2026年10月4日（日）。EP発売日写12月2日（水），该行没有写年份。',characters:'系列商品 / 角色见官方配图',
  specifications:['初回仕様限定盤（CD）','紙ジャケット仕様','アニメ絵柄ワイドキャップステッカー付き','全5曲：MY WAY、What’s my life?、GYUTTO!! (w/ Marty Friedman)、Metal Gandhara (w/ Pineapple Express)、MY WAY (Instrumental)','作詞：HAL-CA','作曲・編曲：ASTERISM'],
  sourceUrl:sources.saiMusic.url,sourceName:'TV动画官网 · MUSIC',
  channels:[['TV动画官网 MUSIC',sources.saiMusic.url,doc],['CD购买链接','https://ASTERISM.lnk.to/MY_WAY','官方音乐页列出的购买链接（跳转页，未再核对单价）']],
}));

const targets=[
  {
    key:'kanata',id:'ole-6b00dca43a78',originalTitle:'彼方から',site:sources.kanataHome.url,source:sources.kanataMusic.url,
    label:'来自远方 · 动画官网',
    scope:'核对动画官网首页、ON AIR、音乐页和新闻列表，以及官网链出的乐天特集、白泉社漫画页。音乐页只有OP「逃光行」、ED「光の側で」的曲名和创作信息，没有品番、价格和发售日。新闻列表的静态页面没有条目。乐天特集的静态页面没有单价商品。因此本批没有入库商品。',
    yearSource:sources.kanataOnair.url,yearNote:'动画官网ON AIR记2026年10月4日（日）起于TOKYO MX、ABC电视、WOWOW播出。',
    sources:[sources.kanataHome,sources.kanataOnair,sources.kanataMusic,sources.kanataNews,sources.kanataRakuten,sources.kanataBooks],
    notes:['OP、ED没有编成商品。','白泉社页面是原作漫画，未纳入动画周边。','不是全市场收集。'],
    goods:[],
  },
  {
    key:'inhumans',id:'ole-40a1811c91a8',originalTitle:'ホテル・インヒューマンズ',site:sources.hotelHome.url,source:sources.hotelBd.url,
    label:'异人旅馆 · 动画官网Blu-ray与规格变更公告',
    scope:'登记官网现行Blu-ray BOX与Blu-ray BOXⅡ。2025.09.25公告中的Vol.1、Vol.2已写明発売中止，不另建商品。第2期OP「螺旋」、ED「スイートピー」只有曲名和评论，没有品番、价格和发售日，未编成商品。目录这一条同时覆盖2025年7月开播的第1期和2026年10月开播的第2期，没有另建作品编号。',
    yearSource:sources.hotelNews17.url,yearNote:'2025.06.06新闻记2025年7月6日（日）23时45分起于东京台系列播出。2026.09.08新闻另记第2期2026年10月4日（日）23时45分起播出。目录年份仍保留2025。',
    sources:[sources.hotelHome,sources.hotelBd,sources.hotelNews99,sources.hotelNews70,sources.hotelNews71,sources.hotelNews17,sources.hotelNews78,sources.hotelNews87,sources.hotelNews86],
    notes:['BOXⅡ的发售日在商品页和新闻中不一致，两条原文都保留。','乐天活动页的「11年」「12年」按原文保留。','早期预约截止日期在HTML注释中，未写入可见规格。'],
    goods:hotelGoods,
  },
  {
    key:'seihantai',id:'ole-1221f7d90dca',originalTitle:'正反対な君と僕',site:sources.seiHome.url,source:sources.seiBd1.url,
    label:'相反的你和我 · 松竹动画官网',
    scope:'目录只有一条2026年作品。官网首页把2026年1月的播出和7月起的第2期写在同一作品下，因此第1至第4卷Blu-ray都记在这条编号下；第3、4卷页面自己写了「2期」。GOODS索引的静态HTML只有分页、没有单品和价格。永旺快闪新闻没有单品和价格，给出的两则详情链接返回404。店铺特典未拆成商品。',
    yearSource:sources.seiHome.url,yearNote:'官网首页写2026年1月起播出，第2期7月起播出。ON AIR表只写7月5日より毎週日曜午後5時，没有再写年份。',
    sources:[sources.seiHome,sources.seiOnair,sources.seiMusic,sources.seiGoods,sources.seiBd1,sources.seiBd2,sources.seiBd3,sources.seiBd4,sources.seiOst,sources.seiPopup,sources.seiEvent],
    notes:['音乐页的主题歌没有品番和价格，未单列。','原声Vol.02只有配信公告，价格标为未标注。','GOODS页按脚本渲染处理，没有拆SKU。'],
    goods:seiGoods,
  },
  {
    key:'kantei3',id:'ole-49a13e022683',originalTitle:'転生貴族、鑑定スキルで成り上がる 第3期',site:sources.kanHome.url,source:sources.kanBd.url,
    label:'转生贵族凭鉴定技能扭转人生 第三季 · 官方门户与V-STORAGE',
    scope:'只登记标明第3期的Blu-ray BOX、第3期OP两形态、第3期ED两形态，以及2026.9.17 V-STORAGE稿里已标价的6条THEキャラ系列。第1期、第2期影像和更早话数的抽选没有并入。GOODS列表、MINI SOF协作和店铺特典没有单价或没有单品名，未拆成商品。',
    yearSource:sources.kanVGoods.url,yearNote:'V-STORAGE 2026.9.17稿写第3期于9月27日（日）深夜00时00分起在CBC/TBS系开播；该句没有再写年份，稿件日期为2026.9.17。官网ON AIR只列每周时间。',
    sources:[sources.kanHome,sources.kanOnair,sources.kanBd,sources.kanOp,sources.kanEd,sources.kanGoods,sources.kanBonus,sources.kanMini,sources.kanVGoods,sources.kanVBd],
    notes:['动画盘价格节点的税込与税抜按原文保留。','目录稿一处把同一品番写成第2期，与第3期标题并存。','官网与目录稿的分辨率写法不同，两处并存。','THEキャラ的「各」没有拆成未列名的单款。'],
    goods:kanteiGoods,
  },
  {
    key:'saikyo',id:'ole-8833513bff5a',originalTitle:'目覚めたら最強装備と宇宙船持ちだったので、一戸建て目指して傭兵として自由に生きたい',site:sources.saiHome.url,source:sources.saiBd.url,
    label:'一觉醒来坐拥神装和飞船 · 动画官网影像与音乐页',
    scope:'登记官网Blu-ray&DVD第1至第3卷的特装版、完全生产限定版Blu-ray和DVD，以及音乐页上两行已标价单曲和未标价的EP。抱枕尺寸只在第1卷特装版写了H 500×W 1,600（㎜），没有套用到第2、3卷。店铺特典和三种形态共用的商店链接没有再拆库存。异世界三作合作新闻没有商品单价。',
    yearSource:sources.saiNews.url,yearNote:'2026.09.15官方新闻更新播出信息，TOKYO MX为10月4日より每周日曜21:30。正文没有再写年份。ON AIR页同样只写10月4日（日）。',
    sources:[sources.saiHome,sources.saiOnair,sources.saiBd,sources.saiMusic,sources.saiNews,sources.saiCollab],
    notes:['CD发售日「10月28日（水）」「12月2日（水）」没有写年份，未补成2026年。','两行FLOW单曲都放在期间生产限定盘标题下，未自行指定哪一行是限定盘。','EP没有价格。','第1卷店铺共通特典和各店特典没有单独标价，未另建商品。'],
    goods:saiGoods,
  },
];

const context={window:{}};
vm.runInNewContext(await readFile(resolve(root,'data/catalog-data.js'),'utf8'),context);
const catalog=context.window.ANIME_CATALOG;
const originalIds=catalog.items.map(work=>work.id);
assert.equal(catalog.items.length,1427);
const protectedIds=['ole-ce2cf196c30e','ole-12b781269ea2','ole-73acd87f49ee','ole-b5f3972beab5','ole-cb17d1062ff3','ole-91ad750080fb','ole-861abb65641d','ole-227a3dd6adab'];
const before=new Map(protectedIds.map(id=>{
  const work=catalog.items.find(row=>row.id===id);
  assert(work);
  return [id,JSON.stringify(work.merch??null)];
}));
assert.equal(JSON.parse(before.get('ole-ce2cf196c30e')).length,1464);
assert.equal(JSON.parse(before.get('ole-12b781269ea2')).length,27);
assert.equal(before.get('ole-227a3dd6adab'),'null');
const tally=(items,key)=>items.reduce((out,row)=>(out[row[key]]=(out[row[key]]||0)+1,out),{});
for(const target of targets){
  assert(!protectedIds.includes(target.id));
  const work=catalog.items.find(row=>row.id===target.id);
  assert(work&&work.name);
  const old=work.merch||[];
  assert(old.every(row=>row.addedInBatch===batch),'只合并本批已追加的记录');
  if(target.goods.length){
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
    work.goodsLibrary=true;
    work.goodsExport=`data/chronology-${target.key}-products.csv`;
    work.researchReportUrl='reports/chronology-latest-6-10.html';
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
  }else{
    assert.equal(old.length,0);
    delete work.merch;
  }
  work.originalTitle=target.originalTitle;
  work.retrievedAt=checkedAt;
  work.officialSiteUrl=target.site;
  work.goodsSourceUrl=target.source;
  work.goodsSourceLabel=target.label;
  work.goodsResearchScope=target.scope;
  work.yearSources=[{url:target.yearSource,note:target.yearNote,checkedAt}];
}
assert.deepEqual(catalog.items.map(work=>work.id),originalIds);
for(const [id,snapshot] of before)assert.equal(JSON.stringify(catalog.items.find(work=>work.id===id).merch??null),snapshot);
assert.equal(catalog.items.find(work=>work.id==='ole-227a3dd6adab').merch,undefined);
const research={
  checkedAt,batch,
  scope:'作品清单「最新」顺序的第6至第10部。只采用无需登录的公开页面。不是这5部的全市场收集，也不是后续作品已调查。',
  works:targets.map(target=>({id:target.id,name:catalog.items.find(work=>work.id===target.id).name,originalTitle:target.originalTitle,products:target.goods.length,limits:target.scope,sources:target.sources,goods:target.goods})),
};
await writeFile(resolve(root,'data/latest-order-batch-2026-11-06-6to10.json'),JSON.stringify(research,null,2)+'\n');
await writeFile(resolve(root,'data/catalog-data.js'),'window.ANIME_CATALOG = '+JSON.stringify(catalog)+';\n');
const progress=JSON.parse(await readFile(resolve(root,'data/chronology-progress.json'),'utf8'));
const done=new Map(targets.map(target=>[target.id,target]));
for(const row of progress.queue){
  if(!done.has(row.id))continue;
  row.yearVerified=true;
  row.stage=done.get(row.id).goods.length?'最新顺序第2批目录调查已入库，仍有待补来源':'最新顺序第2批已核查公开页面，未形成可入库商品';
}
const kanata=targets[0];
progress.latestOrderBatch2={
  checkedAt,order:'作品清单「最新」第6–10部',
  completedWorks:targets.map(target=>target.id),
  products:targets.reduce((sum,target)=>sum+target.goods.length,0),
  unlisted:[{id:kanata.id,name:'来自远方',originalTitle:kanata.originalTitle,reason:kanata.scope,sources:kanata.sources}],
  note:'本批只处理最新顺序第6至第10部。前5部、海贼王和学园默示录没有改写。下一部仍是乱马1/2 第三季。',
};
await writeFile(resolve(root,'data/chronology-progress.json'),JSON.stringify(progress,null,2)+'\n');
console.log(JSON.stringify({status:'imported',products:targets.map(target=>({key:target.key,count:target.goods.length,id:target.id}))},null,2));
