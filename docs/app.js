'use strict';
(async function () {
const datasets=(await loadJSON('data/datasets.json')).datasets;
const datasetConfig=datasets.find(config=>config.collection===document.body.dataset.collection);
if(!datasetConfig)throw new Error('Unknown collection');
const isEssen=datasetConfig.parser==='essen';
const updatesLink=document.createElement('a');updatesLink.href='updates.html';updatesLink.textContent='資料版本與更新';document.querySelector('footer').append(updatesLink);
let PAGE_SIZE=48,previousPageSize=48;
document.addEventListener('error',event=>{const img=event.target;if(!(img instanceof HTMLImageElement))return;if(img.matches('.designer-photo')){const fallback=img.parentElement.querySelector('.designer-fallback');fallback.hidden=false;fallback.querySelector('.micro').textContent='照片暫時無法載入';img.remove();return}if(img.closest('.cover')){const fallback=document.createElement('span');fallback.className='placeholder';fallback.textContent=img.alt.replace(/ (?:封面|出版社圖片)$/,'');const label=document.createElement('small');label.textContent=img.alt.includes('出版社圖片')?'出版社圖片暫時無法載入':'封面暫時無法載入';fallback.append(label);img.replaceWith(fallback)}else if(img.closest('.related,.publisher-heading'))img.hidden=true},true);
async function loadJSON(path){const response=await fetch(path);if(!response.ok)throw new Error(`HTTP ${response.status}`);return response.json()}

const data=(document.getElementById('game-data')?JSON.parse(document.getElementById('game-data').textContent):await loadJSON(datasetConfig.listPath)), mains=data.filter(d=>d.kind==='主遊戲'), $=id=>document.getElementById(id), esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])), num=v=>v!==null&&v!==''&&Number.isFinite(Number(v))?Number(v):null, val=v=>v===null||v===undefined||v===''?'未提供':String(v), safeurl=v=>/^https:\/\//.test(v||'')?esc(v):'#';
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
const designers=CatalogCore.buildDesigners(data);
let designerData=null,designerLoading=false,designerFailed=false;
async function ensureDesigners(){
 if(designerData||designerLoading)return;designerLoading=true;designerFailed=false;
 try{const source=await loadJSON('data/designers.json');designerData=source.designers||source}
 catch(error){designerFailed=true;console.error(error)}
 finally{designerLoading=false;if(catalogMode==='designers'){renderDesignerContext();render()}}
}
function designerRecord(person){return designerData?.[person.key]||{}}
function designerPortrait(person){const record=designerRecord(person);return `<div class="cover designer-cover">${record.image?`<img class="designer-photo" src="${esc(record.image)}" alt="${esc(person.name)} 設計師照片" loading="lazy">`:''}<span class="designer-fallback" ${record.image?'hidden':''}><span aria-hidden="true" class="designer-initials">${esc(person.name.split(/\s+/).filter(Boolean).map(part=>part[0]).slice(0,2).join(''))}</span><span class="micro">${designerLoading?'照片載入中':designerFailed?'照片暫時無法載入':'BGG 尚無可確認照片'}</span></span></div>`}
function renderDesignerContext(){
 const designer=designerKey?designers.get(designerKey):null;
 $('designer-context').hidden=!designer;
 if(!designer){$('designer-context').innerHTML='';return}
 const record=designerRecord(designer);
 $('designer-context').innerHTML=`<button class="back" data-all-designers>← 返回設計師清單</button><div class="designer-heading">${designerPortrait(designer)}<div><div class="micro">DESIGNER COLLECTION</div><h2>${esc(designer.name)}</h2><p class="meta">本清單收錄 ${designer.games.filter(game=>game.kind==='主遊戲').length} 款主遊戲 · ${designer.games.length} 個項目。共同設計的作品會分別歸類；依來源姓名分組。</p></div></div><div class="links">${link(record.bggUrl,'BGG 設計師頁')}${link(record.sourceUrl,'設計師照片來源')}</div>`;
}
let catalogMode='games',publisherKey=null,designerKey=null;
const directoryStates={publishers:{search:'',page:1,sort:'publisher-count'},designers:{search:'',page:1,sort:'designer-count'}};
function currentCollection(){return designerKey?designers.get(designerKey):publisherKey?publishers.get(publisherKey):null}
function isDirectory(){return catalogMode==='publishers'&&!publisherKey||catalogMode==='designers'&&!designerKey}

let gameSort=isEssen?'source':'name';
let gameSortOptions=$('sort').innerHTML;
const relationOptions=$('relation').innerHTML;
const defaultSearch=$('search').placeholder;

const children=new Map(data.map(d=>[d.id,(d.relatedIds||[]).map(id=>byId.get(id)).filter(Boolean)]));
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
function copyNameButton(d){return `<button type="button" class="copy-name" data-copy-name="${d.id}" aria-label="複製 ${esc(d.name)} 的名稱" title="複製桌遊名稱" aria-live="polite">複製</button>`}
async function copyGameName(button){
 const game=byId.get(Number(button.dataset.copyName));if(!game)return;
 const fallback=()=>{const previous=document.activeElement,input=document.createElement('textarea');input.value=game.name;input.setAttribute('readonly','');input.style.cssText='position:fixed;opacity:0;pointer-events:none';($('modal').open?$('modal'):document.body).append(input);try{input.select();if(!document.execCommand('copy'))throw new Error('Copy failed')}finally{input.remove();previous?.focus({preventScroll:true})}};
 try{if(navigator.clipboard?.writeText){try{await navigator.clipboard.writeText(game.name)}catch{fallback()}}else fallback();button.textContent='已複製';button.setAttribute('aria-label',`已複製 ${game.name} 的名稱`)}catch{button.textContent='複製失敗';button.setAttribute('aria-label',`複製 ${game.name} 失敗，請重試`)}
 clearTimeout(button.copyResetTimer);button.copyResetTimer=setTimeout(()=>{button.textContent='複製';button.setAttribute('aria-label',`複製 ${game.name} 的名稱`)},1800);
}
document.addEventListener('click',event=>{const button=event.target.closest('[data-copy-name]');if(button){event.preventDefault();event.stopPropagation();copyGameName(button)}});
function family(d){return children.get(d.id)||[]}
function counts(d){return ['擴充','Promo','新版'].map(k=>{const n=family(d).filter(x=>x.kind===k).length;return n?`<span class="pill">${n} ${k}</span>`:''}).join('')}
const searchIndex=new Map(data.map(d=>[d.id,CatalogCore.index(d)]));
function matches(d,q){return CatalogCore.match(searchIndex.get(d.id),q,$('search-field')?.value||'all')}

