const {test}=require('node:test');const assert=require('node:assert/strict');const c=require('../catalog-core.js');
test('normalizes accents, width and hyphens without folding unrelated names',()=>{assert.equal(c.normalize(' Ｃafé—Game '),'cafe game');assert.notEqual(c.normalize('陸'),c.normalize('陆'));});
test('all tokens must match meaningful fields, never URLs or notes',()=>{const r=c.index({name:'Café Game',designer:'Alex',url:'https://secret.example',notes:'hidden'});assert(c.match(r,'alex cafe'));assert(!c.match(r,'cafe absent'));assert(!c.match(r,'secret'));assert(!c.match(r,'hidden'));assert(!c.match(r,'alex','name'));});
test('full name ranks before a partial name',()=>{assert(c.relevance(c.index({name:'Catan'}),'catan')>c.relevance(c.index({name:'Catan Expansion'}),'catan'));});
