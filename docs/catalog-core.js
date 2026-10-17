/* Shared, DOM-free catalog search and URL helpers. */
(function(root){
'use strict';
const fields={name:['name','nameZh','aliases'],designer:['designer'],publisher:['publisher'],mechanism:['mechanism','mechanismZh'],category:['category','categoryZh','type','typeZh']};
const normalize=value=>String(value??'').normalize('NFKD').replace(/\p{M}/gu,'').toLocaleLowerCase().replace(/[‐‑–—-]/g,' ').replace(/\s+/g,' ').trim();
function index(game){return Object.fromEntries(Object.entries(fields).map(([key,keys])=>[key,normalize(keys.map(k=>Array.isArray(game[k])?game[k].join(' '):game[k]||'').join(' '))]));}
function match(record,query,field='all'){const tokens=normalize(query).split(' ').filter(Boolean),text=field==='all'?Object.values(record).join(' '):record[field]||'';return tokens.every(token=>text.includes(token));}
function relevance(record,query){const q=normalize(query);return !q?0:record.name===q?100:record.name.startsWith(q)?75:record.name.includes(q)?50:10;}
function decode(search){const p=new URLSearchParams(search);return Object.fromEntries(p);}
const api={fields,normalize,index,match,relevance,decode};root.CatalogCore=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window==='undefined'?globalThis:window);
