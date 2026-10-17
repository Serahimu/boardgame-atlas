'use strict';
/* Private data stays in this browser. Public catalog data is never mutated. */
window.AtlasPersonal = (() => {
 const KEY='atlas-personal-v1', esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let db={version:1,items:{},lists:[],budget:0,currency:'EUR'}, games=[], active=null, dialog;
 try {const saved=JSON.parse(localStorage.getItem(KEY));if(saved?.version===1&&saved.items)db={...db,...saved}}catch{}
 const features=[];
 function id(g){return g.stableId||g.uid||'item:'+encodeURIComponent([g.bggid||g.url||'',g.name,g.kind,g.edition||'',g.version||''].join('|'))}
 function record(g){const key=id(g);return db.items[key]||{id:key,name:g.name,publisher:g.publisher||'',statuses:[],lists:[],plays:[]}}
 function save(g,patch){const key=id(g), next={...record(g),...patch,updatedAt:new Date().toISOString()};const copy={...db,items:{...db.items,[key]:next}};localStorage.setItem(KEY,JSON.stringify(copy));db=copy;document.dispatchEvent(new CustomEvent('atlas:personal-change',{detail:{id:key,record:next}}));return next}
 function persist(){localStorage.setItem(KEY,JSON.stringify(db))}
 function input(name,label,type='text',value='',attrs=''){return `<label>${label}<input name="${name}" type="${type}" value="${esc(value)}" ${attrs}></label>`}
 function select(name,label,values,value=''){return `<label>${label}<select name="${name}">${values.map(v=>`<option value="${esc(v)}" ${v===value?'selected':''}>${esc(v||'未設定')}</option>`).join('')}</select></label>`}
 function button(action,label){return `<button type="button" data-personal-action="${action}">${label}</button>`}
 function download(name,text,type='application/json'){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
 function message(text){dialog.querySelector('[role=status]').textContent=text}
 function render(){const rows=Object.values(db.items);dialog.querySelector('.personal-content').innerHTML=`<h2>我的桌遊工具</h2><p>私人資料僅儲存在此瀏覽器，請定期匯出備份。跨裝置請使用 JSON 備份移轉。</p><div class="personal-toolbar">${features.filter(f=>f.toolbar).map(f=>f.toolbar()).join('')}</div><div class="personal-summary">${features.filter(f=>f.summary).map(f=>f.summary(rows)).join('')}</div><label>搜尋個人項目<input type="search" data-personal-search placeholder="名稱、出版社、清單或狀態"></label><div class="personal-items">${rows.map(r=>`<article data-personal-row="${esc(r.id)}"><label><input type="checkbox" data-personal-select value="${esc(r.id)}">選取</label><h3>${esc(r.name)}</h3><p>${esc(r.publisher)} · ${esc((r.statuses||[]).join('、'))} · ${esc((r.lists||[]).join('、'))}</p>${button('edit:'+encodeURIComponent(r.id),'編輯個人資料')}</article>`).join('')||'<p>從遊戲詳情加入第一款遊戲。</p>'}</div>`}
 function edit(g){active=g;const r=record(g);dialog.querySelector('.personal-content').innerHTML=`<h2>${esc(g.name)} · 個人資料</h2><form class="personal-form">${features.filter(f=>f.form).map(f=>`<fieldset><legend>${f.title}</legend>${f.form(r,g)}</fieldset>`).join('')}<div class="personal-toolbar"><button type="submit">儲存</button>${button('home','返回我的清單')}</div></form>`}
 function open(g){if(g)edit(g);else render();if(!dialog.open)dialog.showModal()}
 function attach(g){const detail=document.getElementById('detail');if(!detail)return;detail.querySelector('.personal-entry')?.remove();const b=document.createElement('button');b.className='personal-entry link';b.textContent='收藏、備註與逛展規劃';b.onclick=()=>open(g);detail.prepend(b)}
 function init(data){games=data;if(dialog)return;dialog=document.createElement('dialog');dialog.className='personal-dialog';dialog.innerHTML='<button class="personal-close" aria-label="關閉個人工具">×</button><div class="personal-content"></div><p role="status" aria-live="polite"></p>';document.body.append(dialog);dialog.querySelector('.personal-close').onclick=()=>dialog.close();const entry=document.createElement('button');entry.className='personal-launch';entry.textContent='我的清單與逛展工具';entry.onclick=()=>open();(document.querySelector('.collections')||document.body).append(entry);
 dialog.addEventListener('submit',e=>{e.preventDefault();try{const fd=new FormData(e.target),patch={};for(const f of features)if(f.read)Object.assign(patch,f.read(fd,record(active)));save(active,patch);message('已儲存在此瀏覽器')}catch(error){message('無法儲存：'+error.message)}});
 dialog.addEventListener('input',e=>{if(e.target.matches('[data-personal-search]')){const q=e.target.value.toLocaleLowerCase();dialog.querySelectorAll('[data-personal-row]').forEach(el=>el.hidden=!el.textContent.toLocaleLowerCase().includes(q))}});
 dialog.addEventListener('click',async e=>{const a=e.target.closest('[data-personal-action]')?.dataset.personalAction;if(!a)return;try{if(a==='home'){render();return}if(a.startsWith('edit:')){const key=decodeURIComponent(a.slice(5));edit(games.find(g=>id(g)===key)||db.items[key]);return}for(const f of features)if(f.action)await f.action(a)}catch(error){message(error.message)}});
 }
 features.push({title:'收藏狀態',form:r=>['已擁有','想玩','想買','已玩','已出售'].map(v=>`<label><input type="checkbox" name="statuses" value="${v}" ${(r.statuses||[]).includes(v)?'checked':''}>${v}</label>`).join('')+'<p>想玩、想買、已玩可並存；已擁有與已出售互斥。</p>',read:fd=>{const statuses=fd.getAll('statuses');if(statuses.includes('已擁有')&&statuses.includes('已出售'))throw Error('已擁有與已出售不能同時選取');return {statuses}}});
 return {init,attach,open,id,record,save,features,esc,input,select,button,download,get state(){return db},get games(){return games},persist,message,render,get dialog(){return dialog}};
})();
document.addEventListener('atlas:ready',e=>AtlasPersonal.init(e.detail.data));
document.addEventListener('atlas:detail',e=>AtlasPersonal.attach(e.detail.game));
if(window.Atlas?.data)AtlasPersonal.init(window.Atlas.data);

{const A=window.AtlasPersonal;A.features.push({title:'自訂清單',form:r=>A.input('lists','清單名稱（逗號分隔）','text',(r.lists||[]).join(', ')),read:fd=>({lists:[...new Set(String(fd.get('lists')||'').split(/[,，]/).map(s=>s.trim()).filter(Boolean))]})});}

{const A=window.AtlasPersonal;A.features.push({title:'私人備註',form:r=>`<label>規則提醒、購買考量與心得<textarea name="note">${A.esc(r.note||'')}</textarea></label>`,read:fd=>({note:String(fd.get('note')||'')})});}

{const A=window.AtlasPersonal;A.features.push({title:'個人評分',form:r=>A.input('rating','我的評分 / 10','number',r.rating??'','min="0" max="10" step="0.1"'),read:fd=>({rating:fd.get('rating')===''?null:Number(fd.get('rating'))})});}

{const A=window.AtlasPersonal;A.features.push({title:'購買優先級',form:r=>A.select('priority','購買優先',['','必買','考慮中','試玩後決定'],r.priority),read:fd=>({priority:fd.get('priority')})});}

{const A=window.AtlasPersonal;A.features.push({title:'批次操作',toolbar:()=>A.button('batch','批次加入清單 / 狀態'),action:a=>{if(a!=='batch')return;const ids=[...A.dialog.querySelectorAll('[data-personal-select]:checked')].map(el=>el.value);if(!ids.length)throw Error('請先勾選要操作的項目');const list=prompt(`已選 ${ids.length} 項，加入哪個清單？（留空不變更）`);if(list===null)return;const status=prompt('加入狀態：已擁有、想玩、想買、已玩、已出售（留空不變更）','');if(status===null)return;if(status&&!['已擁有','想玩','想買','已玩','已出售'].includes(status))throw Error('狀態無效');for(const key of ids){const r=A.state.items[key],g=A.games.find(g=>A.id(g)===key)||r;let statuses=[...(r.statuses||[])];if(status){statuses=statuses.filter(s=>!(status==='已擁有'&&s==='已出售')&&!(status==='已出售'&&s==='已擁有'));statuses=[...new Set([...statuses,status])]}A.save(g,{statuses,lists:list?[...new Set([...(r.lists||[]),list])]:r.lists})}A.render();A.message(`已更新 ${ids.length} 項`)}});}

{const A=window.AtlasPersonal;A.features.push({title:'收藏統計',form:r=>`<label><input type="checkbox" name="sealed" ${r.sealed?'checked':''}>尚未開封</label>`,read:fd=>({sealed:fd.has('sealed')}),summary:rows=>{const owned=rows.filter(r=>(r.statuses||[]).includes('已擁有')),gs=owned.map(r=>A.games.find(g=>A.id(g)===r.id)).filter(Boolean),count=field=>Object.entries(gs.reduce((o,g)=>{const v=String(g[field]||'未提供');o[v]=(o[v]||0)+1;return o},{})).map(([k,v])=>`${A.esc(k)}: ${v}`).join(' · ');return `<section><h3>收藏統計</h3><p>已擁有 ${owned.length} · 未開封 ${owned.filter(r=>r.sealed).length}</p><details><summary>重度 / 人數 / 機制覆蓋</summary><p>重度：${count('weight')}</p><p>玩家：${count('players')}</p><p>機制：${count('mechanism')}</p></details></section>`}});}
