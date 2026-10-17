'use strict';
(async function () {
const isEssen=document.body.dataset.collection==='essen';
let PAGE_SIZE=48;
document.addEventListener('error',event=>{const img=event.target;if(!(img instanceof HTMLImageElement))return;if(img.closest('.cover')){const fallback=document.createElement('span');fallback.className='placeholder';fallback.textContent=img.alt.replace(/ (?:封面|出版社圖片)$/,'');const label=document.createElement('small');label.textContent=img.alt.includes('出版社圖片')?'出版社圖片暫時無法載入':'封面暫時無法載入';fallback.append(label);img.replaceWith(fallback)}else if(img.closest('.related,.publisher-heading'))img.hidden=true},true);
async function loadJSON(path){const response=await fetch(path);if(!response.ok)throw new Error(`HTTP ${response.status}`);return response.json()}

const data=(isEssen?await loadJSON('data/essen.json'):(document.getElementById('game-data')?JSON.parse(document.getElementById('game-data').textContent):await loadJSON('data/catalog.json'))), mains=data.filter(d=>d.kind==='主遊戲'), $=id=>document.getElementById(id), esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])), num=v=>v!==null&&v!==''&&Number.isFinite(Number(v))?Number(v):null, val=v=>v===null||v===undefined||v===''?'未提供':String(v), safeurl=v=>/^https:\/\//.test(v||'')?esc(v):'#';
const byId=new Map(data.map(d=>[d.id,d]));
let publisherData=null,publisherLoading=false,publisherFailed=false;
const publisherRecords=new Map(),publishers=new Map();
async function ensurePublishers(){
 if(publisherData||publisherLoading)return;publisherLoading=true;publisherFailed=false;
 try{publisherData=await loadJSON('data/publishers.json');for(const p of publisherData.publishers||[])publisherRecords.set(p.key,p);
 for(const game of data.filter(d=>d.kind!=='佔位項目')){const source=(game.publisher||'').trim();for(const key of publisherData.sources[source]||[source?'unresolved:'+source:'unknown']){if(!publishers.has(key))publishers.set(key,{...(publisherRecords.get(key)||{key,name:source||'出版社未提供'}),games:[]});publishers.get(key).games.push(game)}}
 }catch(error){publisherFailed=true;console.error(error)}finally{publisherLoading=false;if(catalogMode==='publishers')applyRoute()}
}
function publisherNames(game){const source=(game.publisher||'').trim();return (publisherData?.sources[source]||[]).map(key=>publisherRecords.get(key)?.name).filter(Boolean).join('、')||val(game.publisher)}
let catalogMode='games',publisherKey=null;
let directoryState={search:'',page:1,sort:'publisher-count'};
let gameSort=isEssen?'source':'name';
let gameSortOptions=$('sort').innerHTML;
const relationOptions=$('relation').innerHTML;
const defaultSearch=$('search').placeholder;

const children=new Map((isEssen?data:mains).map(m=>[isEssen?m.id:m.name,isEssen?(m.relatedIds||[]).map(id=>byId.get(id)).filter(Boolean):data.filter(d=>d.kind!=='主遊戲'&&d.parent===m.name)]));
const taxonomy=[['mechanismZh','遊戲機制'],['typeZh','遊戲類型'],['categoryZh','分類']];
const selected=Object.fromEntries(taxonomy.map(([key])=>[key,new Set()]));
function terms(d,key){if(d.filterTerms?.[key])return d.filterTerms[key];const raw=d[key];if(!raw||raw.includes('BGG 未')||(key==='categoryZh'&&String(d.category).startsWith('2022 Golden Geek')))return [];return [...new Set(raw.split(/[、；;]/).map(x=>x.trim()).filter(x=>x&&!x.includes('另有')&&!x.includes('摘要未展開')))];}
const taxTerms=new Map(data.map(d=>[d.id,Object.fromEntries(taxonomy.map(([key])=>[key,terms(d,key)]))]));
let restoring=false;
let page=1,view='grid',filtered=[],activeId=null,relTab='全部',lastFocus=null;
try{view=localStorage.getItem('bgg-catalog-view')==='list'?'list':'grid'}catch{}
const numberRange=v=>(String(v||'').match(/\d+/g)||[]).map(Number);
const score=d=>num(d.rating)===null?'未評分':num(d.rating).toFixed(1);
function cover(d){return `<div class="cover">${d.image?`<img src="${d.image}" alt="${esc(d.name)} 封面" loading="lazy">`:`<span class="placeholder">${esc(d.name)}${isEssen?`<small>${d.kind==='佔位項目'?'非具名桌遊項目':'來源暫無封面'}</small>`:''}</span>`}<span class="score">${score(d)}</span></div>`}
function family(d){return children.get(isEssen?d.id:d.name)||[]}
function counts(d){return ['擴充','Promo','新版'].map(k=>{const n=family(d).filter(x=>x.kind===k).length;return n?`<span class="pill">${n} ${k}</span>`:''}).join('')}
const searchIndex=new Map(data.map(d=>[d.id,CatalogCore.index(d)]));
function matches(d,q){return CatalogCore.match(searchIndex.get(d.id),q,$('search-field')?.value||'all')}