const extraFilters=document.createElement('div');extraFilters.innerHTML='<label class="field"><span>目錄範圍</span><select id="catalog-scope"><option value="main">主遊戲</option><option value="all">所有項目</option><option value="擴充">擴充</option><option value="Promo">Promo</option><option value="新版">新版</option></select></label><label class="field"><span>年份／發行狀態（依來源快照）</span><select id="year-filter"><option value="">不限</option><option value="released">來源標示已發行</option><option value="upcoming">來源標示未發行</option><option value="unknown">年份未提供</option></select></label><label class="field"><span>數值缺漏</span><select id="missing-values"><option value="exclude">套用條件時排除缺值</option><option value="include">保留缺值項目</option></select></label><label class="field"><span>同組標籤比對</span><select id="taxonomy-mode"><option value="any">符合任一項</option><option value="all">符合全部</option></select></label><label class="field"><span>排除機制／分類（分號分隔）</span><input id="excluded-tags" placeholder="例如：工人擺放;骰子擲放"></label>';
$('multifilters').before(extraFilters);
const years=[...new Set(data.map(d=>String(d.year)).filter(v=>/^\d{4}$/.test(v)))].sort().reverse();$('year-filter').insertAdjacentHTML('beforeend',years.map(y=>`<option value="${y}">${y}</option>`).join(''));
for(const id of ['catalog-scope','year-filter','missing-values','taxonomy-mode','excluded-tags'])$(id).addEventListener('change',()=>{page=1;render()});
let documentFacets=null,documentFacetLoading=null;
const docFacetBox=document.createElement('div');docFacetBox.innerHTML='<label class="field"><span>規則文件條件</span><select id="document-category"><option value="">不限文件</option><option>規則書</option><option>玩家輔助卡</option><option>勘誤</option><option>單人規則</option><option>其他</option></select></label><label class="field"><span>文件語言</span><select id="document-language"><option value="">不限語言</option><option value="traditional">繁體中文</option><option value="simplified">簡體中文</option><option value="english">英文</option></select></label><p id="document-facet-status" role="status"></p>';$('multifilters').before(docFacetBox);
async function ensureDocumentFacets(){if(documentFacets)return;if(!documentFacetLoading)documentFacetLoading=loadJSON('data/document-facets.json').then(index=>{documentFacets=index;$('document-facet-status').textContent='原收藏文件未完整盤點；以下依已查核文件篩選。'}).catch(()=>{$('document-facet-status').innerHTML='文件條件載入失敗。<button id="retry-facets">重試</button>';$('retry-facets').onclick=()=>{documentFacetLoading=null;ensureDocumentFacets().then(render)}});await documentFacetLoading;}
for(const id of ['document-category','document-language'])$(id).onchange=async()=>{await ensureDocumentFacets();page=1;render()};
const personalFilters=document.createElement('div');personalFilters.innerHTML='<label class="field"><span>個人收藏狀態</span><select id="personal-state"><option value="">不限</option>'+['已擁有','想玩','想買','已玩','已出售'].map(s=>`<option>${s}</option>`).join('')+'</select></label><label class="field"><span>排除個人狀態</span><select id="exclude-personal"><option value="">不排除</option>'+['已擁有','想玩','想買','已玩','已出售'].map(s=>`<option>${s}</option>`).join('')+'</select></label>';$('multifilters').before(personalFilters);for(const id of ['personal-state','exclude-personal'])$(id).onchange=()=>{page=1;render()};document.addEventListener('atlas:personal-change',()=>render());
const searchControls=document.createElement('div');searchControls.className='advanced-search';searchControls.innerHTML='<label>搜尋範圍 <select id="search-field"><option value="all">所有欄位（多詞同時符合）</option><option value="name">遊戲名稱／別名</option><option value="designer">設計師</option><option value="publisher">出版社</option><option value="mechanism">機制</option><option value="category">分類</option></select></label><datalist id="search-suggestions"></datalist>';
$('search').closest('label').after(searchControls);
$('search').setAttribute('list','search-suggestions');
$('search-suggestions').innerHTML=[...new Set(data.flatMap(d=>[d.name,d.publisher,...terms(d,'mechanismZh')]).filter(Boolean))].slice(0,6000).map(v=>`<option value="${esc(v)}">`).join('');
$('search-field').onchange=()=>{page=1;render()};
$('sort').insertAdjacentHTML('beforeend','<option value="relevance">搜尋相關度</option>');

gameSortOptions=$('sort').innerHTML;
function initMultiselect(){
 const scope=designerKey?'本設計師收錄項目':publisherKey?'本出版社收錄項目':'主遊戲';
 $('multifilters').innerHTML=taxonomy.map(([key,label])=>{
 const counts=new Map();for(const d of catalogGames())for(const term of taxTerms.get(d.id)[key])counts.set(term,(counts.get(term)||0)+1);
 const options=[...counts].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'zh-Hant'));
 return `<details class="multifilter" data-group="${key}"><summary><strong>${label}</strong><span class="selectcount" id="count-${key}">不限</span></summary><div class="multibody"><label><span class="sr">搜尋${label}選項</span><input class="multisearch" type="search" data-option-search="${key}" placeholder="搜尋${label}…" autocomplete="off"></label><div class="multioptions" role="group" aria-label="${label}多選">${options.map(([term,count])=>`<label class="multioption"><input type="checkbox" data-taxonomy="${key}" value="${esc(term)}"><span>${esc(term)}</span><small>${count}</small></label>`).join('')}<p class="multinone" hidden>找不到符合的選項</p></div><div class="multiactions"><span>可複選 · 符合任一項</span><button class="textbtn" type="button" data-clear-group="${key}" aria-label="清除${label}選擇">清除</button></div></div></details>`;
 }).join('')+`<p class="filterhelp">同組可選任一／全部；數量排除本組條件計算，不同組須同時符合。<br>依${scope}已收錄的標籤篩選；未列出的資料不推測補入。</p>`;
}
function updateSelection(){for(const [key] of taxonomy){$('count-'+key).textContent=selected[key].size?`已選 ${selected[key].size}`:'不限';document.querySelector(`[data-group="${key}"]`).classList.toggle('has-selection',selected[key].size>0)}}
$('multifilters').addEventListener('change',e=>{const input=e.target;if(!input.matches('[data-taxonomy]'))return;const set=selected[input.dataset.taxonomy];input.checked?set.add(input.value):set.delete(input.value);updateSelection();page=1;render()});
$('multifilters').addEventListener('input',e=>{if(!e.target.matches('[data-option-search]'))return;const group=e.target.closest('.multifilter'),query=e.target.value.trim().toLocaleLowerCase();let visible=0;group.querySelectorAll('.multioption').forEach(label=>{label.hidden=!label.querySelector('input').value.toLocaleLowerCase().includes(query);if(!label.hidden)visible++});group.querySelector('.multinone').hidden=visible>0});
$('multifilters').addEventListener('click',e=>{const button=e.target.closest('[data-clear-group]');if(!button)return;const key=button.dataset.clearGroup;selected[key].clear();document.querySelectorAll(`[data-taxonomy="${key}"]`).forEach(input=>input.checked=false);updateSelection();page=1;render()});
if(isEssen)loadJSON(datasetConfig.notesPath).then(notes=>{$('source-notes').innerHTML=notes.map(n=>`<div class="datum"><dt>${esc(n.label)}</dt><dd>${esc(n.text)}</dd></div>`).join('')}).catch(()=>{$('source-notes').textContent='整理說明載入失敗，請重新整理或下載 Excel 查看。'});

