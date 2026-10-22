/* Shared, DOM-free catalog search and URL helpers. */
(function(root){
'use strict';
const fields={name:['name','nameZh','aliases'],designer:['designer'],publisher:['publisher'],mechanism:['mechanism','mechanismZh'],category:['category','categoryZh','type','typeZh']};
const normalize=value=>String(value??'').normalize('NFKD').replace(/\p{M}/gu,'').toLocaleLowerCase().replace(/[‐‑–—-]/g,' ').replace(/\s+/g,' ').trim();
function index(game){return Object.fromEntries(Object.entries(fields).map(([key,keys])=>[key,normalize(keys.map(k=>Array.isArray(game[k])?game[k].join(' '):game[k]||'').join(' '))]));}
function match(record,query,field='all'){const tokens=normalize(query).split(' ').filter(Boolean),text=field==='all'?Object.values(record).join(' '):record[field]||'';return tokens.every(token=>text.includes(token));}
function relevance(record,query){const q=normalize(query);return !q?0:record.name===q?100:record.name.startsWith(q)?75:record.name.includes(q)?50:10;}
function decode(search){const p=new URLSearchParams(search);return Object.fromEntries(p);}
function designerKey(name){return String(name).normalize('NFKC').toLocaleLowerCase().replace(/\s+/g,' ').trim();}
function designerNames(value){
 const text=String(value||'');
 return text.split(/[;；]/.test(text)?/[;；]/:/[,、]/).map(name=>name.trim()).filter(name=>name&&!/^(?:BGG\s*未.*|未(?:標示|提供|公開)|不適用|unknown|uncredited|\(uncredited\)|n\/a|-)$/i.test(name));
}
function buildDesigners(games){
 const designers=new Map();
 for(const game of games){if(game.kind==='佔位項目')continue;const seen=new Set();for(const name of designerNames(game.designer)){const key=designerKey(name);if(seen.has(key))continue;seen.add(key);if(!designers.has(key))designers.set(key,{key,name,games:[]});designers.get(key).games.push(game)}}
 return designers;
}
function bggGameUrl(game){
 const id=String(game.bggid||'').trim();
 if(/^\d+$/.test(id)&&Number(id)>0)return 'https://boardgamegeek.com/boardgame/'+id;
 const match=String(game.url||'').match(/^https?:\/\/(?:www\.)?boardgamegeek\.com\/boardgame\/(\d+)(?:[/?#]|$)/i);
 return match&&Number(match[1])>0?'https://boardgamegeek.com/boardgame/'+match[1]:null;
}
function bggLinks(games){return [...new Set(games.map(bggGameUrl).filter(Boolean))];}
const api={fields,normalize,index,match,relevance,decode,designerKey,designerNames,buildDesigners,bggGameUrl,bggLinks};root.CatalogCore=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window==='undefined'?globalThis:window);
