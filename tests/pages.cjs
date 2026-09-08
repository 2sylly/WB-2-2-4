const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
(async () => {
  for (const base of ['https://2sylly.github.io/WB-2-2-4', 'http://localhost:8765']) {
    const requests = [];
    const location = new URL(base + '/builder/');
    const element = () => ({classList:{add(){},contains(){return false}},style:{},addEventListener(){}});
    const context = vm.createContext({console:{log(){}}, screen:{width:1440}, navigator:{userAgent:'test'},
      window:{location}, document:{currentScript:{src:base+'/js/utils.js'},getElementById:element,createElement:element},
      setTimeout,clearTimeout,TextEncoder,TextDecoder,URLSearchParams,
      fetch:async url => { requests.push(url); assert.ok(url.startsWith(base+'/data/'), url);
        const relative = url.slice(base.length+1); return {json:async()=>JSON.parse(read(relative))}; }});
    for (const file of ['js/utils.js','js/build_utils.js','js/powders.js','js/damage_calc.js','js/computation_graph.js',
      'js/loader.js','js/load_item.js','js/builder/build_encode_decode.js','js/builder/atree.js']) {
      vm.runInContext(read(file), context, {filename:file});
    }
    await vm.runInContext(`Promise.all([Loader.load_json('data/2.2.4.0/items'),
      load_major_id_data('2.2.4.0'),load_encoding_constants('2.2.4.0','2.2.3.0'),load_atree_data('2.2.4.0')])`,context);
    assert.equal(requests.length,5);
    for (const page of ['builder/index.html','builder/index_full.html']) {
      for (const match of read(page).matchAll(/(?:src|href)=["']([^"']+)["']/g)) {
        if (/^(https?:|#|$)/.test(match[1])) continue;
        const url = new URL(match[1],base+'/builder/');
        assert.ok(url.href.startsWith(base+'/'),url.href);
        assert.ok(fs.existsSync(path.join(root,url.pathname.slice(new URL(base).pathname.replace(/\/$/,'').length))),url.href);
      }
    }
  }
  assert.ok(read('index.html').includes("'./builder/' + window.location.search + window.location.hash"));
  assert.ok(fs.existsSync(path.join(root,'.nojekyll')));
  console.log('PASS: Pages subdirectory and localhost assets, snapshot/historical data fetches, root redirect.');
})().catch(error=>{console.error(error);process.exitCode=1;});