function catalogGames(){
 return currentCollection()?currentCollection().games:($('catalog-scope')?.value==='all'?data:$('catalog-scope')?.value!=='main'?data.filter(d=>d.kind===$('catalog-scope').value):mains);
}
function pageControls(total){
 if(PAGE_SIZE==='all'){page=1;$('pages').innerHTML=total?`<span>顯示全部 ${total} 項</span><button data-show-all aria-pressed="true">恢復分頁</button>`:'';return;}
 const totalPages=Math.max(1,Math.ceil(total/PAGE_SIZE));
 page=Math.max(1,Math.min(page,totalPages));
 $('pages').innerHTML=total?`<button data-page="${page-1}" ${page===1?'disabled':''}>上一頁</button><label>第 <input id="page-jump" aria-label="跳至頁碼" type="number" min="1" max="${totalPages}" value="${page}"> / ${totalPages} 頁</label><button data-page="${page+1}" ${page===totalPages?'disabled':''}>下一頁</button><button data-show-all aria-pressed="false">顯示全部</button>`:'';if($('page-jump'))$('page-jump').onchange=()=>{page=Math.max(1,Math.min(totalPages,Number($('page-jump').value)||1));render();$('catalog-section').focus({preventScroll:true})};
}
function pageItems(items){return PAGE_SIZE==='all'?items:items.slice((page-1)*PAGE_SIZE,page*PAGE_SIZE);}
function renderPublishers(query){
 if(!publisherData){
  $('result').textContent=publisherLoading?'正在載入出版社…':'出版社資料載入失敗';$('pages').innerHTML='';
  $('catalog').innerHTML=`<div class="empty"><h3>${publisherLoading?'正在載入出版社清單…':'無法載入出版社清單'}</h3><p>請重新整理頁面再試一次，或使用本機 HTTP 伺服器預覽。</p><button class="textbtn" data-retry-publishers>重試出版社</button></div>`;return;
 }
 const found=[...publishers.values()].filter(p=>!query||p.name.toLocaleLowerCase().includes(query)||p.games.some(g=>g.name.toLocaleLowerCase().includes(query)));
 found.sort((a,b)=>($('sort').value==='publisher-count'?b.games.length-a.games.length:0)||a.name.localeCompare(b.name,'zh-Hant'));
 $('result').textContent=`${found.length} 家出版社 / 共 ${publishers.size} 家 · 僅顯示本清單收錄項目`;
 pageControls(found.length);if(!restoring)saveRoute();
 $('catalog').innerHTML=found.length?pageItems(found).map(p=>`<button class="card publisher-card" data-logo-background="${p.imageBackground||'light'}" data-publisher="${esc(p.key)}" aria-label="查看 ${esc(p.name)} 的收錄桌遊"><div class="cover">${p.image?`<img src="${esc(p.image)}" alt="${esc(p.name)} 出版社圖片" loading="lazy">`:`<span class="placeholder">${esc(p.name)}<small>${p.status==='unknown'?'資料未提供出版社':'BGG 暫無出版社圖片'}</small></span>`}</div><div><h3>${esc(p.name)}</h3><div class="meta">${p.games.filter(g=>g.kind==='主遊戲').length} 款主遊戲 · ${p.games.length} 項收錄</div></div><div class="cardfoot"><span class="pill">探索收錄桌遊 →</span></div></button>`).join(''):'<div class="empty"><h3>沒有符合條件的出版社</h3><p>試試其他出版社或遊戲名稱。</p><button class="textbtn" data-reset>清除搜尋</button></div>';
}
function renderDesigners(query){
 const found=[...designers.values()].filter(person=>!query||CatalogCore.normalize(person.name).includes(CatalogCore.normalize(query))||person.games.some(game=>CatalogCore.match(searchIndex.get(game.id),query,'name')));
 found.sort((a,b)=>($('sort').value==='designer-count'?b.games.length-a.games.length:0)||a.name.localeCompare(b.name,'en'));
 $('result').textContent=`${found.length} 位設計師 / 共 ${designers.size} 位 · 僅顯示本清單收錄作品`;
 if(designerFailed)$('result').insertAdjacentHTML('beforeend',' · <button class="textbtn" data-retry-designers>重試載入照片</button>');
 pageControls(found.length);if(!restoring)saveRoute();
 $('catalog').innerHTML=found.length?pageItems(found).map(person=>`<button class="card designer-card" data-designer="${esc(person.key)}" aria-label="查看 ${esc(person.name)} 的設計作品">${designerPortrait(person)}<div><h3>${esc(person.name)}</h3><div class="meta">${person.games.filter(game=>game.kind==='主遊戲').length} 款主遊戲 · ${person.games.length} 項收錄</div></div><div class="cardfoot"><span class="pill">探索設計作品 →</span></div></button>`).join(''):'<div class="empty"><h3>沒有符合條件的設計師</h3><p>試試其他設計師姓名或作品名稱。</p><button class="textbtn" data-reset>清除搜尋</button></div>';
}
const sidebar=document.querySelector('.sidebar'),filterButton=document.createElement('button');filterButton.id='filter-toggle';filterButton.className='filter-toggle';filterButton.textContent='篩選條件';filterButton.setAttribute('aria-expanded','false');sidebar.before(filterButton);
const filterActions=document.createElement('div');filterActions.className='filter-actions';filterActions.innerHTML='<button type="button" id="apply-filters">套用條件</button><button type="button" id="close-filters">關閉</button>';sidebar.append(filterActions);
let drawerSnapshot=null;
function closeDrawer(cancel=false){if(cancel&&drawerSnapshot){for(const [id,value] of Object.entries(drawerSnapshot.values))if($(id))$(id).value=value;for(const [key,values] of Object.entries(drawerSnapshot.tax))selected[key]=new Set(values);document.querySelectorAll('[data-taxonomy]').forEach(i=>i.checked=selected[i.dataset.taxonomy].has(i.value));updateSelection();render()}sidebar.classList.remove('drawer-open');sidebar.removeAttribute('role');sidebar.removeAttribute('aria-modal');filterButton.setAttribute('aria-expanded','false');document.body.classList.remove('filters-open');filterButton.focus({preventScroll:true});}
filterButton.onclick=()=>{drawerSnapshot={values:Object.fromEntries([...sidebar.querySelectorAll('select,input[id]')].map(i=>[i.id,i.value])),tax:Object.fromEntries(taxonomy.map(([key])=>[key,[...selected[key]]]))};sidebar.classList.add('drawer-open');sidebar.setAttribute('role','dialog');sidebar.setAttribute('aria-modal','true');filterButton.setAttribute('aria-expanded','true');document.body.classList.add('filters-open');$('reset').focus()};
$('apply-filters').onclick=()=>closeDrawer();$('close-filters').onclick=()=>closeDrawer(true);
sidebar.addEventListener('keydown',e=>{if(!sidebar.classList.contains('drawer-open'))return;if(e.key==='Escape'){e.preventDefault();closeDrawer(true)}if(e.key==='Tab'){const els=[...sidebar.querySelectorAll('button,input,select,summary')].filter(el=>el.getClientRects().length&&!el.disabled),first=els[0],last=els.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}});
const density=document.createElement('label');density.innerHTML='每頁 <select id="page-size"><option>24</option><option selected>48</option><option>96</option><option value="all">全部</option></select> <label><input id="compact-view" type="checkbox"> 精簡</label>';$('sort').closest('.tools').append(density);
try{const saved=localStorage.getItem('atlas-page-size');PAGE_SIZE=saved==='all'?'all':[24,48,96].includes(Number(saved))?Number(saved):48;$('page-size').value=PAGE_SIZE;$('compact-view').checked=localStorage.getItem('atlas-compact')==='true'}catch{}
$('page-size').onchange=()=>{if(PAGE_SIZE!=='all')previousPageSize=PAGE_SIZE;PAGE_SIZE=$('page-size').value==='all'?'all':Number($('page-size').value);page=1;try{localStorage.setItem('atlas-page-size',PAGE_SIZE)}catch{}render()};$('compact-view').onchange=()=>{try{localStorage.setItem('atlas-compact',$('compact-view').checked)}catch{}render()};
let selectionMode=false;
const chosenGames=new Set();
const selectionTools=document.createElement('div');selectionTools.className='selection-tools';
selectionTools.innerHTML='<button type="button" id="selection-mode" aria-pressed="false">啟動選取模式</button><button type="button" id="export-selection" disabled>輸出 BGG 連結清單</button><button type="button" id="clear-selection" disabled>清除選取</button><span id="selection-count" role="status" aria-live="polite">已選 0 項</span><p id="selection-help">啟動後，點擊桌遊項目即可選取或取消選取；跨頁與篩選時保留選取。</p>';
$('catalog').before(selectionTools);
const linkDialog=document.createElement('dialog');linkDialog.className='selection-dialog';linkDialog.setAttribute('aria-labelledby','selection-title');
linkDialog.innerHTML='<div class="modalbar"><h2 id="selection-title">所選 BGG 連結清單</h2><button type="button" class="close" aria-label="關閉連結清單">×</button></div><p id="selection-summary"></p><label for="selection-links">每行一個連結</label><textarea id="selection-links" readonly spellcheck="false"></textarea><button type="button" id="copy-selection">複製全部連結</button><p id="selection-copy-status" role="status" aria-live="polite"></p>';
document.body.append(linkDialog);
linkDialog.querySelector('.close').onclick=()=>linkDialog.close();
linkDialog.addEventListener('click',e=>{if(e.target!==linkDialog)return;const r=linkDialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)linkDialog.close()});
linkDialog.addEventListener('close',()=>{$('export-selection').focus({preventScroll:true})});
function updateGameSelection(){
 $('selection-mode').setAttribute('aria-pressed',selectionMode);$('selection-mode').textContent=selectionMode?'退出選取模式':'啟動選取模式';
 $('selection-mode').disabled=isDirectory();
 $('export-selection').disabled=$('clear-selection').disabled=chosenGames.size===0;
 $('selection-count').textContent=`已選 ${chosenGames.size} 項`;
 $('selection-help').textContent=isDirectory()?'進入出版社或設計師的作品清單後，即可選取桌遊項目。':selectionMode?'選取模式已啟動：點擊桌遊項目只會選取或取消選取，不開啟詳情。跨頁與篩選時保留選取。':'啟動後，點擊桌遊項目即可選取或取消選取；跨頁與篩選時保留選取。';
 document.querySelectorAll('.game-card').forEach(card=>{
  const game=byId.get(Number(card.dataset.open)),chosen=chosenGames.has(game.id),button=card.querySelector('.game-name-open');
  card.classList.toggle('selection-active',selectionMode);card.classList.toggle('is-selected',selectionMode&&chosen);
  if(selectionMode){button.setAttribute('aria-pressed',chosen);button.setAttribute('aria-label',`${chosen?'取消選取':'選取'} ${game.name}`)}else{button.removeAttribute('aria-pressed');button.setAttribute('aria-label',`查看 ${game.name} 詳情`)}
  let marker=card.querySelector('.selection-marker');if(selectionMode&&!marker){marker=document.createElement('span');marker.className='selection-marker';marker.setAttribute('aria-hidden','true');card.prepend(marker)}
  if(marker){marker.hidden=!selectionMode;marker.textContent=CatalogCore.bggGameUrl(game)?chosen?'已選取':'選取':'無 BGG 連結';}
 });
}
function toggleGameSelection(id){
 const game=byId.get(Number(id));if(!game)return;
 if(!CatalogCore.bggGameUrl(game)){$('selection-count').textContent='此項目未提供 BGG 遊戲連結，無法選取。';return;}
 chosenGames.has(game.id)?chosenGames.delete(game.id):chosenGames.add(game.id);updateGameSelection();
}
$('selection-mode').onclick=()=>{selectionMode=!selectionMode;updateGameSelection()};
$('clear-selection').onclick=()=>{chosenGames.clear();updateGameSelection()};
document.addEventListener('click',e=>{
 if(!selectionMode)return;const item=e.target.closest('.game-card,[data-open],[data-explore-open]');if(!item)return;
 const id=item.dataset.open??data.find(g=>(g.stableId||String(g.id))===item.dataset.exploreOpen)?.id;
 if(id===undefined)return;e.preventDefault();e.stopImmediatePropagation();toggleGameSelection(id);
},true);
$('export-selection').onclick=()=>{const links=CatalogCore.bggLinks([...chosenGames].map(id=>byId.get(id)));$('selection-links').value=links.join('\n');$('selection-summary').textContent=`已選 ${chosenGames.size} 個項目，共 ${links.length} 個 BGG 連結。相同 BGG 遊戲的不同版次合併為一個連結。`;$('selection-copy-status').textContent='';linkDialog.showModal()};
$('copy-selection').onclick=async()=>{
 const field=$('selection-links');
 const fallback=()=>{field.focus();field.select();if(!document.execCommand('copy'))throw new Error('Copy failed')};
 try{if(navigator.clipboard?.writeText){try{await navigator.clipboard.writeText(field.value)}catch{fallback()}}else fallback();$('selection-copy-status').textContent='已複製全部連結。'}catch{$('selection-copy-status').textContent='無法自動複製，請選取上方連結後手動複製。';field.focus();field.select()}
};
$('pages').addEventListener('click',e=>{if(!e.target.closest('[data-show-all]'))return;if(PAGE_SIZE==='all')PAGE_SIZE=previousPageSize;else{previousPageSize=PAGE_SIZE;PAGE_SIZE='all'}page=1;try{localStorage.setItem('atlas-page-size',PAGE_SIZE)}catch{}render();$('catalog-section').scrollIntoView({block:'start'});});
const activeFilters=document.createElement('div');activeFilters.id='active-filters';activeFilters.className='active-filters';$('catalog').before(activeFilters);
function renderChips(){
 filterButton.textContent='篩選條件'+(taxonomy.reduce((n,[key])=>n+selected[key].size,0)?` · ${taxonomy.reduce((n,[key])=>n+selected[key].size,0)}`:'');
 const ids=['search','players','time','weight','rating','relation','search-field','year-filter','missing-values','catalog-scope','document-category','document-language','personal-state','exclude-personal','excluded-tags','taxonomy-mode'];
 activeFilters.innerHTML=ids.filter(id=>$(id)?.value&&!['all','main','exclude','any'].includes($(id).value)).map(id=>`<button data-remove-filter="${id}">${esc($(id).selectedOptions?.[0]?.textContent||$(id).value)} ×</button>`).join('')+taxonomy.flatMap(([key])=>[...selected[key]].map(term=>`<button data-remove-tax="${key}" data-term="${esc(term)}">${esc(term)} ×</button>`)).join('');
 if(activeFilters.children.length)activeFilters.insertAdjacentHTML('beforeend','<button data-reset>清除全部</button>');
}
activeFilters.onclick=e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.removeFilter){$(b.dataset.removeFilter).value=b.dataset.removeFilter==='search-field'?'all':b.dataset.removeFilter==='taxonomy-mode'?'any':b.dataset.removeFilter==='catalog-scope'?'main':b.dataset.removeFilter==='missing-values'?'exclude':'';}if(b.dataset.removeTax){selected[b.dataset.removeTax].delete(b.dataset.term);document.querySelectorAll('[data-taxonomy]').forEach(i=>i.checked=selected[i.dataset.taxonomy].has(i.value));updateSelection()}page=1;render()};
function render(){
 renderChips();
 updateGameSelection();
 $('page-size').value=PAGE_SIZE;
 if(!restoring)saveRoute();
 const directory=isDirectory();
 const query=$('search').value.trim().toLocaleLowerCase();
 $('catalog').className='catalog'+(view==='list'?' list':'')+($('compact-view').checked?' compact':'');
 $('grid').setAttribute('aria-pressed',view==='grid');$('list').setAttribute('aria-pressed',view==='list');
 if(directory){filtered=[];if(catalogMode==='designers')renderDesigners(query);else renderPublishers(query);return;}
 const candidates=currentCollection()?catalogGames():($('relation').value==='佔位項目'?data.filter(d=>d.kind==='佔位項目'):catalogGames());
 const predicate=(d,skipGroup=null)=>{
  if(taxonomy.some(([key])=>key!==skipGroup&&selected[key].size&&!([...selected[key]][$('taxonomy-mode').value==='all'?'every':'some'](term=>(taxTerms.get(d.id)?.[key]||[]).includes(term)))))return false;
  if($('document-category').value||$('document-language').value){const id=d.bggid||d.url?.match(/boardgame\/(\d+)/)?.[1],facet=documentFacets?.[id];if(!facet)return false;if($('document-category').value&&!facet.categories.includes($('document-category').value))return false;const language=$('document-language').value,patterns={traditional:/繁|Traditional/i,simplified:/簡|Simplified/i,english:/英文|English/i};if(language&&!facet.languages.some(v=>patterns[language].test(v)))return false;}
  const statuses=window.AtlasPersonal?.record(d)?.statuses||[];if($('personal-state').value&&!statuses.includes($('personal-state').value))return false;if($('exclude-personal').value&&statuses.includes($('exclude-personal').value))return false;
  const exclusions=CatalogCore.normalize($('excluded-tags').value).split(/[;；]/).map(x=>x.trim()).filter(Boolean);
  if(exclusions.some(term=>taxonomy.some(([key])=>taxTerms.get(d.id)[key].some(t=>CatalogCore.normalize(t)===term))))return false;
  const releaseStatus=d.releaseInfo?.status;const yr=$('year-filter').value;if(yr==='unknown'&&/^\d{4}$/.test(String(d.year)))return false;if(/^\d{4}$/.test(yr)&&String(d.year)!==yr)return false;
  if(yr==='upcoming'&&!['unreleased','scheduled'].includes(releaseStatus))return false;if(yr==='released'&&releaseStatus!=='released')return false;
  const missing=$('missing-values').value==='include';
  const p=numberRange(d.players),t=numberRange(d.time),w=num(d.weight),r=num(d.rating),want=Number($('players').value);
  if(want&&!(missing&&!p.length)&&(!p.length||(want===6?Math.max(...p)<6:!(want>=p[0]&&want<=p[p.length-1]))))return false;
  if($('time').value&&!(missing&&!t.length)&&(!t.length||($('time').value==='long'?Math.max(...t)<=120:Math.max(...t)>Number($('time').value))))return false;
  if($('weight').value&&!(missing&&w===null)&&(w===null||!({light:w<2,medium:w>=2&&w<3,heavy:w>=3&&w<4,expert:w>=4&&w<=5}[$('weight').value])))return false;
  if($('rating').value&&!(missing&&r===null)&&(r===null||r<Number($('rating').value)))return false;
  if($('relation').value&&(currentCollection()?d.kind!==$('relation').value:$('relation').value!=='佔位項目'&&!family(d).some(x=>x.kind===$('relation').value)))return false;
  return !query||matches(d,query)||family(d).some(x=>matches(x,query)); };
 filtered=candidates.filter(d=>predicate(d));
 for(const [key] of taxonomy){const counts=new Map();for(const d of candidates.filter(d=>predicate(d,key)))for(const term of taxTerms.get(d.id)[key])counts.set(term,(counts.get(term)||0)+1);document.querySelectorAll(`[data-taxonomy="${key}"]`).forEach(input=>{const count=counts.get(input.value)||0;input.closest("label").querySelector("small").textContent=count;input.disabled=!count&&!input.checked;})}

 const sort=$('sort').value;
 filtered.sort((a,b)=>{const n=(d,key,missing)=>num(d[key])??missing;return (sort==='relevance'?CatalogCore.relevance(searchIndex.get(b.id),query)-CatalogCore.relevance(searchIndex.get(a.id),query):sort==='source'?(num(a.sourceOrder)??999999)-(num(b.sourceOrder)??999999):sort==='rating'?n(b,'rating',-1)-n(a,'rating',-1):sort==='year'?n(b,'year',-1)-n(a,'year',-1):sort==='weight'?n(a,'weight',99)-n(b,'weight',99):sort==='relations'?family(b).length-family(a).length:0)||a.name.localeCompare(b.name,'en')});
 $('result').textContent=currentCollection()?`${filtered.length} / ${candidates.length} 項收錄桌遊`:`${filtered.length} / ${candidates.length} ${$('catalog-scope').value==='main'?'款主遊戲':'個項目'}`;
 pageControls(filtered.length);if(!restoring)saveRoute();
 $('catalog').innerHTML=filtered.length?pageItems(filtered).map(d=>`<article class="card game-card" data-open="${d.id}">${cover(d)}<div><div class="game-title"><h3><button type="button" class="game-name-open" data-open="${d.id}" aria-label="查看 ${esc(d.name)} 詳情">${esc(d.name)}</button></h3>${copyNameButton(d)}</div>${d.nameZh?`<div class="name-zh">${esc(d.nameZh)}</div>`:""}<div class="meta">${esc(val(d.year))} · ${esc(val(d.players).replace(/ Players?/g,''))} 人<br>${esc(val(d.time))} · 重度 ${num(d.weight)===null?'未提供':num(d.weight).toFixed(2)}</div></div><div class="cardfoot">${currentCollection()?`<span class="pill">${esc(d.kind)}</span>`:''}${view==='list'?`<span class="pill">BGG ${score(d)}</span>`:''}${counts(d)}${query?`<span class="pill match">${matches(d,query)?Object.entries(searchIndex.get(d.id)).filter(([,v])=>CatalogCore.match({text:v},query)).map(([k])=>({name:'名稱',designer:'設計師',publisher:'出版社',mechanism:'機制',category:'分類'}[k])).join('、')||'多欄位':'相關項目'}符合搜尋</span>`:''}</div></article>`).join(''):'<div class="empty"><h3>沒有符合條件的遊戲</h3><p>試試其他關鍵字，或重設篩選條件。</p><button class="textbtn" data-reset>清除所有條件</button></div>';
 updateGameSelection();
}
const routeFields=['search','players','time','weight','rating','relation','sort','search-field','year-filter','missing-values','catalog-scope','taxonomy-mode','excluded-tags','document-category','document-language','personal-state','exclude-personal'];
const routeDefaults=Object.fromEntries(routeFields.map(id=>[id,$(id).value]));
function saveRoute(){const u=new URL(location.href);for(const key of routeFields){const value=$(key)?.value;if(value)u.searchParams.set(key,value);else u.searchParams.delete(key)}for(const [key] of taxonomy){if(selected[key].size)u.searchParams.set(key,JSON.stringify([...selected[key]]));else u.searchParams.delete(key)}u.searchParams.set('page',page);u.searchParams.set('size',PAGE_SIZE);u.searchParams.set('view',view);history.replaceState({...history.state,scroll:window.scrollY},'',u);}
function restoreRoute(){const p=new URLSearchParams(location.search);for(const key of routeFields){if(!p.has(key)||!$(key))continue;const el=$(key),v=p.get(key);if(el.tagName!=='SELECT'||[...el.options].some(o=>o.value===v))el.value=v}for(const [key] of taxonomy){try{const values=JSON.parse(p.get(key)||'[]');if(Array.isArray(values))values.filter(v=>typeof v==='string').forEach(v=>selected[key].add(v))}catch{}}document.querySelectorAll('[data-taxonomy]').forEach(i=>i.checked=selected[i.dataset.taxonomy].has(i.value));updateSelection();if(p.has('page'))page=Math.max(1,Number(p.get('page'))||1);if(p.has('size'))PAGE_SIZE=p.get('size')==='all'?'all':[24,48,96].includes(Number(p.get('size')))?Number(p.get('size')):48;view=p.get('view')==='list'?'list':view;}
let migrationsPromise;
async function restoreGameRoute(game){
 let stable=game;if(/^\d+$/.test(game)){try{migrationsPromise??=loadJSON('data/id-migrations.json').catch(e=>{migrationsPromise=null;throw e});stable=(await migrationsPromise).datasets[datasetConfig.id]?.[game]||game;}catch{$('result').textContent='舊版遊戲網址對照載入失敗，請重新整理重試。';return}}
 if(new URLSearchParams(location.search).get('game')!==game)return;const d=data.find(x=>x.stableId===stable||String(x.id)===stable);if(d)show(d.id,false,true);else $('result').textContent='此遊戲網址未在目前清單中找到，請使用搜尋查找。';
}
function applyRoute(){
 restoring=true;
 if(isDirectory())Object.assign(directoryStates[catalogMode],{search:$('search').value,page,sort:$('sort').value});else if($('sort').value)gameSort=$('sort').value;
 publisherKey=null;designerKey=null;
 catalogMode=location.hash==='#publishers'||location.hash.startsWith('#publisher=')?'publishers':location.hash==='#designers'||location.hash.startsWith('#designer=')?'designers':'games';
 if(catalogMode==='publishers'&&!publisherData&&!publisherLoading&&!publisherFailed)ensurePublishers();
 if(catalogMode==='designers'&&!designerData&&!designerLoading&&!designerFailed)ensureDesigners();
 if(location.hash.startsWith('#publisher=')){try{const key=decodeURIComponent(location.hash.slice(11));if(publishers.has(key))publisherKey=key}catch{}}
 let missingDesigner=false;
 if(location.hash.startsWith('#designer=')){try{const key=decodeURIComponent(location.hash.slice(10));if(designers.has(key))designerKey=key;else missingDesigner=true}catch{missingDesigner=true}}
 const directory=isDirectory(),state=directoryStates[catalogMode];
 $('modal').close();
 document.querySelector('.workspace').classList.toggle('publisher-directory',directory);
 document.querySelector('.sidebar').hidden=directory;filterButton.hidden=directory;document.querySelector('.advanced-search').hidden=directory;activeFilters.hidden=directory;
 document.querySelectorAll('[data-mode]').forEach(button=>button.setAttribute('aria-pressed',button.dataset.mode===catalogMode));
 document.querySelectorAll('.collections a').forEach(a=>{const url=new URL(a.getAttribute('href'),location.href);if(!datasets.some(config=>config.page===url.pathname.split('/').at(-1)))return;url.hash=catalogMode==='games'?'':catalogMode;a.href=url.pathname.split('/').at(-1)+url.hash});
 $('sort').innerHTML=directory?`<option value="${catalogMode==='designers'?'designer-count':'publisher-count'}">收錄項目由多至少</option><option value="name">${catalogMode==='designers'?'設計師姓名':'出版社名稱'} A–Z</option>`:gameSortOptions;
 $('sort').value=directory?state.sort:gameSort;
 for(const id of routeFields)if(id!=='sort')$(id).value=routeDefaults[id];
 $('relation').innerHTML=currentCollection()?'<option value="">所有項目類型</option>'+['主遊戲','擴充','Promo','新版'].map(kind=>`<option>${kind}</option>`).join(''):relationOptions;
 $('relation').previousElementSibling.textContent=currentCollection()?'項目類型':'相關內容';
 $('catalog-scope').closest('.field').hidden=!!currentCollection();
 const scope=designerKey?'本設計師收錄項目':publisherKey?'本出版社收錄項目':'主遊戲';
 const tip=document.querySelector('.tip');tip.innerHTML=tip.innerHTML.replace(/依(?:主遊戲|本出版社收錄項目|本設計師收錄項目)資料篩選。/,`依${scope}資料篩選。`);
 $('search').placeholder=directory?(catalogMode==='designers'?'搜尋設計師或收錄桌遊…':'搜尋出版社或收錄桌遊…'):defaultSearch;
 $('search-label').textContent=$('search').placeholder.replace(/…$/,'');
 $('catalog-section').setAttribute('aria-label',directory?(catalogMode==='designers'?'設計師目錄':'出版社目錄'):'遊戲目錄');
 const publisher=publisherKey?publishers.get(publisherKey):null;
 $('publisher-context').hidden=!publisher;
 $('publisher-context').innerHTML=publisher?`<button class="back" data-all-publishers>← 返回出版社清單</button><div class="publisher-heading">${publisher.image?`<img class="publisher-logo" data-logo-background="${publisher.imageBackground||'light'}" src="${esc(publisher.image)}" alt="${esc(publisher.name)} 出版社圖片">`:''}<div><div class="micro">PUBLISHER COLLECTION</div><h2>${esc(publisher.name)}</h2><p class="meta">本清單收錄 ${publisher.games.length} 個項目</p></div></div><div class="links">${link(publisher.url,'BGG 出版社頁')}${link(publisher.sourceUrl,'出版社圖片來源')}</div>`:'';
 renderDesignerContext();
 for(const [key] of taxonomy)selected[key].clear();
 initMultiselect();page=directory?state.page:1;
 if(directory)$('search').value=state.search;
 restoreRoute();render();if(($('document-category').value||$('document-language').value)&&!documentFacets)ensureDocumentFacets().then(render);restoring=false;
 if(missingDesigner)$('result').textContent='找不到此設計師，已顯示設計師清單。'+$('result').textContent;
 const game=new URLSearchParams(location.search).get('game');if(game)restoreGameRoute(game)
}
function navigateCatalog(hash,returnToDirectory=false){
 saveRoute();if(isDirectory())directoryStates[catalogMode].url=location.href;
 const mode=hash==='designers'?'designers':'publishers';
 const target=returnToDirectory&&directoryStates[mode].url?new URL(directoryStates[mode].url):new URL(location.href);
 if(!returnToDirectory){target.search='';target.searchParams.set('view',view);target.searchParams.set('size',PAGE_SIZE)}
 else if(!directoryStates[mode].url)target.search='';
 target.hash=hash;history.pushState({scroll:window.scrollY},'',target);applyRoute();
}
document.querySelector('.skip-link').addEventListener('click',event=>{event.preventDefault();$('catalog-section').focus();$('catalog-section').scrollIntoView({block:'start'})});
window.addEventListener('hashchange',applyRoute);window.addEventListener('popstate',()=>{applyRoute();requestAnimationFrame(()=>window.scrollTo(0,history.state?.scroll||0))});
document.addEventListener('click',event=>{
 const button=event.target.closest('[data-mode],[data-publisher],[data-designer],[data-all-publishers],[data-all-designers],[data-reload],[data-retry-publishers],[data-retry-designers]');if(!button)return;
 if(button.hasAttribute('data-mode'))navigateCatalog(button.dataset.mode==='games'?'':button.dataset.mode);
 if(button.hasAttribute('data-publisher'))navigateCatalog('publisher='+encodeURIComponent(button.dataset.publisher));
 if(button.hasAttribute('data-designer'))navigateCatalog('designer='+encodeURIComponent(button.dataset.designer));
 if(button.hasAttribute('data-all-publishers'))navigateCatalog('publishers',true);
 if(button.hasAttribute('data-all-designers'))navigateCatalog('designers',true);
 if(button.hasAttribute('data-retry-designers')){ensureDesigners();render()}
 if(button.hasAttribute('data-reload'))location.reload();if(button.hasAttribute('data-retry-publishers')){publisherFailed=false;ensurePublishers();render()}
});

