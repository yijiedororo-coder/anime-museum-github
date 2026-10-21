from pathlib import Path
root=Path(__file__).resolve().parent.parent;p=root/'museum.js';s=p.read_text(encoding='utf-8')
def replace(a,b):
    global s
    assert a in s,a[:100]
    s=s.replace(a,b)
replace('  function merchCards(r,folder,rows)', '''  const merchPhotos=g=>[...new Set([g.image,...g.images||[]].filter(Boolean))];
  function makerOverview(r){const report=r.manufacturerResearch;if(!report)return '';return `<section class="maker-overview" aria-label="厂商调查档案"><span class="eyebrow">厂商与景品档案 · ${esc(report.checkedAt)}</span><div class="maker-stats"><div><strong>${report.newProducts}</strong><span>本次补充</span></div><div><strong>${report.prizeProducts}</strong><span>景品档案</span></div><div><strong>${Object.keys(report.manufacturerCounts).length}</strong><span>已核实厂商 / 发行方</span></div></div><nav class="maker-shortcuts" aria-label="快捷浏览"><button data-merch-focus="all" aria-pressed="true">全部档案</button><button data-merch-focus="prize" aria-pressed="false">娃娃机景品</button><button data-merch-focus="new" aria-pressed="false">本次新增 ${report.newProducts}</button></nav><details class="maker-method"><summary>已调查哪些目录？</summary><p>${esc(report.limits)}</p><ul>${report.sourceNotes.map(n=>`<li>${esc(n)}</li>`).join('')}</ul><div class="maker-directory">${Object.entries(report.manufacturerCounts).map(([name,n])=>`<button data-merch-maker="${esc(name)}">${esc(name)} <span>${n}</span></button>`).join('')}</div></details></section>`;}
  function observationDetails(g){const rows=(g.sourceObservations||[]).filter(v=>v.sourceUrl!==g.sourceUrl);if(!rows.length)return '';return `<details class="merch-variants"><summary>其他来源的投放日期与规格 · ${rows.length}</summary><p>厂商出荷、运营商入荷和再登场可能使用不同日期，下面保留各来源记录。</p>${rows.map(v=>`<div class="source-observation"><p>${esc(v.sourceName)} · ${esc(v.releaseDate)}<br>${esc(v.price)} · ${esc(v.size)}</p>${link(v.sourceUrl,'核对这条来源')}</div>`).join('')}</details>`;}
  function merchCards(r,folder,rows)''')
replace('<strong>${esc(g.name)}</strong><span class="merch-price">','<strong>${esc(g.displayName||g.name)}</strong>${g.manufacturer?`<small class="merch-maker">${esc(g.manufacturer)} · ${esc(g.acquisitionType)}</small>`:\'\'}<span class="merch-price">')
replace("category:'全部',limit:48", "category:'全部',focus:'all',limit:48")
replace('资料范围：TV早期目录、四部剧场物贩、青ブタ展、AMNIBUS联名、Good Smile与TAITO。包含历史商品和购买特典，未宣称覆盖全市场。','资料范围：动画官方、展览物贩、厂商直营目录、制作方及运营商景品档案；包含历史商品、限定版本和购买特典。')
replace('</p></div><details class="merch-channel-summary">','</p></div>${makerOverview(r)}<details class="merch-channel-summary">')
replace('<label>渠道<select id="merch-shop">','${r.manufacturerResearch?`<label>厂商 / 发行方<select id="merch-maker">${merchOptions([...new Set(goods.map(g=>g.manufacturer))].sort(),\'全部厂商\')}</select></label><label>获取方式<select id="merch-acquisition">${merchOptions([...new Set(goods.map(g=>g.acquisitionType))],\'全部方式\')}</select></label>`:\'\'}<label>渠道<select id="merch-shop">')
replace('download>下载完整商品资料表 CSV ↗</a><nav','download>下载完整商品资料表 CSV ↗</a>${r.manufacturerResearch?\'<button class="pill merch-reset" data-merch-reset>清除筛选</button>\':\'\'}<nav')
replace("q=($('merch-query')?.value", "focus=merchBrowse.focus,maker=$('merch-maker')?.value,acquisition=$('merch-acquisition')?.value,q=($('merch-query')?.value")
replace("+' '+g.category).toLowerCase()", "+' '+g.category+' '+(g.manufacturer||'')+' '+(g.productBrand||'')+' '+(g.acquisitionType||'')+' '+(g.variant||'')).toLowerCase()")
replace("&&(!shop||g.channels.some(c=>c.name===shop))", "&&(!shop||g.channels.some(c=>c.name===shop))&&(!maker||g.manufacturer===maker)&&(!acquisition||g.acquisitionType===acquisition)&&(!focus||focus==='all'||focus==='prize'&&g.acquisitionType==='娃娃机景品'||focus==='new'&&g.addedInBatch===r.manufacturerResearch?.batch)")
replace("document.querySelectorAll('[data-merch-filter]').forEach", "document.querySelectorAll('[data-merch-focus]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.merchFocus===focus)));document.querySelectorAll('[data-merch-filter]').forEach")
replace("['merch-idol','merch-type','merch-shop']", "['merch-idol','merch-type','merch-shop','merch-maker','merch-acquisition']")
replace('</button><span class="eyebrow">${esc(g.category)} / 商品资料', '</button>${merchPhotos(g).length>1?`<nav class="merch-gallery" aria-label="商品图片">${merchPhotos(g).map((u,i)=>`<button data-merch-photo="${i}" aria-pressed="${i===0}" aria-label="查看商品图 ${i+1}"><img src="${esc(u)}" alt="商品图 ${i+1}" loading="lazy" referrerpolicy="no-referrer"></button>`).join(\'\')}</nav>`:\'\'}<span class="eyebrow">${esc(g.category)} / 商品资料')
replace("[['角色',g.characters],['原始类型'", "[['厂商 / 发行方',g.manufacturer],['品牌',g.productBrand],['获取方式',g.acquisitionType],['款式',g.variant],['角色',g.characters],['原始类型'")
replace("${g.originalName?`<details", "${observationDetails(g)}${g.originalName?`<details")
replace("    const merchImage=e.target.closest('[data-merch-image]');", '''    const photo=e.target.closest('[data-merch-photo]');if(photo){const src=merchPhotos(route.file)[Number(photo.dataset.merchPhoto)];document.querySelector('.merch-photo img').src=src;document.querySelectorAll('[data-merch-photo]').forEach(b=>b.setAttribute('aria-pressed',String(b===photo)));return;}
    const focus=e.target.closest('[data-merch-focus]');if(focus){merchBrowse.focus=focus.dataset.merchFocus;updateMerch();return;}
    const maker=e.target.closest('[data-merch-maker]');if(maker){$('merch-maker').value=maker.dataset.merchMaker;updateMerch();return;}
    if(e.target.closest('[data-merch-reset]')){for(const id of ['merch-query','merch-idol','merch-type','merch-shop','merch-maker','merch-acquisition'])if($(id))$(id).value='';merchBrowse.category='全部';merchBrowse.focus='all';updateMerch();return;}
    const merchImage=e.target.closest('[data-merch-image]');''')
replace("viewerFiles=[{name:route.file.name,url:route.file.image}];viewerIndex=0", "viewerFiles=merchPhotos(route.file).map((url,i)=>({name:route.file.name+' · '+(i+1),url}));viewerIndex=Math.max(0,viewerFiles.findIndex(v=>v.url===merchImage.querySelector('img').getAttribute('src')))")
p.write_text(s,encoding='utf-8')