const extraFilters=document.createElement('div');extraFilters.innerHTML='<label class="field"><span>目錄範圍</span><select id="catalog-scope"><option value="main">主遊戲</option><option value="all">所有項目</option><option value="擴充">擴充</option><option value="Promo">Promo</option><option value="新版">新版</option></select></label><label class="field"><span>年份／發行狀態（依來源快照）</span><select id="year-filter"><option value="">不限</option><option value="released">來源標示已發行</option><option value="upcoming">來源標示未發行</option><option value="unknown">年份未提供</option></select></label><label class="field"><span>數值缺漏</span><select id="missing-values"><option value="exclude">套用條件時排除缺值</option><option value="include">保留缺值項目</option></select></label><label class="field"><span>同組標籤比對</span><select id="taxonomy-mode"><option value="any">符合任一項</option><option value="all">符合全部</option></select></label><label class="field"><span>排除機制／分類（分號分隔）</span><input id="excluded-tags" placeholder="例如：工人擺放;骰子擲放"></label>';
$('multifilters').before(extraFilters);
const years=[...new Set(data.map(d=>String(d.year)).filter(v=>/^\d{4}$/.test(v)))].sort().reverse();$('year-filter').insertAdjacentHTML('beforeend',years.map(y=>`<option value="${y}">${y}</option>`).join(''));
for(const id of ['catalog-scope','year-filter','missing-values','taxonomy-mode','excluded-tags'])$(id).addEventListener('change',()=>{page=1;render()});
const searchControls=document.createElement('div');searchControls.className='advanced-search';searchControls.innerHTML='<label>搜尋範圍 <select id="search-field"><option value="all">所有欄位（多詞同時符合）</option><option value="name">遊戲名稱／別名</option><option value="designer">設計師</option><option value="publisher">出版社</option><option value="mechanism">機制</option><option value="category">分類</option></select></label><datalist id="search-suggestions"></datalist>';
$('search').closest('label').after(searchControls);
$('search').setAttribute('list','search-suggestions');
$('search-suggestions').innerHTML=[...new Set(data.flatMap(d=>[d.name,d.publisher,...terms(d,'mechanismZh')]).filter(Boolean))].slice(0,6000).map(v=>`<option value="${esc(v)}">`).join('');
$('search-field').onchange=()=>{page=1;render()};
$('sort').insertAdjacentHTML('beforeend','<option value="relevance">搜尋相關度</option>');

gameSortOptions=$('sort').innerHTML;
function initMultiselect(){
 const scope=publisherKey?'本出版社收錄項目':'主遊戲';
 $('multifilters').innerHTML=taxonomy.map(([key,label])=>{
 const counts=new Map();for(const d of catalogGames())for(const term of taxTerms.get(d.id)[key])counts.set(term,(counts.get(term)||0)+1);
 const options=[...counts].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'zh-Hant'));
 return `<details class="multifilter" data-group="${key}"><summary><strong>${label}</strong><span class="selectcount" id="count-${key}">不限</span></summary><div class="multibody"><label><span class="sr">搜尋${label}選項</span><input class="multisearch" type="search" data-option-search="${key}" placeholder="搜尋${label}…" autocomplete="off"></label><div class="multioptions" role="group" aria-label="${label}多選">${options.map(([term,count])=>`<label class="multioption"><input type="checkbox" data-taxonomy="${key}" value="${esc(term)}"><span>${esc(term)}</span><small>${count}</small></label>`).join('')}<p class="multinone" hidden>找不到符合的選項</p></div><div class="multiactions"><span>可複選 · 符合任一項</span><button class="textbtn" type="button" data-clear-group="${key}" aria-label="清除${label}選擇">清除</button></div></div></details>`;
 }).join('')+`<p class="filterhelp">同組符合任一項，不同組須同時符合。<br>依${scope}已收錄的標籤篩選；未列出的資料不推測補入。</p>`;
}
function updateSelection(){for(const [key] of taxonomy){$('count-'+key).textContent=selected[key].size?`已選 ${selected[key].size}`:'不限';document.querySelector(`[data-group="${key}"]`).classList.toggle('has-selection',selected[key].size>0)}}
$('multifilters').addEventListener('change',e=>{const input=e.target;if(!input.matches('[data-taxonomy]'))return;const set=selected[input.dataset.taxonomy];input.checked?set.add(input.value):set.delete(input.value);updateSelection();page=1;render()});
$('multifilters').addEventListener('input',e=>{if(!e.target.matches('[data-option-search]'))return;const group=e.target.closest('.multifilter'),query=e.target.value.trim().toLocaleLowerCase();let visible=0;group.querySelectorAll('.multioption').forEach(label=>{label.hidden=!label.querySelector('input').value.toLocaleLowerCase().includes(query);if(!label.hidden)visible++});group.querySelector('.multinone').hidden=visible>0});
$('multifilters').addEventListener('click',e=>{const button=e.target.closest('[data-clear-group]');if(!button)return;const key=button.dataset.clearGroup;selected[key].clear();document.querySelectorAll(`[data-taxonomy="${key}"]`).forEach(input=>input.checked=false);updateSelection();page=1;render()});
if(isEssen)loadJSON('data/essen-notes.json').then(notes=>{$('source-notes').innerHTML=notes.map(n=>`<div class="datum"><dt>${esc(n.label)}</dt><dd>${esc(n.text)}</dd></div>`).join('')}).catch(()=>{$('source-notes').textContent='整理說明載入失敗，請重新整理或下載 Excel 查看。'});