function link(url,label,primary=false){return url?`<a class="link${primary?' primary':''}" href="${safeurl(url)}" target="_blank" rel="noopener noreferrer">${label} ↗</a>`:''}
const detailTrail=[];let detailRequest=0;const detailCache=new Map();
async function show(id,keepTab=false,fromRoute=false){const d=data.find(x=>x.id===Number(id)||x.stableId===id);if(!d)return;if(selectionMode&&!fromRoute){toggleGameSelection(d.id);return;}
if(!keepTab&&activeId!==null&&activeId!==d.id)detailTrail.push(activeId);const request=++detailRequest;activeId=d.id;
if(d.detailPath&&!d.detailsLoaded){
 if(!$('modal').open){lastFocus=document.activeElement;$('modal').showModal();document.body.style.overflow='hidden'}
 $('detail').innerHTML='<h2 id="detailTitle">正在載入遊戲詳情…</h2>';
 try{if(!detailCache.has(d.detailPath))detailCache.set(d.detailPath,loadJSON(d.detailPath).catch(e=>{detailCache.delete(d.detailPath);throw e}));const shard=await detailCache.get(d.detailPath);if(request!==detailRequest||!$('modal').open)return;Object.assign(d,shard[d.stableId]||{});d.detailsLoaded=true;}catch(error){if(request===detailRequest){$('detail').innerHTML='<h2 id="detailTitle">詳情載入失敗</h2><button id="retry-detail">重試</button>';$('retry-detail').onclick=()=>show(d.id,keepTab,fromRoute)}return}
}
if(!keepTab&&!fromRoute){saveRoute();const u=new URL(location.href);u.searchParams.set('game',d.stableId||d.id);history.pushState({scroll:window.scrollY},'',u)}activeId=d.id;if(!keepTab)relTab='全部';const parent=byId.get(d.parentIds?.[0]),rels=family(d);$('detail').innerHTML=`${parent?`<button class="back" data-open="${parent.id}">← 返回主遊戲 · ${esc(parent.name)}</button>`:''}<div class="detailhero">${cover(d)}<div><div class="micro">${esc(d.kind)} · ${esc(val(d.year))}</div><div class="game-title detail-game-title"><h2 id="detailTitle">${esc(d.name)}</h2>${copyNameButton(d)}</div>${d.nameZh?`<p>${esc(d.nameZh)} · ${esc(d.nameZhType||"來源中文名")} ${link(d.nameZhSource,"名稱來源")}</p>`:""}<div class="meta">${esc(val(d.designer))}<br>${esc(publisherNames(d))}</div><div class="metrics">${[['BGG 評分',score(d)],['玩家人數',val(d.players)],['遊玩時間',val(d.time)],['重度 / 5',num(d.weight)===null?val(d.weight):num(d.weight).toFixed(2)]].map(([k,v])=>`<div class="metric"><span>${k}</span><strong>${esc(v)}</strong></div>`).join('')}</div><div class="links">${link(d.url,'BGG 遊戲頁',true)}${link(d.gallery,'封面圖庫')}${link(d.imageSource,'封面來源')}${link(d.version,'版次來源')}</div></div></div><dl class="detailsgrid">${[['遊戲類型',d.typeZh??d.type],['分類',d.categoryZh??d.category],['遊戲機制',d.mechanismZh??d.mechanism],['設計師',d.designer],['美術設計',d.artist],['出版社（資料收錄）',publisherNames(d)],['採用版次／語言',d.edition],['採用版次 Release Date',d.release],['集資平台（BGG 標示）',d.funding],['所屬主遊戲',d.parent||(d.kind==='主遊戲'?'此項目為主遊戲':'不適用')]].map(([k,v])=>`<div class="datum"><dt>${k}</dt><dd>${esc(val(v))}</dd></div>`).join('')}</dl>${(d.kind==='主遊戲'||rels.length)?`<h3 class="relationhead">探索相關內容 <span class="micro">${rels.length} 項</span></h3><div class="tabs" aria-label="相關內容分類">${['全部','擴充','Promo','新版'].map(k=>`<button data-tab="${k}" aria-pressed="${relTab===k}">${k} ${k==='全部'?rels.length:rels.filter(r=>r.kind===k).length}</button>`).join('')}</div><div class="related">${rels.filter(r=>relTab==='全部'||r.kind===relTab).map(r=>`<button data-open="${r.id}">${r.image?`<img src="${r.image}" alt="" loading="lazy">`:''}<span><strong>${esc(r.name)}</strong><small>${esc(r.kind)} · ${esc(val(r.year))} · BGG ${score(r)}</small></span></button>`).join('')||'<p class="meta">此分類尚無收錄項目。</p>'}</div>`:''}`;if(isEssen){appendEssenDetails(d);loadDocuments(d)}if(!$('modal').open){lastFocus=document.activeElement;$('modal').showModal();document.body.style.overflow='hidden'}if(!keepTab)$('modal').scrollTop=0;const pos=filtered.findIndex(x=>x.id===d.id);$('detail').insertAdjacentHTML('afterbegin',`<nav class="detail-navigation" aria-label="詳情導覽"><button data-detail-prev ${pos<=0?'disabled':''}>← 上一款</button><button data-detail-next ${pos<0||pos>=filtered.length-1?'disabled':''}>下一款 →</button><button data-detail-back ${detailTrail.length?'':'disabled'}>返回上一個詳情</button></nav>`);
$('detail').querySelector('[data-detail-prev]').onclick=()=>show(filtered[pos-1]?.id);$('detail').querySelector('[data-detail-next]').onclick=()=>show(filtered[pos+1]?.id);$('detail').querySelector('[data-detail-back]').onclick=()=>{const id=detailTrail.pop();activeId=null;show(id)};
document.dispatchEvent(new CustomEvent('atlas:detail',{detail:{game:d}}));}
function reset(){for(const id of ['catalog-scope','year-filter','missing-values','taxonomy-mode','excluded-tags','search-field','document-category','document-language','personal-state','exclude-personal']){if($(id))$(id).value=({ 'catalog-scope':'main','missing-values':'exclude','taxonomy-mode':'any','search-field':'all'})[id]||'';}for(const [key] of taxonomy)selected[key].clear();document.querySelectorAll('[data-taxonomy]').forEach(input=>input.checked=false);document.querySelectorAll('[data-option-search]').forEach(input=>input.value='');document.querySelectorAll('.multioption').forEach(label=>label.hidden=false);document.querySelectorAll('.multinone').forEach(label=>label.hidden=true);updateSelection();for(const id of ['search','players','time','weight','rating','relation'])$(id).value='';$('sort').value=isDirectory()?(catalogMode==='designers'?'designer-count':'publisher-count'):(isEssen?'source':'name');page=1;render()}
$('stats').innerHTML=[['主遊戲',mains.length],['擴充 & Promo',data.filter(d=>['擴充','Promo'].includes(d.kind)).length],['新版',data.filter(d=>d.kind==='新版').length]].map(([label,n])=>`<div class="stat"><strong>${n}</strong><span>${label}</span></div>`).join('');
let searchTimer,composing=false;function queueSearch(){clearTimeout(searchTimer);if(!composing)searchTimer=setTimeout(()=>{page=1;render()},140)}$('search').addEventListener('compositionstart',()=>{composing=true;clearTimeout(searchTimer)});$('search').addEventListener('compositionend',()=>{composing=false;queueSearch()});$('search').addEventListener('input',queueSearch);for(const id of ['players','time','weight','rating','relation','sort'])$(id).addEventListener('change',()=>{page=1;render()});$('reset').onclick=reset;for(const v of ['grid','list'])$(v).onclick=()=>{view=v;try{localStorage.setItem('bgg-catalog-view',v)}catch{}render()};document.addEventListener('click',e=>{if(e.target.closest('[data-copy-name]'))return;const b=e.target.closest('[data-open],[data-page],[data-tab],[data-reset]');if(!b)return;if(b.hasAttribute('data-open'))show(b.dataset.open);if(b.hasAttribute('data-tab')){relTab=b.dataset.tab;const top=$('modal').scrollTop;show(activeId,true);$('modal').scrollTop=top;$('detail').querySelector(`[data-tab="${relTab}"]`).focus({preventScroll:true})}if(b.hasAttribute('data-page')){page=Number(b.dataset.page);render();$('search').scrollIntoView({block:'start',behavior:'smooth'})}if(b.hasAttribute('data-reset'))reset()});$('modal').querySelector('.close').onclick=()=>$('modal').close();$('modal').addEventListener('click',e=>{if(e.target===$('modal')){const r=$('modal').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('modal').close()}});$('modal').addEventListener('close',()=>{if(!$('modal').open){detailRequest++;detailTrail.length=0;activeId=null;}document.body.style.overflow='';if(!$('modal').open){const u=new URL(location.href);u.searchParams.delete('game');history.replaceState(history.state,'',u)}lastFocus?.focus({preventScroll:true})});document.addEventListener('keydown',e=>{if(e.key==='/'&&!$('modal').open&&!['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();$('search').focus()}});applyRoute();
window.Atlas={data,show,render,get filtered(){return filtered},getFiltered:()=>filtered,terms,selected,collection:datasetConfig.collection,datasetConfig,datasets,getActive:()=>byId.get(activeId),filter(patch){for(const [k,v] of Object.entries(patch)){if(selected[k]&&Array.isArray(v)){selected[k]=new Set(v);document.querySelectorAll(`[data-taxonomy="${k}"]`).forEach(i=>i.checked=selected[k].has(i.value));updateSelection()}else if($(k))$(k).value=v}page=1;render()}};
document.dispatchEvent(new CustomEvent('atlas:ready',{detail:{data,dataset:datasetConfig.id}}));

function appendEssenDetails(d){
 const fields=[['Type（原文）',d.type],['Category（原文）',d.category],['Mechanism（原文）',d.mechanism],['文件清單摘要',d.documentSummary],['文件查找結果',d.documentStatus],['原清單序號',d.sourceOrder],['BGG ID',d.bggid],['收錄來源',d.source],['官網／集資查找頁',d.officialSearch],['查核日期',d.checked],['資料備註',d.notes],['主遊戲 BGG ID',d.parentBggid]];
 $('detail').insertAdjacentHTML('beforeend',`<details class="source-notes"><summary>來源與查核資料</summary><dl class="detailsgrid">${fields.map(([k,v])=>`<div class="datum"><dt>${esc(k)}</dt><dd>${/^https:\/\//.test(v||'')?link(v,'開啟來源'):esc(val(v))}</dd></div>`).join('')}</dl></details>${(d.parentIds||[]).length?`<h3 class="relationhead">所有關聯遊戲</h3><div class="related">${d.parentIds.map(id=>byId.get(id)).filter(Boolean).map(m=>`<button data-open="${m.id}">${esc(m.name)}</button>`).join('')}</div>`:''}<h3 class="relationhead">規則書與相關文件 <span class="micro">${d.documentCount} 份</span></h3><p class="meta">文件語言與來源標示依原始資料呈現。連結開啟來源文件頁，部分下載需要登入 BGG。</p><div class="links">${/^https:\/\//.test(d.priorityDocument||'')?link(d.priorityDocument,'優先文件入口',true):''}</div><div id="documents" aria-live="polite"><p class="meta">${d.documentCount?'正在載入文件…':'此項目沒有收錄文件。'}</p></div>${d.originals?.length?`<details class="source-notes"><summary>原清單對照 · ${d.originals.length} 筆</summary>${d.originals.map(o=>`<dl class="detailsgrid">${[['原清單序號',o.order],['原始項目名稱',o.name],['來源頁碼',o.page],['原始備註',o.notes],['項目類型',o.kind],['主遊戲',o.parent],['文件查找結果',o.documentStatus]].map(([k,v])=>`<div class="datum"><dt>${k}</dt><dd>${esc(val(v))}</dd></div>`).join('')}</dl><div class="links">${link(o.url,'原始 BGG 項目')}</div>`).join('')}</details>`:''}`);
}
const documentCache=new Map();
async function loadDocuments(d){
 if(!d.documentCount)return;
 const shard=Number(d.bggid)%32;
 try{
  if(!documentCache.has(shard))documentCache.set(shard,loadJSON(`${datasetConfig.documentsPath}/${shard}.json`).catch(error=>{documentCache.delete(shard);throw error}));
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
