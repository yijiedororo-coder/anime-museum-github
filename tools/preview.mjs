import http from 'node:http';
import {createReadStream,existsSync,statSync} from 'node:fs';
import {resolve,dirname,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../dist');
const port=Number(process.env.PORT||4173);
if(!existsSync(resolve(root,'index.html'))){console.error('请先执行 npm run build');process.exit(1);}
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.csv':'text/csv; charset=utf-8','.md':'text/plain; charset=utf-8','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml','.woff2':'font/woff2'};
http.createServer((req,res)=>{
 if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);res.end();return;}
 let p;try{p=decodeURIComponent(new URL(req.url,'http://localhost').pathname);}catch{res.writeHead(400);res.end();return;}
 let file=resolve(root,'.'+p);
 if(file!==root&&!file.startsWith(root+sep)){res.writeHead(403);res.end();return;}
 if(existsSync(file)&&statSync(file).isDirectory())file=resolve(file,'index.html');
 if(!existsSync(file)||!statSync(file).isFile()){res.writeHead(404,{'Content-Type':'text/html; charset=utf-8'});res.end(req.method==='HEAD'?'':'<h1>未找到页面</h1><a href="/">返回博物馆</a>');return;}
 const ext=file.slice(file.lastIndexOf('.')).toLowerCase();
 res.writeHead(200,{'Content-Type':types[ext]||'application/octet-stream','Cache-Control':'no-store'});
 if(req.method==='HEAD')res.end();else createReadStream(file).pipe(res);
}).listen(port,'127.0.0.1',()=>console.log('本地预览：http://127.0.0.1:'+port+' （按 Ctrl+C 停止）'));