function catalogGames(){
 return publisherKey?publishers.get(publisherKey).games:($('catalog-scope')?.value==='all'?data:$('catalog-scope')?.value!=='main'?data.filter(d=>d.kind===$('catalog-scope').value):mains);
}
function pageControls(total){
 const totalPages=Math.max(1,Math.ceil(total/PAGE_SIZE));
 page=Math.max(1,Math.min(page,totalPages));
 $('pages').innerHTML=total?`<button data-page="${page-1}" ${page===1?'disabled':''}>上一頁</button><span>第 ${page} / ${totalPages} 頁</span><button data-page="${page+1}" ${page===totalPages?'disabled':''}>下一頁</button>`:'';
}
function renderPublishers(query){
 if(!publisherData){
  $('result').textContent=publisherLoading?'正在載入出版社…':'出版社資料載入失敗';$('pages').innerHTML='';
  $('catalog').innerHTML=`<div class="empty"><h3>${publisherLoading?'正在載入出版社清單…':'無法載入出版社清單'}</h3><p>請重新整理頁面再試一次，或使用本機 HTTP 伺服器預覽。</p><button class="textbtn" data-retry-publishers>重試出版社</button></div>`;return;
 }
 const found=[...publishers.values()].filter(p=>!query||p.name.toLocaleLowerCase().includes(query)||p.games.some(g=>g.name.toLocaleLowerCase().includes(query)));
 found.sort((a,b)=>($('sort').value==='publisher-count'?b.games.length-a.games.length:0)||a.name.localeCompare(b.name,'zh-Hant'));
 $('result').textContent=`${found.length} 家出版社 / 共 ${publishers.size} 家 · 僅顯示本清單收錄項目`;
 pageControls(found.length);
 $('catalog').innerHTML=found.length?found.slice((page-1)*PAGE_SIZE,page*PAGE_SIZE).map(p=>`<button class="card publisher-card" data-logo-background="${p.imageBackground||'light'}" data-publisher="${esc(p.key)}" aria-label="查看 ${esc(p.name)} 的收錄桌遊"><div class="cover">${p.image?`<img src="${esc(p.image)}" alt="${esc(p.name)} 出版社圖片" loading="lazy">`:`<span class="placeholder">${esc(p.name)}<small>${p.status==='unknown'?'資料未提供出版社':'BGG 暫無出版社圖片'}</small></span>`}</div><div><h3>${esc(p.name)}</h3><div class="meta">${p.games.filter(g=>g.kind==='主遊戲').length} 款主遊戲 · ${p.games.length} 項收錄</div></div><div class="cardfoot"><span class="pill">探索收錄桌遊 →</span></div></button>`).join(''):'<div class="empty"><h3>沒有符合條件的出版社</h3><p>試試其他出版社或遊戲名稱。</p><button class="textbtn" data-reset>清除搜尋</button></div>';
}
const sidebar=document.querySelector('.sidebar'),filterButton=document.createElement('button');filterButton.id='filter-toggle';filterButton.className='filter-toggle';filterButton.textContent='篩選條件';filterButton.setAttribute('aria-expanded','false');sidebar.before(filterButton);
const filterActions=document.createElement('div');filterActions.className='filter-actions';filterActions.innerHTML='<button type="button" id="apply-filters">套用條件</button><button type="button" id="close-filters">關閉</button>';sidebar.append(filterActions);
let drawerSnapshot=null;
function closeDrawer(cancel=false){if(cancel&&drawerSnapshot){for(const [id,value] of Object.entries(drawerSnapshot.values))if($(id))$(id).value=value;for(const [key,values] of Object.entries(drawerSnapshot.tax))selected[key]=new Set(values);document.querySelectorAll('[data-taxonomy]').forEach(i=>i.checked=selected[i.dataset.taxonomy].has(i.value));updateSelection();render()}sidebar.classList.remove('drawer-open');sidebar.removeAttribute('role');sidebar.removeAttribute('aria-modal');filterButton.setAttribute('aria-expanded','false');document.body.classList.remove('filters-open');filterButton.focus({preventScroll:true});}
filterButton.onclick=()=>{drawerSnapshot={values:Object.fromEntries([...sidebar.querySelectorAll('select,input[id]')].map(i=>[i.id,i.value])),tax:Object.fromEntries(taxonomy.map(([key])=>[key,[...selected[key]]]))};sidebar.classList.add('drawer-open');sidebar.setAttribute('role','dialog');sidebar.setAttribute('aria-modal','true');filterButton.setAttribute('aria-expanded','true');document.body.classList.add('filters-open');$('reset').focus()};
$('apply-filters').onclick=()=>closeDrawer();$('close-filters').onclick=()=>closeDrawer(true);
sidebar.addEventListener('keydown',e=>{if(!sidebar.classList.contains('drawer-open'))return;if(e.key==='Escape'){e.preventDefault();closeDrawer(true)}if(e.key==='Tab'){const els=[...sidebar.querySelectorAll('button,input,select,summary')].filter(el=>el.getClientRects().length&&!el.disabled),first=els[0],last=els.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}});
const activeFilters=document.createElement('div');activeFilters.id='active-filters';activeFilters.className='active-filters';$('catalog').before(activeFilters);
function renderChips(){
 filterButton.textContent='篩選條件'+(taxonomy.reduce((n,[key])=>n+selected[key].size,0)?` · ${taxonomy.reduce((n,[key])=>n+selected[key].size,0)}`:'');
 const ids=['search','players','time','weight','rating','relation','search-field','year-filter','missing-values','catalog-scope'];
 activeFilters.innerHTML=ids.filter(id=>$(id)?.value&&!['all','main','exclude'].includes($(id).value)).map(id=>`<button data-remove-filter="${id}">${esc($(id).selectedOptions?.[0]?.textContent||$(id).value)} ×</button>`).join('')+taxonomy.flatMap(([key])=>[...selected[key]].map(term=>`<button data-remove-tax="${key}" data-term="${esc(term)}">${esc(term)} ×</button>`)).join('');
 if(activeFilters.children.length)activeFilters.insertAdjacentHTML('beforeend','<button data-reset>清除全部</button>');
}
activeFilters.onclick=e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.removeFilter){$(b.dataset.removeFilter).value=b.dataset.removeFilter==='search-field'?'all':b.dataset.removeFilter==='catalog-scope'?'main':b.dataset.removeFilter==='missing-values'?'exclude':'';}if(b.dataset.removeTax){selected[b.dataset.removeTax].delete(b.dataset.term);document.querySelectorAll('[data-taxonomy]').forEach(i=>i.checked=selected[i.dataset.taxonomy].has(i.value));updateSelection()}page=1;render()};
function render(){
 renderChips();
 if(!restoring)saveRoute();
 const directory=catalogMode==='publishers'&&!publisherKey;
 const query=$('search').value.trim().toLocaleLowerCase();
 $('catalog').className='catalog'+(view==='list'?' list':'');
 $('grid').setAttribute('aria-pressed',view==='grid');$('list').setAttribute('aria-pressed',view==='list');
 if(directory){renderPublishers(query);return;}
 const candidates=publisherKey?catalogGames():($('relation').value==='佔位項目'?data.filter(d=>d.kind==='佔位項目'):catalogGames());
 filtered=candidates.filter(d=>{
  if(taxonomy.some(([key])=>selected[key].size&&!([...selected[key]][$('taxonomy-mode').value==='all'?'every':'some'](term=>(taxTerms.get(d.id)?.[key]||[]).includes(term)))))return false;
  const exclusions=CatalogCore.normalize($('excluded-tags').value).split(/[;；]/).map(x=>x.trim()).filter(Boolean);
  if(exclusions.some(term=>taxonomy.some(([key])=>taxTerms.get(d.id)[key].some(t=>CatalogCore.normalize(t)===term))))return false;
  const releaseStatus=d.releaseInfo?.status;const yr=$('year-filter').value;if(yr==='unknown'&&/^\d{4}$/.test(String(d.year)))return false;if(/^\d{4}$/.test(yr)&&String(d.year)!==yr)return false;
  if(yr==='upcoming'&&releaseStatus!=='upcoming'&&!/未發行|未上市/.test(d.edition||''))return false;if(yr==='released'&&(!/^\d{4}$/.test(String(d.year))||releaseStatus==='upcoming'||/未發行|未上市/.test(d.edition||'')))return false;
  const missing=$('missing-values').value==='include';
  const p=numberRange(d.players),t=numberRange(d.time),w=num(d.weight),r=num(d.rating),want=Number($('players').value);
  if(want&&!(missing&&!p.length)&&(!p.length||(want===6?Math.max(...p)<6:!(want>=p[0]&&want<=p[p.length-1]))))return false;
  if($('time').value&&!(missing&&!t.length)&&(!t.length||($('time').value==='long'?Math.max(...t)<=120:Math.max(...t)>Number($('time').value))))return false;
  if($('weight').value&&!(missing&&w===null)&&(w===null||!({light:w<2,medium:w>=2&&w<3,heavy:w>=3&&w<4,expert:w>=4&&w<=5}[$('weight').value])))return false;
  if($('rating').value&&!(missing&&r===null)&&(r===null||r<Number($('rating').value)))return false;
  if($('relation').value&&(publisherKey?d.kind!==$('relation').value:$('relation').value!=='佔位項目'&&!family(d).some(x=>x.kind===$('relation').value)))return false;
  return !query||matches(d,query)||family(d).some(x=>matches(x,query));
 });
 const sort=$('sort').value;
 filtered.sort((a,b)=>{const n=(d,key,missing)=>num(d[key])??missing;return (sort==='relevance'?CatalogCore.relevance(searchIndex.get(b.id),query)-CatalogCore.relevance(searchIndex.get(a.id),query):sort==='source'?(num(a.sourceOrder)??999999)-(num(b.sourceOrder)??999999):sort==='rating'?n(b,'rating',-1)-n(a,'rating',-1):sort==='year'?n(b,'year',-1)-n(a,'year',-1):sort==='weight'?n(a,'weight',99)-n(b,'weight',99):sort==='relations'?family(b).length-family(a).length:0)||a.name.localeCompare(b.name,'en')});
 $('result').textContent=publisherKey?`${filtered.length} / ${candidates.length} 項收錄桌遊`:`${filtered.length} 款${$('relation').value==='佔位項目'?'佔位項目':'主遊戲'} / 共 ${mains.length} 款主遊戲`;
 pageControls(filtered.length);
 $('catalog').innerHTML=filtered.length?filtered.slice((page-1)*PAGE_SIZE,page*PAGE_SIZE).map(d=>`<button class="card" data-open="${d.id}" aria-label="查看 ${esc(d.name)} 詳情">${cover(d)}<div><h3>${esc(d.name)}</h3><div class="meta">${esc(val(d.year))} · ${esc(val(d.players).replace(/ Players?/g,''))} 人<br>${esc(val(d.time))} · 重度 ${num(d.weight)===null?'未提供':num(d.weight).toFixed(2)}</div></div><div class="cardfoot">${publisherKey?`<span class="pill">${esc(d.kind)}</span>`:''}${view==='list'?`<span class="pill">BGG ${score(d)}</span>`:''}${counts(d)}${query?`<span class="pill match">${matches(d,query)?Object.entries(searchIndex.get(d.id)).filter(([,v])=>CatalogCore.match({text:v},query)).map(([k])=>({name:'名稱',designer:'設計師',publisher:'出版社',mechanism:'機制',category:'分類'}[k])).join('、')||'多欄位':'相關項目'}符合搜尋</span>`:''}</div></button>`).join(''):'<div class="empty"><h3>沒有符合條件的遊戲</h3><p>試試其他關鍵字，或重設篩選條件。</p><button class="textbtn" data-reset>清除所有條件</button></div>';
}
const routeFields=['search','players','time','weight','rating','relation','sort','search-field','year-filter','missing-values','catalog-scope','taxonomy-mode','excluded-tags'];
function saveRoute(){const u=new URL(location.href);for(const key of routeFields){const value=$(key)?.value;if(value)u.searchParams.set(key,value);else u.searchParams.delete(key)}for(const [key] of taxonomy){if(selected[key].size)u.searchParams.set(key,JSON.stringify([...selected[key]]));else u.searchParams.delete(key)}u.searchParams.set('page',page);u.searchParams.set('size',PAGE_SIZE);u.searchParams.set('view',view);history.replaceState({...history.state,scroll:window.scrollY},'',u);}
function restoreRoute(){const p=new URLSearchParams(location.search);for(const key of routeFields){if(!p.has(key)||!$(key))continue;const el=$(key),v=p.get(key);if(el.tagName!=='SELECT'||[...el.options].some(o=>o.value===v))el.value=v}for(const [key] of taxonomy){try{const values=JSON.parse(p.get(key)||'[]');if(Array.isArray(values))values.filter(v=>typeof v==='string').forEach(v=>selected[key].add(v))}catch{}}document.querySelectorAll('[data-taxonomy]').forEach(i=>i.checked=selected[i.dataset.taxonomy].has(i.value));updateSelection();page=Math.max(1,Number(p.get('page'))||1);PAGE_SIZE=[24,48,96].includes(Number(p.get('size')))?Number(p.get('size')):48;view=p.get('view')==='list'?'list':view;}
function applyRoute(){
 restoring=true;
 const oldDirectory=catalogMode==='publishers'&&!publisherKey;
 if(oldDirectory)directoryState={search:$('search').value,page,sort:$('sort').value};else gameSort=$('sort').value;
 publisherKey=null;catalogMode=location.hash==='#publishers'||location.hash.startsWith('#publisher=')?'publishers':'games';
 if(catalogMode==='publishers'&&!publisherData&&!publisherLoading&&!publisherFailed)ensurePublishers();
 if(location.hash.startsWith('#publisher=')){
  try{const key=decodeURIComponent(location.hash.slice(11));if(publishers.has(key))publisherKey=key}catch{}
 }
 const directory=catalogMode==='publishers'&&!publisherKey;
 $('modal').close();
 document.querySelector('.workspace').classList.toggle('publisher-directory',directory);
 document.querySelector('.sidebar').hidden=directory;
 document.querySelectorAll('[data-mode]').forEach(button=>button.setAttribute('aria-pressed',button.dataset.mode===catalogMode));
 document.querySelectorAll('.collections a').forEach(a=>{a.href=a.getAttribute('href').split('#')[0]+(catalogMode==='publishers'?'#publishers':'')});
 $('sort').innerHTML=directory?'<option value="publisher-count">收錄項目由多至少</option><option value="name">出版社名稱 A–Z</option>':gameSortOptions;
 $('sort').value=directory?directoryState.sort:gameSort;
 $('relation').innerHTML=publisherKey?'<option value="">所有項目類型</option>'+['主遊戲','擴充','Promo','新版'].map(kind=>`<option>${kind}</option>`).join(''):relationOptions;
 $('relation').previousElementSibling.textContent=publisherKey?'項目類型':'相關內容';
 const tip=document.querySelector('.tip');tip.innerHTML=tip.innerHTML.replace(/依(?:主遊戲|本出版社收錄項目)資料篩選。/,publisherKey?'依本出版社收錄項目資料篩選。':'依主遊戲資料篩選。');
 $('search').placeholder=directory?'搜尋出版社或收錄桌遊…':defaultSearch;$('search-label').textContent=$('search').placeholder.replace(/…$/,'');
 $('catalog-section').setAttribute('aria-label',directory?'出版社目錄':'遊戲目錄');
 const publisher=publisherKey?publishers.get(publisherKey):null;
 $('publisher-context').hidden=!publisher;
 $('publisher-context').innerHTML=publisher?`<button class="back" data-all-publishers>← 返回出版社清單</button><div class="publisher-heading">${publisher.image?`<img class="publisher-logo" data-logo-background="${publisher.imageBackground||'light'}" src="${esc(publisher.image)}" alt="${esc(publisher.name)} 出版社圖片">`:''}<div><div class="micro">PUBLISHER COLLECTION</div><h2>${esc(publisher.name)}</h2><p class="meta">本清單收錄 ${publisher.games.length} 個項目</p></div></div><div class="links">${link(publisher.url,'BGG 出版社頁')}${link(publisher.sourceUrl,'出版社圖片來源')}</div>`:'';
 for(const [key] of taxonomy)selected[key].clear();
 for(const id of ['search','players','time','weight','rating','relation'])$(id).value='';
 initMultiselect();page=directory?directoryState.page:1;
 if(directory)$('search').value=directoryState.search;
 restoreRoute();render();restoring=false;const game=new URLSearchParams(location.search).get('game');if(game){const d=data.find(x=>x.stableId===game||String(x.id)===game);if(d)show(d.id,false,true)}
}
window.addEventListener('hashchange',applyRoute);window.addEventListener('popstate',()=>{applyRoute();requestAnimationFrame(()=>window.scrollTo(0,history.state?.scroll||0))});
document.addEventListener('click',event=>{
 const button=event.target.closest('[data-mode],[data-publisher],[data-all-publishers],[data-reload],[data-retry-publishers]');if(!button)return;
 if(button.hasAttribute('data-mode')){location.hash=button.dataset.mode==='publishers'?'publishers':'';}
 if(button.hasAttribute('data-publisher'))location.hash='publisher='+encodeURIComponent(button.dataset.publisher);
 if(button.hasAttribute('data-all-publishers'))location.hash='publishers';
 if(button.hasAttribute('data-reload'))location.reload();if(button.hasAttribute('data-retry-publishers')){publisherFailed=false;ensurePublishers();render()}
});

