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
context.data = json('data/2.2.4.1/atree.json');
context.majorData = json('data/2.2.4.1/majid.json');
context.encData = json('data/2.2.4.1/encoding_consts.json');
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
for (const version of [0,18,33,34,35]) {
    assert.equal(run(`decodeHeader(new BitVectorCursor(encodeHeader(${version})))`),version);
}
for (const level of [1,106,121]) assert.equal(run(`decodeLevel(new BitVectorCursor(encodeLevel(${level},34)))`),level);
for (const clazz of ['Archer','Warrior','Mage','Assassin','Shaman']) {
    const actual=run(`get_sorted_class_atree(ATREES,'${clazz}').map(n=>n.ability.id)`);
    assert.equal(new Set(actual).size,context.data[clazz].length,`${clazz} tree is fully reachable`);
}
const items=json('data/2.2.4.1/items.json').items;
const byId=new Map(items.map(i=>[i.id,i]));
assert.equal(byId.size,items.length,'item IDs must be unique');
for (const [name,level,damage,rolls] of [
    ['Divzer',110,['26-27','215-215'],{ls:[326,1413],ms:[7,31],sdRaw:[91,393],spd:[7,30]}],
    ['Sunstar',109,['295-385','850-1055'],{ls:[248,1073],tDamPct:[8,33],mdPct:[3,14]}],
    ['Warp',111,['40-65','140-160'],{mr:[-46,-25],aDamPct:[7,30],spRaw2:[-113,-488]}]
]) {
    const item=items.find(i=>i.name==='Masterwork '+name);
    assert.equal(item.lvl,level);
    assert.equal(item.nDam,damage[0]);
    assert.equal(item[name==='Warp'?'aDam':'tDam'],damage[1]);
    assert.ok(item.id+1 < 2**context.encData.ITEM_ID_BITLEN);
    context.ascension=item;
    const expanded=run(`Object.fromEntries(['minRolls','maxRolls'].map(k=>[k,Object.fromEntries(expandItem(ascension).get(k))]))`);
    for(const [stat,range] of Object.entries(rolls)) assert.deepEqual([expanded.minRolls[stat],expanded.maxRolls[stat]],range,name+' '+stat);
}
result=run(`evaluateBuild('Mage',['Teleport'],['VORTEX'])`);
assert.deepEqual(part(result,2,'Vortex').multipliers,[200,0,0,0,0,20]);
assert.equal(result.spells[2].display,'Total Damage');
assert.equal(part(result,2,'Single Teleport').hits.Vortex,1);
assert.equal(part(result,2,'Total Damage').hits['Single Teleport'],1);

assert.equal(items.find(i=>i.displayName==='Cancer').maxMana,31);
assert.equal(items.find(i=>i.displayName==='Necrosis').maxMana,undefined);
assert.equal(items.find(i=>i.displayName==='Tectonics').nDam,'130-150');
assert.equal(items.find(i=>i.displayName==='Tremor').nDam,undefined);
assert.equal(items.find(i=>i.name==='Galleon').maxMana,58);
assert.equal(items.find(i=>i.name==='Mist Unit Trousers').fixID,true);
const oldItems=json('data/2.2.3.0/items.json').items;
for (const item of oldItems) if(byId.has(item.id)) assert.equal(byId.get(item.id).name,item.name);
const ingredients=json('data/2.2.4.1/ingreds.json');
const catalyst=ingredients.find(i=>i.name==='Ritual Catalyst');
assert.deepEqual(catalyst.ids,{ms:{minimum:8,maximum:8},sdPct:{minimum:6,maximum:6},ls:{minimum:-100,maximum:-100},mdPct:{minimum:-12,maximum:-12}});
assert.equal(catalyst.itemIDs.strReq,-15);
assert.equal(catalyst.itemIDs.intReq,40);
assert.equal(catalyst.itemIDs.dura,-135);
const oldIngredients=new Map(json('data/2.2.3.0/ingreds.json').map(i=>[i.id,i]));
for(const ing of ingredients) for(const [stat,range] of Object.entries(ing.ids || {})) {
    if(range.minimum>range.maximum) assert.deepEqual(range,oldIngredients.get(ing.id)?.ids[stat],ing.name+' must not introduce reversed ranges');
}
assert.deepEqual(json('data/2.2.4.1/encoding_consts.json'),json('data/2.2.3.0/encoding_consts.json'));
assert.deepEqual(json('data/2.2.4.1/items.json'),json('data/baseline/compressed/compress.json'));
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

