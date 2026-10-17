const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
function load(){const listeners={};const context={window:{},document:{addEventListener:(name,fn)=>(listeners[name]??=[]).push(fn)},console,Set,Map,queueMicrotask,fetch:async()=>({json:async()=>({games:{},mechanisms:{}})})};context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('enhancements.js','utf8'),context);return {E:context.AtlasEnhancements,context,listeners}}
test('escapes source HTML and rejects executable links',()=>{const {E}=load();assert.equal(E.esc('<img src=x>'),'&lt;img src=x&gt;');assert.equal(E.link('javascript:alert(1)','x'),'');assert.match(E.link('https://example.com','source'),/noopener/)});
test('retains missing numeric data and parses ranges',()=>{const {E}=load();assert.equal(E.missing(null),'未提供');assert.equal(E.missing(0),0);assert.deepEqual(Array.from(E.nums('30–90 Min')),[30,90]);assert.deepEqual(Array.from(E.nums('未提供')),[])});
test('no unverified translation is invented',()=>{const {E}=load();assert.equal(E.translation({id:123}).length,0);assert.equal(E.id({id:123,stableId:'bgg:7:v1'}),'bgg:7:v1')});
test('dedup preserves language and edition scope differences',()=>{const {E,context}=load();let received;const text=fs.readFileSync('enhancements.js','utf8');const start=text.indexOf('(()=>{const original=AtlasEnhancements.documents;');const end=text.indexOf('\n',start);E.documents=(c,r)=>{received=r;c.querySelector=()=>({insertAdjacentHTML(){}})};vm.runInContext(text.slice(start,end),context);const a={url:'https://x',name:'Rules',date:'2026',language:'English',scope:'1st'};E.documents({},[a,{...a},{...a,language:'繁中'},{...a,scope:'2nd'}],{});assert.equal(received.length,3)});