function link(url,label,primary=false){return url?`<a class="link${primary?' primary':''}" href="${safeurl(url)}" target="_blank" rel="noopener noreferrer">${label} ↗</a>`:''}
let detailRequest=0;const detailCache=new Map();
async function show(id,keepTab=false,fromRoute=false){const d=data.find(x=>x.id===Number(id)||x.stableId===id);if(!d)return;
const request=++detailRequest;activeId=d.id;
if(d.detailPath&&!d.detailsLoaded){
 if(!$('modal').open){lastFocus=document.activeElement;$('modal').showModal();document.body.style.overflow='hidden'}
 $('detail').innerHTML='<h2 id="detailTitle">正在載入遊戲詳情…</h2>';
 try{if(!detailCache.has(d.detailPath))detailCache.set(d.detailPath,loadJSON(d.detailPath).catch(e=>{detailCache.delete(d.detailPath);throw e}));const shard=await detailCache.get(d.detailPath);if(request!==detailRequest||!$('modal').open)return;Object.assign(d,shard[d.stableId]||{});d.detailsLoaded=true;}catch(error){if(request===detailRequest){$('detail').innerHTML='<h2 id="detailTitle">詳情載入失敗</h2><button id="retry-detail">重試</button>';$('retry-detail').onclick=()=>show(d.id,keepTab,fromRoute)}return}
}
if(!keepTab&&!fromRoute){saveRoute();const u=new URL(location.href);u.searchParams.set('game',d.stableId||d.id);history.pushState({scroll:window.scrollY},'',u)}activeId=d.id;if(!keepTab)relTab='全部';const parent=isEssen?byId.get(d.parentIds?.[0]):mains.find(m=>m.name===d.parent),rels=family(d);$('detail').innerHTML=`${parent?`<button class="back" data-open="${parent.id}">← 返回主遊戲 · ${esc(parent.name)}</button>`:''}<div class="detailhero">${cover(d)}<div><div class="micro">${esc(d.kind)} · ${esc(val(d.year))}</div><h2 id="detailTitle">${esc(d.name)}</h2><div class="meta">${esc(val(d.designer))}<br>${esc(publisherNames(d))}</div><div class="metrics">${[['BGG 評分',score(d)],['玩家人數',val(d.players)],['遊玩時間',val(d.time)],['重度 / 5',num(d.weight)===null?val(d.weight):num(d.weight).toFixed(2)]].map(([k,v])=>`<div class="metric"><span>${k}</span><strong>${esc(v)}</strong></div>`).join('')}</div><div class="links">${link(d.url,'BGG 遊戲頁',true)}${link(d.gallery,'封面圖庫')}${link(d.imageSource,'封面來源')}${link(d.version,'版次來源')}</div></div></div><dl class="detailsgrid">${[['遊戲類型',d.typeZh??d.type],['分類',d.categoryZh??d.category],['遊戲機制',d.mechanismZh??d.mechanism],['設計師',d.designer],['美術設計',d.artist],['出版社（資料收錄）',publisherNames(d)],['採用版次／語言',d.edition],['採用版次 Release Date',d.release],['集資平台（BGG 標示）',d.funding],['所屬主遊戲',d.parent||(d.kind==='主遊戲'?'此項目為主遊戲':'不適用')]].map(([k,v])=>`<div class="datum"><dt>${k}</dt><dd>${esc(val(v))}</dd></div>`).join('')}</dl>${(d.kind==='主遊戲'||rels.length)?`<h3 class="relationhead">探索相關內容 <span class="micro">${rels.length} 項</span></h3><div class="tabs" aria-label="相關內容分類">${['全部','擴充','Promo','新版'].map(k=>`<button data-tab="${k}" aria-pressed="${relTab===k}">${k} ${k==='全部'?rels.length:rels.filter(r=>r.kind===k).length}</button>`).join('')}</div><div class="related">${rels.filter(r=>relTab==='全部'||r.kind===relTab).map(r=>`<button data-open="${r.id}">${r.image?`<img src="${r.image}" alt="" loading="lazy">`:''}<span><strong>${esc(r.name)}</strong><small>${esc(r.kind)} · ${esc(val(r.year))} · BGG ${score(r)}</small></span></button>`).join('')||'<p class="meta">此分類尚無收錄項目。</p>'}</div>`:''}`;if(isEssen){appendEssenDetails(d);loadDocuments(d)}if(!$('modal').open){lastFocus=document.activeElement;$('modal').showModal();document.body.style.overflow='hidden'}if(!keepTab)$('modal').scrollTop=0;document.dispatchEvent(new CustomEvent('atlas:detail',{detail:{game:d}}));}
function reset(){for(const id of ['catalog-scope','year-filter','missing-values','taxonomy-mode','excluded-tags','search-field']){if($(id))$(id).value=({ 'catalog-scope':'main','missing-values':'exclude','taxonomy-mode':'any','search-field':'all'})[id]||'';}for(const [key] of taxonomy)selected[key].clear();document.querySelectorAll('[data-taxonomy]').forEach(input=>input.checked=false);document.querySelectorAll('[data-option-search]').forEach(input=>input.value='');document.querySelectorAll('.multioption').forEach(label=>label.hidden=false);document.querySelectorAll('.multinone').forEach(label=>label.hidden=true);updateSelection();for(const id of ['search','players','time','weight','rating','relation'])$(id).value='';$('sort').value=catalogMode==='publishers'&&!publisherKey?'publisher-count':(isEssen?'source':'name');page=1;render()}
$('stats').innerHTML=[['主遊戲',mains.length],['擴充 & Promo',data.filter(d=>['擴充','Promo'].includes(d.kind)).length],['新版',data.filter(d=>d.kind==='新版').length]].map(([label,n])=>`<div class="stat"><strong>${n}</strong><span>${label}</span></div>`).join('');
let searchTimer,composing=false;function queueSearch(){clearTimeout(searchTimer);if(!composing)searchTimer=setTimeout(()=>{page=1;render()},140)}$('search').addEventListener('compositionstart',()=>{composing=true;clearTimeout(searchTimer)});$('search').addEventListener('compositionend',()=>{composing=false;queueSearch()});$('search').addEventListener('input',queueSearch);for(const id of ['players','time','weight','rating','relation','sort'])$(id).addEventListener('change',()=>{page=1;render()});$('reset').onclick=reset;for(const v of ['grid','list'])$(v).onclick=()=>{view=v;try{localStorage.setItem('bgg-catalog-view',v)}catch{}render()};document.addEventListener('click',e=>{const b=e.target.closest('[data-open],[data-page],[data-tab],[data-reset]');if(!b)return;if(b.hasAttribute('data-open'))show(b.dataset.open);if(b.hasAttribute('data-tab')){relTab=b.dataset.tab;const top=$('modal').scrollTop;show(activeId,true);$('modal').scrollTop=top;$('detail').querySelector(`[data-tab="${relTab}"]`).focus({preventScroll:true})}if(b.hasAttribute('data-page')){page=Number(b.dataset.page);render();$('search').scrollIntoView({block:'start',behavior:'smooth'})}if(b.hasAttribute('data-reset'))reset()});$('modal').querySelector('.close').onclick=()=>$('modal').close();$('modal').addEventListener('click',e=>{if(e.target===$('modal')){const r=$('modal').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('modal').close()}});$('modal').addEventListener('close',()=>{if(!$('modal').open)detailRequest++;document.body.style.overflow='';if(!$('modal').open){const u=new URL(location.href);u.searchParams.delete('game');history.replaceState(history.state,'',u)}lastFocus?.focus({preventScroll:true})});document.addEventListener('keydown',e=>{if(e.key==='/'&&!$('modal').open&&!['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();$('search').focus()}});applyRoute();
window.Atlas={data,show,render,get filtered(){return filtered},getFiltered:()=>filtered,terms,selected,collection:isEssen?'essen':'original',getActive:()=>byId.get(activeId),filter(patch){for(const [k,v] of Object.entries(patch)){if(selected[k]&&Array.isArray(v)){selected[k]=new Set(v);document.querySelectorAll(`[data-taxonomy="${k}"]`).forEach(i=>i.checked=selected[k].has(i.value));updateSelection()}else if($(k))$(k).value=v}page=1;render()}};
document.dispatchEvent(new CustomEvent('atlas:ready',{detail:{data,dataset:isEssen?'essen':'catalog'}}));

function appendEssenDetails(d){
 const fields=[['Type（原文）',d.type],['Category（原文）',d.category],['Mechanism（原文）',d.mechanism],['文件清單摘要',d.documentSummary],['文件查找結果',d.documentStatus],['原清單序號',d.sourceOrder],['BGG ID',d.bggid],['收錄來源',d.source],['官網／集資查找頁',d.officialSearch],['查核日期',d.checked],['資料備註',d.notes],['主遊戲 BGG ID',d.parentBggid]];
 $('detail').insertAdjacentHTML('beforeend',`<h3 class="relationhead">來源與查核資料</h3><dl class="detailsgrid">${fields.map(([k,v])=>`<div class="datum"><dt>${esc(k)}</dt><dd>${/^https:\/\//.test(v||'')?link(v,'開啟來源'):esc(val(v))}</dd></div>`).join('')}</dl>${(d.parentIds||[]).length?`<h3 class="relationhead">所有關聯遊戲</h3><div class="related">${d.parentIds.map(id=>byId.get(id)).filter(Boolean).map(m=>`<button data-open="${m.id}">${esc(m.name)}</button>`).join('')}</div>`:''}<h3 class="relationhead">規則書與相關文件 <span class="micro">${d.documentCount} 份</span></h3><p class="meta">文件語言與來源標示依原始資料呈現。連結開啟來源文件頁，部分下載需要登入 BGG。</p><div class="links">${/^https:\/\//.test(d.priorityDocument||'')?link(d.priorityDocument,'優先文件入口',true):''}</div><div id="documents" aria-live="polite"><p class="meta">${d.documentCount?'正在載入文件…':'此項目沒有收錄文件。'}</p></div>${d.originals?.length?`<details class="source-notes"><summary>原清單對照 · ${d.originals.length} 筆</summary>${d.originals.map(o=>`<dl class="detailsgrid">${[['原清單序號',o.order],['原始項目名稱',o.name],['來源頁碼',o.page],['原始備註',o.notes],['項目類型',o.kind],['主遊戲',o.parent],['文件查找結果',o.documentStatus]].map(([k,v])=>`<div class="datum"><dt>${k}</dt><dd>${esc(val(v))}</dd></div>`).join('')}</dl><div class="links">${link(o.url,'原始 BGG 項目')}</div>`).join('')}</details>`:''}`);
}
const documentCache=new Map();
async function loadDocuments(d){
 if(!d.documentCount)return;
 const shard=Number(d.bggid)%32;
 try{
  if(!documentCache.has(shard))documentCache.set(shard,loadJSON(`data/essen-documents/${shard}.json`).catch(error=>{documentCache.delete(shard);throw error}));
  const records=(await documentCache.get(shard))[d.bggid]||[];
  if(activeId!==d.id)return;
  const container=$('documents');
  if(window.AtlasEnhancements){window.AtlasEnhancements.documents(container,records,d);return}
  container.innerHTML='<label class="search document-search"><span class="sr">搜尋文件名稱、類別或語言</span><input type="search" placeholder="搜尋文件名稱、類別或語言…"></label><p class="meta document-count" role="status"></p><div class="document-list"></div>';
  const draw=()=>{const q=container.querySelector('input').value.trim().toLocaleLowerCase();const found=records.filter(r=>Object.values(r).join(' ').toLocaleLowerCase().includes(q));container.querySelector('.document-count').textContent=`${found.length} / ${records.length} 份文件`;container.querySelector('.document-list').innerHTML=found.map(r=>`<article class="document"><h4>${esc(r.name)}</h4><p class="meta">${esc(r.category)} · 來源語言：${esc(val(r.language))} · 辨識語言：${esc(val(r.detectedLanguage))}<br>${esc(r.scope)} · ${esc(r.source)} · ${esc(r.date)}</p><p class="meta">${esc(r.notes)}</p><div class="links">${link(r.url,'開啟文件',true)}${link(r.sourceUrl,'來源頁')}</div></article>`).join('')||'<p class="meta">沒有符合的文件。</p>'};
  container.querySelector('input').addEventListener('input',draw);draw();
 }catch{if(activeId===d.id)$('documents').innerHTML='<p>文件載入失敗。</p><button class="textbtn" id="retry-documents">重試</button>';$('retry-documents')?.addEventListener('click',()=>loadDocuments(d));}
}
})().catch(error=>{console.error(error);document.getElementById('catalog').innerHTML='<div class="empty"><h3>清單載入失敗</h3><p>請重新整理頁面再試一次。若是在電腦預覽，請使用本機 HTTP 伺服器開啟。</p><button onclick="location.reload()">重新載入</button></div>'});
