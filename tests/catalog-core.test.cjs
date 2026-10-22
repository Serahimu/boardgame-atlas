const {test}=require('node:test');const assert=require('node:assert/strict');const c=require('../catalog-core.js');
test('selected BGG links deduplicate editions and reject non-game URLs',()=>{
 const games=[{bggid:'123',url:'https://boardgamegeek.com/boardgame/123/a'},
 {bggid:'123',version:'https://boardgamegeek.com/boardgameversion/456'},
 {url:'https://www.boardgamegeek.com/boardgame/789/b?tracking=1'},
 {url:'https://boardgamegeek.com/boardgameversion/456'},
 {url:'https://boardgamegeek.com.evil.test/boardgame/555'},
 {url:'https://example.com/project/123'},{bggid:'0'},{bggid:'not available'}];
 assert.deepEqual(c.bggLinks(games),['https://boardgamegeek.com/boardgame/123','https://boardgamegeek.com/boardgame/789']);
 assert.deepEqual(c.bggLinks([]),[]);
 assert.deepEqual(c.bggLinks([...games].reverse()),['https://boardgamegeek.com/boardgame/789','https://boardgamegeek.com/boardgame/123']);
});
test('normalizes accents, width and hyphens without folding unrelated names',()=>{assert.equal(c.normalize(' Ｃafé—Game '),'cafe game');assert.notEqual(c.normalize('陸'),c.normalize('陆'));});
test('all tokens must match meaningful fields, never URLs or notes',()=>{const r=c.index({name:'Café Game',designer:'Alex',url:'https://secret.example',notes:'hidden'});assert(c.match(r,'alex cafe'));assert(!c.match(r,'cafe absent'));assert(!c.match(r,'secret'));assert(!c.match(r,'hidden'));assert(!c.match(r,'alex','name'));});
test('full name ranks before a partial name',()=>{assert(c.relevance(c.index({name:'Catan'}),'catan')>c.relevance(c.index({name:'Catan Expansion'}),'catan'));});
test('designer credits split coauthors without splitting credentials in semicolon sources',()=>{
 assert.deepEqual(c.designerNames('Michael Rieneck, Stefan Stadler'),['Michael Rieneck','Stefan Stadler']);
 assert.deepEqual(c.designerNames('Rajiv V. Basaiawmoit, PhD, MBA; Chavi C-Y Fletcher Chen; Taru Deva, PhD'),['Rajiv V. Basaiawmoit, PhD, MBA','Chavi C-Y Fletcher Chen','Taru Deva, PhD']);
 for(const missing of [null,'','BGG 未標示','未提供','(Uncredited)','Unknown'])assert.deepEqual(c.designerNames(missing),[]);
});
test('designer grouping counts coauthored expansions once per person and excludes placeholders',()=>{
 const games=[{id:1,name:'Base',kind:'主遊戲',designer:'Alex; Bea; Alex'},{id:2,name:'Expansion',kind:'擴充',designer:'Alex'},{id:3,kind:'佔位項目',designer:'Alex'},{id:4,kind:'主遊戲',designer:null}];
 const before=JSON.stringify(games),people=c.buildDesigners(games);
 assert.equal(people.size,2);assert.deepEqual(people.get('alex').games.map(g=>g.id),[1,2]);assert.deepEqual(people.get('bea').games.map(g=>g.id),[1]);assert.equal(JSON.stringify(games),before);
 assert.equal(c.buildDesigners([games[1]]).size,1);
});
test('designer route keys normalize width and spacing while retaining distinct accents',()=>{
 assert.equal(c.designerKey(' Ａlex  Smith '),'alex smith');assert.notEqual(c.designerKey('José'),c.designerKey('Jose'));
 const key=c.designerKey('Shem Phillips / 張三');assert.equal(decodeURIComponent(encodeURIComponent(key)),key);
});
test('both real datasets group shared credits and keep their own collection scope',()=>{
 const fs=require('node:fs');const catalog=JSON.parse(fs.readFileSync('data/catalog.json')),essen=JSON.parse(fs.readFileSync('data/essen.json'));
 for(const games of [catalog,essen]){const people=c.buildDesigners(games);assert(people.size>50);for(const person of people.values()){assert.equal(new Set(person.games.map(g=>g.id)).size,person.games.length);assert(person.games.every(g=>games.includes(g)));assert(!/^BGG 未/.test(person.name));}}
 const original=c.buildDesigners(catalog);assert(original.get('uwe rosenberg').games.some(g=>g.name==='A Feast for Odin'));assert(original.get('michael rieneck').games.some(g=>g.name==='Cubaneo'));assert(original.get('stefan stadler').games.some(g=>g.name==='Cubaneo'));
});
