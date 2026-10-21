import { mkdir, readFile, writeFile, copyFile, rm } from 'node:fs/promises';
import { dirname, resolve, relative, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = resolve(root, 'dist');
// Only replace the generated dist folder of this portable checkout.
if (dirname(output) !== root || relative(root, output) !== 'dist') throw new Error('Invalid output folder');
await rm(output, { recursive: true, force: true });
await mkdir(resolve(output, 'data'), { recursive: true });
await mkdir(resolve(output, 'reports'), { recursive: true });
const source = await readFile(resolve(root, 'data/catalog-data.js'), 'utf8');
const context = { window: {} };
vm.runInNewContext(source, context, { timeout: 3000 });
vm.runInNewContext(await readFile(resolve(root, 'data/gakumas-data.js'), 'utf8'), context, { timeout: 3000 });
vm.runInNewContext(await readFile(resolve(root, 'data/aobuta-data.js'), 'utf8'), context, { timeout: 3000 });
const items = [...context.window.ANIME_CATALOG.items, ...context.window.MUSEUM_ADDITIONS.items,...context.window.MUSEUM_EVENTS.items];
const posters = new Set(items.flatMap(item => [item, ...(item.alternateRecords || [])]).map(item => item.localPoster).filter(Boolean));
for (const item of items) for (const goods of item.merch || []) if (!/^https?:/.test(goods.image)) posters.add(goods.image);
for (const asset of posters) {
  const path = resolve(root, asset);
  const location = relative(resolve(root, 'assets'), path);
  if (location.startsWith('..') || isAbsolute(location)) throw new Error('Invalid poster path');
  const target = resolve(output, asset);
  await mkdir(dirname(target), { recursive: true });
  await copyFile(path, target);
}
for (const file of ['museum.js', 'museum.css', 'events.js', 'series.js', 'data/aobuta-products.csv', 'data/aobuta-data.js', 'data/catalog-data.js', 'data/gakumas-data.js', 'data/gakumas-products.csv', 'data/gakumas-collection-report.json', 'data/gakumas-oct20-research.json', 'reports/gakumas-2026-10-20.md']) await copyFile(resolve(root, file), resolve(output, file));
// Build a directly readable report so visitors do not need a Markdown viewer.
const report = await readFile(resolve(root, 'reports/gakumas-2026-10-20.md'), 'utf8');
const escape = value => value.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const inline = value => escape(value).replace(/\[([^\]]+)\]\((https:\/\/[^()\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1 ↗</a>');
let reportBody = '', block = '';
const closeBlock = () => { if (block) reportBody += block === 'table' ? '</tbody></table></div>' : '</ul>'; block = ''; };
for (const line of report.split(/\r?\n/)) {
  if (line.startsWith('|')) {
    if (/^\|[\s:|\-]+\|$/.test(line)) continue;
    const first = block !== 'table';
    if (first) { closeBlock(); reportBody += '<div class="table-scroll"><table><tbody>'; block = 'table'; }
    const tag = first ? 'th' : 'td';
    reportBody += '<tr>' + line.slice(1, -1).split('|').map(cell => `<${tag}>${inline(cell.trim())}</${tag}>`).join('') + '</tr>';
    continue;
  }
  if (line.startsWith('- ')) {
    if (block !== 'list') { closeBlock(); reportBody += '<ul>'; block = 'list'; }
    reportBody += `<li>${inline(line.slice(2))}</li>`;
    continue;
  }
  closeBlock();
  const heading = line.match(/^(#{1,3}) (.*)$/);
  if (heading) reportBody += `<h${heading[1].length}>${inline(heading[2])}</h${heading[1].length}>`;
  else if (line.trim()) reportBody += `<p>${inline(line)}</p>`;
}
closeBlock();
const reportPage = `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>学园偶像大师 · 10月20日完整调查报告</title><style>body{margin:0;color:#243c35;background:#f6f8f3;font:16px/1.8 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:44px 24px 90px}a{color:#20615c;text-underline-offset:4px}nav{border-bottom:1px solid #ccd8ce;padding-bottom:24px}h1{font-size:clamp(28px,4vw,48px);line-height:1.35;margin:48px 0 24px}h2{margin-top:56px}h3{margin-top:36px}.table-scroll{overflow:auto;margin:24px 0}table{border-collapse:collapse;width:100%;font-size:14px;background:#fff}th,td{border:1px solid #d2ddd3;text-align:left;vertical-align:top;padding:12px;min-width:110px}th{background:#deebe0}td:first-child{min-width:220px}p,li{max-width:90ch}</style><main><nav><a href="/?view=canvas#/ip/gakuen-idolmaster/folder/events">← 返回学园偶像大师活动档案</a> · <a href="/?view=canvas#/ip/gakuen-idolmaster/folder/merch">打开完整周边库</a></nav>${reportBody}</main></html>`;
await writeFile(resolve(root, 'reports/gakumas-2026-10-20.html'), reportPage);
await writeFile(resolve(output, 'reports/gakumas-2026-10-20.html'), reportPage);
const html = (await readFile(resolve(root, 'index.html'), 'utf8')).replace(/<a href="index\.before-museum\.html"[^>]*>.*?<\/a>/, '');
await writeFile(resolve(output, 'index.html'), html);
for (const file of ['_headers', '404.html']) await copyFile(resolve(root, 'public', file), resolve(output, file));
await writeFile(resolve(output, 'build-info.json'), JSON.stringify({
  project: 'anime-museum-github',
  repository: 'https://github.com/yijiedororo-coder/anime-museum-github',
  commit: process.env.WORKERS_CI_COMMIT_SHA || process.env.GITHUB_SHA || null,
  builtAtUTC: new Date().toISOString(),
  works: items.length,
  products: items.reduce((total, work) => total + (work.merch?.length || 0), 0),
  events: items.reduce((total, work) => total + (work.events?.length || 0), 0)
}, null, 2) + '\n');
console.log(JSON.stringify({ output, works: items.length, images: posters.size, status: 'build complete' }));
