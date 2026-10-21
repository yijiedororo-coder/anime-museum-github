import {readFileSync,existsSync} from 'node:fs';
import {resolve,dirname,isAbsolute,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const context={window:{}};
for(const name of ['catalog-data','gakumas-data','aobuta-data'])vm.runInNewContext(readFileSync(resolve(root,'data',name+'.js'),'utf8'),context,{timeout:10000});
const original=context.window.ANIME_CATALOG.items,gakumas=context.window.MUSEUM_ADDITIONS.items,aobuta=context.window.MUSEUM_EVENTS.items;
assert.equal(original.length,1427,'原作品库应保留1427部');
const all=[...original,...gakumas,...aobuta];
assert.equal(new Set(all.map(w=>w.id)).size,all.length,'作品编号不可重复');
function local(file){assert(!isAbsolute(file));const full=resolve(root,file),r=relative(root,full);assert(r&&!r.startsWith('..')&&!isAbsolute(r),'本地资源路径必须位于项目内');assert(existsSync(full),'缺少资源 '+file);}
let products=0,events=0;
for(const work of all){
 for(const record of [work,...work.alternateRecords||[]])local(record.localPoster);
 if(work.merch){
  products+=work.merch.length;assert.equal(new Set(work.merch.map(g=>g.id)).size,work.merch.length);
  if(work.collectionReport)assert.equal(work.collectionReport.products,work.merch.length,'周边汇总数量需要同步');
  for(const g of work.merch){assert(g.name&&g.sourceUrl.startsWith('https://'));assert(Array.isArray(g.channels));if(!g.image.startsWith('https://'))local(g.image);for(const c of g.channels)assert(c.url.startsWith('https://'),'渠道必须使用HTTPS');}
 }
 if(work.events){events+=work.events.length;assert.equal(new Set(work.events.map(e=>e.id)).size,work.events.length);for(const e of work.events){assert(e.sourceUrl.startsWith('https://'));for(const k of e.sources)assert(work.eventSources[k]);}}
 if(work.seriesWorks)for(const w of work.seriesWorks)local(w.localPoster);
}
const html=readFileSync(resolve(root,'index.html'),'utf8'),js=readFileSync(resolve(root,'museum.js'),'utf8');
const ids=new Set(Array.from((html+'\n'+js).matchAll(/\bid="([^"]+)"/g),m=>m[1]));
for(const m of js.matchAll(/\$\('([^']+)'\)/g))assert(ids.has(m[1]),'缺少交互节点 '+m[1]);
console.log(JSON.stringify({status:'check passed',works:all.length,products,events,localAssets:true}));
