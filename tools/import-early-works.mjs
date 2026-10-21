// Import today's verified facts, preserving original work order and existing product positions.
import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import assert from 'node:assert/strict';
import vm from 'node:vm';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const research=JSON.parse(await readFile(resolve(root,'data/early-works-research.json'),'utf8'));
const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
assert.equal(research.checkedAt,today,'请先重新调查来源，不能把旧缓存当作当天资料');
assert.equal(research.failures.length,0,'存在来源访问失败，需要人工核查后再导入');
const context={window:{}};
vm.runInNewContext(await readFile(resolve(root,'data/catalog-data.js'),'utf8'),context);
const catalog=context.window.ANIME_CATALOG,originalIds=catalog.items.map(w=>w.id);
assert.equal(catalog.items.length,1427);
const batch=research.checkedAt+'-chronology-first';
const targets=[
  {key:'onepiece',id:'ole-ce2cf196c30e',site:'https://one-piece.com/',source:'https://www.megahobby.jp/products/portraitofpirates/',
   label:'海贼王 · 厂商与官方商店目录',scope:'P.O.P历史目录19页、Banpresto作品目录29页及毛绒商品子页、BANDAI扭蛋、COSPA服饰生活品、麦草商店出张店限定公告。单条记录可以是多款商品系列，尚未穷尽其他厂商、剧场版物贩及二手市场。',
   yearSource:'https://one-piece.com/anime/1/index.html',yearNote:'官方第一集档案标注1999年10月20日播出。'},
  {key:'hotd',id:'ole-12b781269ea2',site:'https://www.nbcuni.co.jp/rondorobe/anime/hotd/',source:'https://www.nbcuni.co.jp/rondorobe/anime/hotd/contents/hp0007/list00000000.html',
   label:'学园默示录 · 动画旧官网与原作出版社',scope:'动画旧官网Blu-ray与DVD六卷分别登记，主题曲、片尾专辑、原声带、游乐场景品、C79联动、制服公告及KADOKAWA原作漫画。历史手办、其他零售商目录与更多特典仍待后续核查。原作漫画单列，不混入动画首播年份。',
   yearSource:'https://group.kadokawa.co.jp/documents/ir/library/pdf_k/report/572.pdf',yearNote:'KADOKAWA当期业务报告记录2010年7月TV动画播出。'},
];
const tally=(items,key)=>items.reduce((out,item)=>(out[item[key]]=(out[item[key]]||0)+1,out),{});
for(const target of targets){
  const work=catalog.items.find(w=>w.id===target.id);assert(work,'作品编号不存在');
  const products=research.goods[target.key];assert(products.length>0);
  const old=work.merch||[],positions=new Map(old.map((g,i)=>[g.id,i]));
  for(const original of products){
    const g=structuredClone(original);
    assert(g.name&&g.sourceUrl.startsWith('https://')&&g.channels.every(c=>c.url.startsWith('https://')));
    if(!g.image){g.image=work.localPoster;g.images=[];g.imagePlaceholder=true;}
    g.characters=charactersFor(g.name,target.key);
    if(positions.has(g.id)){
      const index=positions.get(g.id),previous=old[index];
      const channels=[...previous.channels];
      for(const channel of g.channels){const i=channels.findIndex(c=>c.url===channel.url&&c.name===channel.name);if(i>=0)channels[i]={...channels[i],...channel};else channels.push(channel);}
      old[index]={...previous,...g,channels:channels.filter((c,i,a)=>a.findIndex(v=>v.url===c.url&&v.name===c.name&&v.linkType===c.linkType)===i),images:[...new Set([...(previous.images||[]),...(g.images||[])])]};
    }else{positions.set(g.id,old.length);old.push(g);}
  }
  work.merch=old;work.retrievedAt=research.checkedAt;work.goodsLibrary=true;
  work.officialSiteUrl=target.site;work.goodsSourceUrl=target.source;work.goodsSourceLabel=target.label;
  work.goodsResearchScope=target.scope;work.goodsExport='data/chronology-'+target.key+'-products.csv';
  work.researchReportUrl='reports/chronology-first.html';
  work.yearSources=[{url:target.yearSource,note:target.yearNote,checkedAt:research.checkedAt}];
  const relevant=research.sources.filter(s=>target.key==='hotd'?/nbcuni|kadokawa/.test(s.url):!/nbcuni|kadokawa/.test(s.url));
  work.chronologyResearch={batch,checkedAt:research.checkedAt,products:old.length,sources:relevant,limits:target.scope};
  work.manufacturerResearch={checkedAt:research.checkedAt,batch,newProducts:products.length,totalProducts:old.length,
    prizeProducts:old.filter(g=>g.acquisitionType==='娃娃机景品').length,manufacturerCounts:tally(old,'manufacturer'),
    sourceNotes:[target.scope,'商品页、官方目录、对应店铺查询分别标注；目录引用的外部购买页未逐个核查实时库存。','历史税率、再版日期及未来发售计划按来源保留；未提供的价格、尺寸和日期明确标注。'],limits:target.scope};
  const summary=new Map();
  for(const g of old)for(const channel of g.channels){
    if(!summary.has(channel.name))summary.set(channel.name,{name:channel.name,sourceUrl:channel.url,description:channel.linkType,examples:[]});
    const entry=summary.get(channel.name);if(entry.examples.length<3&&!entry.examples.includes(g.name))entry.examples.push(g.name);
  }
  work.channelSummary=[...summary.values()];
}
function charactersFor(name,key){
  if(key!=='onepiece')return ['小室孝','宮本麗','毒島冴子','高城沙耶','平野耕太','鞠川静香'].filter(n=>name.includes(n)).join('、')||'系列商品 / 角色见官方配图';
  // フィギュア contains the substring ルフィ; it is not evidence of a Luffy product.
  const normalized=name.replace(/フィギュア|ドレスローザ/g,'');
  const characters=[['路飞 / ルフィ','ルフィ','LUFFY'],['索隆 / ゾロ','ゾロ','ZORO'],['娜美 / ナミ','ナミ','NAMI'],['乌索普 / ウソップ','ウソップ','USOPP'],['山治 / サンジ','サンジ','SANJI'],['乔巴 / チョッパー','チョッパー','CHOPPER'],['罗宾 / ロビン','ロビン','ROBIN'],['弗兰奇 / フランキー','フランキー','FRANKY'],['布鲁克 / ブルック','ブルック','BROOK'],['甚平 / ジンベエ','ジンベエ','JINBE'],['艾斯 / エース','エース','ACE'],['萨博 / サボ','サボ','SABO'],['香克斯 / シャンクス','シャンクス','SHANKS'],['罗 / ロー','トラファルガー','LAW'],['基德 / キッド','キッド','KID'],['汉库克 / ハンコック','ハンコック','HANCOCK'],['大和 / ヤマト','ヤマト','YAMATO'],['凯多 / カイドウ','カイドウ','KAIDO'],['巴基 / バギー','バギー','BUGGY'],['鹰眼 / ミホーク','ミホーク','MIHAWK'],['克洛克达尔 / クロコダイル','クロコダイル','CROCODILE'],['佩罗娜 / ペローナ','ペローナ','PERONA'],['波妮 / ボニー','ボニー','BONNEY'],['熊 / くま','バーソロミュー','KUMA'],['卡鲁 / カルー','カルー','KAROO'],['洛基 / ロキ','ロキ','LOKI']];
  return characters.filter(([,jp,en])=>normalized.includes(jp)||new RegExp('\\b'+en+'\\b','i').test(normalized)).map(([label])=>label).join('、')||'系列商品 / 角色见官方配图';
}
const corrections=[
  ['ole-f826d44f7d4c','2017','https://www.b-ch.com/titles/5459/','Bandai Channel第2期作品标签为2017年。'],
  ['ole-b67cffe860a5','2017','https://masamune-tv.com/1st/onair/','动画官网记录第一季2017年1月5日开始播出。'],
  ['ole-5766ccfba813','2017','https://ichijinsha-20th.com/history/','原作出版社年表将TV动画列于2017年7月。'],
  ['ole-ce0b0ad4a998','2017','https://www.sunrise-inc.co.jp/work/topics.php?id=13682','制作公司公告记录2017年8月4日第1话开始配信。'],
  ['ole-35c33d466aa4','2016','https://bangumi.tv/subject/127448/ep','章节档案记录2016年3月10日首播；2016年玄机官方制作特辑交叉核对。'],
];
const yearChanges=[];
for(const [id,year,source,note] of corrections){
  const work=catalog.items.find(w=>w.id===id);assert(work);
  work.originalImportedYear??=work.year;work.year=year;
  work.yearSources=[{url:source,note,checkedAt:research.checkedAt}];
  if(id==='ole-35c33d466aa4')work.yearSources.push({url:'https://www.bilibili.com/video/BV1qs411k7iv/',note:'玄机科技官方账号2016年8月发布制作特辑；该链接不是首播日证据。',checkedAt:research.checkedAt});
  yearChanges.push({id,name:work.name,originalYear:work.originalImportedYear,year,sources:work.yearSources});
}
assert.deepEqual(catalog.items.map(w=>w.id),originalIds,'原作品的编号和顺序不能改变');
await writeFile(resolve(root,'data/catalog-data.js'),'window.ANIME_CATALOG = '+JSON.stringify(catalog)+';\n');
const completed=new Set(targets.map(t=>t.id));
const queue=[...catalog.items].sort((a,b)=>(Number(a.year)||9999)-(Number(b.year)||9999)).map(w=>({id:w.id,name:w.name,catalogYear:w.year,yearVerified:Boolean(w.yearSources),stage:completed.has(w.id)?'首轮目录调查已入库，仍有待补来源':'待调查'}));
await writeFile(resolve(root,'data/chronology-progress.json'),JSON.stringify({checkedAt:research.checkedAt,totalWorks:1427,firstSurveyWorks:2,yearChanges,sourcePages:research.sources.length,queue},null,2)+'\n');
console.log(JSON.stringify({status:'imported',products:targets.map(t=>({work:t.key,count:catalog.items.find(w=>w.id===t.id).merch.length})),yearCorrections:yearChanges.length}));
