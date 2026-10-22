import {readFileSync,existsSync} from 'node:fs';
import {resolve,isAbsolute,relative} from 'node:path';
import assert from 'node:assert/strict';
import {root,loadMuseum,orderedWorks,visibleItems} from './load-museum.mjs';
const {context,registry,catalog}=loadMuseum();
const original=catalog.items;
const sameIds=(actual,expected,message)=>{assert.equal(actual.length,expected.length,message);for(let i=0;i<actual.length;i++)assert.equal(actual[i],expected[i],message);};
assert.equal(original.length,1427,'原作品库应保留1427部');
sameIds(registry.sections.filter(section=>section.beforeCatalog).map(section=>section.id),['aobuta-autumn-2026','gakuen-idolmaster'],'既有专题保持在目录之前；新专题不要写 beforeCatalog');
const slots=['idolmaster-shinycolors','idolmaster-millionlive','idolmaster-cinderella','idolmaster-sidem','idolmaster-765','zenless-zone-zero','hololive','idolmaster'];
let hidden=0;
for(const id of slots){
 const section=registry.sections.find(item=>item.id===id);
 assert(section,'缺少专题登记 '+id);
 const bag=context.window[section.global];
 if(bag.placeholder===true){
  assert.equal((bag.items||[]).length,0,id+' 标记为空位时不能带作品条目');
  assert.equal(visibleItems(bag).length,0);
  hidden++;
 }else assert(bag.items?.some(item=>item.id===id),id+' 已填写时应包含同名作品');
}
for(const section of registry.sections){
 const bag=context.window[section.global];
 if(bag.placeholder===true)assert.equal((bag.items||[]).length,0,section.id+' 标记为空位时不能带作品条目');
 else assert(bag.items?.some(item=>item.id===section.id),section.id+' 的数据里要有同名作品');
}
const all=orderedWorks(context,registry);
sameIds(all.slice(0,2).map(work=>work.id),['aobuta-autumn-2026','gakuen-idolmaster'],'既有专题顺序被改变');
sameIds(all.slice(2,2+original.length).map(work=>work.id),original.map(work=>work.id),'原目录顺序被改变');
assert.equal(new Set(all.map(work=>work.id)).size,all.length,'作品编号不可重复');
for(const id of slots){
 const section=registry.sections.find(item=>item.id===id);
 const bag=context.window[section.global];
 if(bag.placeholder===true)assert(!all.some(work=>work.id===id),id+' 空位不应出现在页面');
 else assert(all.some(work=>work.id===id),id+' 已填写时应出现在页面');
}
function local(file){assert(!isAbsolute(file));const full=resolve(root,file),rel=relative(root,full);assert(rel&&!rel.startsWith('..')&&!isAbsolute(rel),'本地资源路径必须位于项目内');assert(existsSync(full),'缺少资源 '+file);}
let products=0,events=0;
for(const work of all){
 for(const record of [work,...work.alternateRecords||[]])local(record.localPoster);
 if(work.merch){
  products+=work.merch.length;assert.equal(new Set(work.merch.map(goods=>goods.id)).size,work.merch.length);
  if(work.collectionReport)assert.equal(work.collectionReport.products,work.merch.length,'周边汇总数量需要同步');
  if(work.chronologyResearch){assert.equal(work.chronologyResearch.products,work.merch.length,'按年份调查数量必须同步');assert(work.goodsExport&&work.researchReportUrl&&work.channelSummary.length);assert(work.chronologyResearch.sources.every(s=>s.url.startsWith('https://')&&s.checkedAtJST&&s.sha256));}
  for(const goods of work.merch){assert(goods.name&&goods.sourceUrl.startsWith('https://'));assert(Array.isArray(goods.channels));if(!goods.image.startsWith('https://'))local(goods.image);for(const channel of goods.channels)assert(channel.url.startsWith('https://'),'渠道必须使用HTTPS');}
 }
 if(work.events){events+=work.events.length;assert.equal(new Set(work.events.map(event=>event.id)).size,work.events.length);for(const event of work.events){assert(event.sourceUrl.startsWith('https://'));for(const key of event.sources)assert(work.eventSources[key]);}}
 if(work.seriesWorks)for(const series of work.seriesWorks)local(series.localPoster);
}
const html=readFileSync(resolve(root,'index.html'),'utf8'),js=readFileSync(resolve(root,'museum.js'),'utf8');
assert(html.includes('data/ip-registry.js')&&html.includes('data/ip-loader.js'),'首页应通过登记表加载专题');
assert(!html.includes('gakumas-data.js')&&!html.includes('aobuta-data.js'),'首页不应再写死专题数据文件');
assert(js.includes('MUSEUM_IP_REGISTRY'),'页面应从登记表收集专题');
const ids=new Set(Array.from((html+'\n'+js).matchAll(/\bid="([^"]+)"/g),match=>match[1]));
for(const match of js.matchAll(/\$\('([^']+)'\)/g))assert(ids.has(match[1]),'缺少交互节点 '+match[1]);
console.log(JSON.stringify({status:'check passed',works:all.length,products,events,sections:registry.sections.length,hidden,localAssets:true}));