// Checklist nodes are independent, spend AP, and survive tree sharing/reset.
vm.runInContext(`
draw_atlas_image = () => {};
const testElements = new Map();
document.getElementById = id => { if (!testElements.has(id)) testElements.set(id, {}); return testElements.get(id); };
const checklistTree = get_sorted_class_atree(ATREES,'Shaman');
const checklistState = new Map(checklistTree.map(n => [n.ability.id,{...n,active:false,checkbox:{checked:false}}]));
const free = checklistTree.filter(n=>n.ability.snapshot_checklist);
for (const n of free) atree_set_state(checklistState.get(n.ability.id),true);
const validateChecklist = () => atree_validate.compute_func(new Map([['atree',checklistTree],['atree-state',checklistState],['level',121]]));
`,context);
assert.equal(run('free.length'),14);
assert.deepEqual(run('validateChecklist()'),[false,[]]);
assert.equal(run("testElements.get('active_AP_cost').textContent"),run('free.reduce((s,n)=>s+n.ability.cost,0)'));
assert.ok(run('free.every(n=>checklistState.get(n.ability.id).checkbox.checked)'));
assert.ok(run('checklistTree.filter(n=>!n.ability.snapshot_checklist).every(n=>n.parents.every(p=>!p.ability.snapshot_checklist))'));
assert.deepEqual(run('decodeAtree(checklistTree,encodeAtree(checklistTree,checklistState)).filter(n=>n.ability.snapshot_checklist).map(n=>n.ability.id).sort((a,b)=>a-b)'),run('free.map(n=>n.ability.id).sort((a,b)=>a-b)'));
vm.runInContext('for (const n of free) atree_set_state(checklistState.get(n.ability.id),false); validateChecklist();',context);
assert.equal(run("testElements.get('active_AP_cost').textContent"),0);
assert.ok(run('free.every(n=>!checklistState.get(n.ability.id).checkbox.checked)'));
result=run(`evaluateBuild('Shaman',['Totem','Aura','Totemic Shatter'])`);
const inherited=part(result,3,'Single Wave').multipliers[0];
const baseAura=part(run(`evaluateBuild('Shaman',['Aura'])`),3,'Single Wave').multipliers[0];
assert.equal(inherited-baseAura,10);
result=run(`evaluateBuild('Shaman',['Uproot','Mystic Masks','Haunting Memory','Awakened'])`);
assert.equal(part(result,4,'Rotation DPS').hits['Mask Throw'],1);
console.log('PASS: checklist AP, independent paths, selection round trips/reset, inherited Egomania and Corporeal Manifestation.');

vm.runInContext(`
const sacrifice = free.find(n=>n.ability.display_name==='Greater Sacrifice');
const doubleTotem = checklistTree.find(n=>n.ability.display_name==='Double Totem');
atree_set_state(checklistState.get(sacrifice.ability.id),true);
checklistState.get(doubleTotem.ability.id).active=true;
`,context);
assert.equal(run('abil_can_activate(sacrifice,checklistState,new Set(),new Map(),50)[1]'),true);
vm.runInContext('checklistState.get(doubleTotem.ability.id).active=false;',context);
assert.equal(run('abil_can_activate(sacrifice,checklistState,new Set(),new Map(),0)[0]'),false);
vm.runInContext('for (const n of checklistTree) checklistState.get(n.ability.id).active=true; validateChecklist();',context);
assert.equal(run("testElements.get('active_AP_cost').textContent"),run('checklistTree.reduce((s,n)=>s+n.ability.cost,0)'));
assert.ok(run("validateChecklist()[1].some(e=>e.includes('too many ability points'))"));
console.log('PASS: confirmed exclusions and AP overspending include checklist selections.');
