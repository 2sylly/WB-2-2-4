const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root,p), 'utf8');
const json = p => JSON.parse(read(p));
const element = () => ({classList:{add(){},contains(){return false}},style:{},addEventListener(){}});
const context = vm.createContext({console:{log(){},warn(){},error(){}}, structuredClone, screen:{width:1440}, TextEncoder, TextDecoder, URLSearchParams,
    window:{location:{protocol:'http:',host:'localhost',pathname:'/builder/',search:'',hash:''}},
    navigator:{userAgent:'node-test'},document:{getElementById:element,createElement:element}, setTimeout,clearTimeout});
for (const file of ['js/utils.js','js/build_utils.js','js/powders.js','js/damage_calc.js',
    'js/computation_graph.js','js/loader.js','js/load_item.js','js/builder/build_encode_decode.js',
    'js/builder/atree.js','js/snapshot_224.js']) {
    vm.runInContext(read(file),context,{filename:file});
}
context.data = json('data/2.2.4.0/atree.json');
context.majorData = json('data/2.2.4.0/majid.json');
context.encData = json('data/2.2.4.0/encoding_consts.json');
vm.runInContext(`
ATREES=data; MAJOR_IDS=majorData; ENC=encData; DEC=encData;
function evaluateBuild(clazz, names, majorIds=[]) {
    const order=get_sorted_class_atree(ATREES,clazz);
    const state=new Map(order.map(n=>[n.ability.id,{active:names.includes(n.ability.display_name)}]));
    const types={Mage:'wand',Shaman:'relik',Warrior:'spear',Archer:'bow',Assassin:'dagger'};
    const build={weapon:{statMap:new Map([['type',types[clazz]]])},statMap:new Map([['activeMajorIDs',majorIds]])};
    const merged=atree_merge.compute_func(new Map([['atree-errors',[false,[]]],['player-class',clazz],['build',build],['atree-state',state],['atree',order],['final-aspects',[]]]));
    const spells=atree_collect_spells.compute_func(new Map([['atree-merged',merged]]));
    return {spells:Object.fromEntries(spells),merged:Object.fromEntries(merged)};
}
`,context);
function run(code) { return JSON.parse(JSON.stringify(vm.runInContext(code,context))); }
function part(result, spell, name) { return result.spells[spell].parts.find(p=>p.name===name); }
let result=run(`evaluateBuild('Mage',['Ice Snake','Freezing Sigil'],['FISSURE'])`);
assert.deepEqual(part(result,7,'Tick Damage').multipliers,[40,0,0,10,0,0]);
assert.deepEqual(part(result,4,'Ice Snake Damage').multipliers,[470,0,0,255,0,0]);
result=run(`evaluateBuild('Shaman',['Totem','Haul','Uproot','Aura','Frog Dance'],['FAUSTIAN_GAMBIT'])`);
assert.deepEqual(part(result,2,'Hop Damage').multipliers,[225,0,400,75,0,0]);
assert.equal(part(result,2,'Total Damage').hits['Hop Damage'],1);
result=run(`evaluateBuild('Shaman',['Totem','Twisted Tether','Bloodletting','Eldritch Call'])`);
assert.deepEqual(part(result,8,'Tether Tick').multipliers,[45,0,0,0,0,20]);
assert.deepEqual(part(result,11,'Single Hit').multipliers,[650,0,100,0,100,0]);
result=run(`evaluateBuild('Mage',['Meteor','Thunderstorm','Induced Instability'],['SOLAR_WIND'])`);
assert.equal(result.spells[3].mana_gained,30);
assert.equal(part(result,3,'Total Damage').hits['Lightning Damage'],3);
const bolt=part(result,3,'Lightning Damage').multipliers;
assert.ok(Math.abs(bolt.reduce((a,b)=>a+b)*3-840)<1e-9);
result=run(`evaluateBuild('Archer',['Arrow Bomb'],['FOREST_BLESSING'])`);
assert.deepEqual(part(result,3,'Arrow Bomb').multipliers,[140,0,0,0,20,0]);
assert.equal(run(`snapshot224ManaOnHeretic(new Map([['maxMana',40],['int',0]]))`),42);
assert.equal(run(`snapshot224ManaOnHeretic(new Map([['maxMana',-300],['int',0]]))`),0);
for (const version of [0,18,33,34]) {
    assert.equal(run(`decodeHeader(new BitVectorCursor(encodeHeader(${version})))`),version);
}
for (const level of [1,106,121]) assert.equal(run(`decodeLevel(new BitVectorCursor(encodeLevel(${level},34)))`),level);
for (const clazz of ['Archer','Warrior','Mage','Assassin','Shaman']) {
    const actual=run(`get_sorted_class_atree(ATREES,'${clazz}').map(n=>n.ability.id)`);
    assert.equal(new Set(actual).size,context.data[clazz].length,`${clazz} tree is fully reachable`);
}
const items=json('data/2.2.4.0/items.json').items;
const byId=new Map(items.map(i=>[i.id,i]));
assert.equal(items.find(i=>i.displayName==='Cancer').maxMana,31);
assert.equal(items.find(i=>i.displayName==='Necrosis').maxMana,undefined);
assert.equal(items.find(i=>i.displayName==='Tectonics').nDam,'130-150');
assert.equal(items.find(i=>i.displayName==='Tremor').nDam,undefined);
assert.equal(items.find(i=>i.name==='Galleon').maxMana,58);
assert.equal(items.find(i=>i.name==='Mist Unit Trousers').fixID,true);
const oldItems=json('data/2.2.3.0/items.json').items;
for (const item of oldItems) if(byId.has(item.id)) assert.equal(byId.get(item.id).name,item.name);
const ingredients=json('data/2.2.4.0/ingreds.json');
const catalyst=ingredients.find(i=>i.name==='Ritual Catalyst');
assert.deepEqual(catalyst.ids,{ms:{minimum:8,maximum:8},sdPct:{minimum:6,maximum:6},ls:{minimum:-100,maximum:-100},mdPct:{minimum:-12,maximum:-12}});
assert.equal(catalyst.itemIDs.strReq,-15);
assert.equal(catalyst.itemIDs.intReq,40);
assert.equal(catalyst.itemIDs.dura,-135);
const oldIngredients=new Map(json('data/2.2.3.0/ingreds.json').map(i=>[i.id,i]));
for(const ing of ingredients) for(const [stat,range] of Object.entries(ing.ids || {})) {
    if(range.minimum>range.maximum) assert.deepEqual(range,oldIngredients.get(ing.id)?.ids[stat],ing.name+' must not introduce reversed ranges');
}
assert.deepEqual(json('data/2.2.4.0/encoding_consts.json'),json('data/2.2.3.0/encoding_consts.json'));
assert.deepEqual(json('data/2.2.4.0/items.json'),json('data/baseline/compressed/compress.json'));
assert.deepEqual(ingredients,json('data/baseline/compressed/ingreds_compress.json'));
for(const page of ['builder/index.html','builder/index_full.html']) {
    const html=read(page);
    assert.ok(html.indexOf('snapshot_224.js')<html.indexOf('builder_graph.js'));
    for(const match of html.matchAll(/<script[^>]+src\s*=\s*["']([^"']+)["']/g)) {
        if(/^https?:/.test(match[1])) continue;
        const target=match[1].startsWith('/')?path.join(root,match[1]):path.resolve(root,path.dirname(page),match[1]);
        assert.ok(fs.existsSync(target),target);
    }
}
console.log('PASS: snapshot spell calculations, item identity, crafting ranges, dataset parity, all-class tree reachability, version header round trips, and script loading order.');
