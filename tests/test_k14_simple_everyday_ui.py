"""Focused checks for the everyday one-screen Local Knowledge experience."""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from tof_cli.ui import app


def test_one_primary_screen_and_progressive_disclosure():
    html = app._render_page("/")
    assert 'id="simple-dropzone"' in html
    assert 'id="source-files"' in html
    assert 'id="source-folder"' in html
    assert 'id="qa-question"' in html
    assert 'id="qa-result"' in html
    assert '<details class="simple-more">' in html
    assert '<nav class="page-nav"' in html
    assert 'id="index-batch-button"' not in html
    assert 'id="source-result"' not in html
    assert 'id="overview-status-title"' in html
    assert "data-i18n=\"simpleMore\"" in html
    assert "id=\"source-import-status\"" in html


def test_original_expert_routes_and_apis_remain():
    assert 'id="search-query"' in app._render_page("/dokumente-durchsuchen")
    assert 'id="index-batch-button"' in app._render_page("/quellen-index")
    assert 'id="evidence-result"' in app._render_page("/beleg-pruefen")
    assert app._render_page("/") == app._render_page("/uebersicht")
    script = app.HTML
    assert "await indexImportedSource(sourceId)" in script
    assert "await refreshOverview()" in script
    assert "zone.addEventListener('drop'" not in script  # delegated via loop
    assert "importSelectedFiles(event.dataTransfer.files, false)" in script


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js unavailable")
def test_import_one_file_automatically_indexes_without_second_click():
    script = app.HTML.split("<script>", 1)[1].split("</script>", 1)[0]
    harness = r"""
const vm = require('vm');
const fs = require('fs');
const js = fs.readFileSync(0, 'utf8');
const requests = [];
const el = (id) => ({
  id, textContent: '', innerHTML: '', disabled: false,
  classList: {add(){},remove(){}},
  addEventListener(){},
  querySelectorAll(){ return []; },
});
const elements = {};
for (const key of [
  'simple-home','simple-dropzone','source-import-status',
  'overview-status-title','overview-status-detail',
  'qa-result','qa-question','qa-scope','qa-limit',
  'language-toggle','theme-toggle','log'
]) elements[key] = el(key);
elements['qa-scope'].value = '';
elements['qa-limit'].value = '5';
const document = {
  documentElement: {lang:'de'},
  body: {classList:{toggle(){}}},
  querySelectorAll:()=>[],
  querySelector:()=>({textContent:'Wissen'}),
  getElementById:(id)=>elements[id]||null,
  title:'',
};
let indexed = 0;
async function fetch(url, opts = {}) {
  requests.push(url);
  if (url === '/api/summary') return {ok:true, async json(){return {}}};
  if (url === '/api/sources') return {ok:true, async json(){
    return {sources:[{indexed}]};
  }};
  if (url === '/api/import-files') return {ok:true, async json(){
    return {status:'ok',copied:1,source_id:'space_demo'};
  }};
  if (url === '/api/index-batch') {
    const payload = JSON.parse(opts.body);
    if (payload.space_id !== 'space_demo') throw new Error('wrong import scope');
    indexed++;
    return {ok:true, async json(){return {
      status:'ok',indexed_this_pass:1,failed:[],
      page_has_more:false,remaining_in_sample:0,
    }}};
  }
  throw new Error('unexpected fetch '+url);
}
class FileReader {
  readAsDataURL() {
    this.result='data:text/plain;base64,dGVzdA==';
    this.onload();
  }
}
const store = {getItem:()=>null,setItem(){}};
const ctx = vm.createContext({
  document, localStorage:store, fetch, FileReader, URLSearchParams,
  window:{location:{pathname:'/',search:''}},
});
vm.runInContext(js, ctx, {timeout:2000});
ctx.selection=[{name:'demo.md',size:4}];
vm.runInContext('importSelectedFiles(selection,false)',ctx,{timeout:2000}).then(()=>{
  const imports=requests.filter(x=>x==='/api/import-files').length;
  const batches=requests.filter(x=>x==='/api/index-batch').length;
  process.stdout.write(JSON.stringify({
    imports,batches,indexed,
    processedNotice: elements['source-import-status'].textContent.includes('bereit'),
  }));
}).catch(e=>{process.stderr.write(e.stack);process.exitCode=1;});
"""
    out = subprocess.run(
        ["node", "-e", harness], input=script, text=True,
        capture_output=True, timeout=10, check=False,
    )
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data == {"imports": 1, "batches": 1, "indexed": 1,
                    "processedNotice": True}


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js unavailable")
def test_five_file_import_continues_after_one_index_failure():
    """Five files require two imports; one failed extraction must not block peers."""
    script = app.HTML.split("<script>", 1)[1].split("</script>", 1)[0]
    harness = r"""
const vm = require('vm');
const fs = require('fs');
const js = fs.readFileSync(0, 'utf8');
const requests = [];
const el = (id) => ({
  id, textContent: '', innerHTML: '', disabled: false,
  classList: {add(){},remove(){}},
  addEventListener(){},
  querySelectorAll(){ return []; },
});
const elements = {};
for (const key of [
  'simple-home','simple-dropzone','source-import-status',
  'overview-status-title','overview-status-detail',
  'qa-result','qa-question','qa-scope','qa-limit',
  'language-toggle','theme-toggle','log'
]) elements[key] = el(key);
elements['qa-scope'].value = '';
elements['qa-limit'].value = '5';
const document = {
  documentElement: {lang:'de'},
  body: {classList:{toggle(){}}},
  querySelectorAll:()=>[],
  querySelector:()=>({textContent:'Wissen'}),
  getElementById:(id)=>elements[id]||null,
  title:'',
};
let indexed = 0;
let indexCalls = 0;
async function fetch(url, opts = {}) {
  requests.push(url);
  if (url === '/api/summary') return {ok:true, async json(){return {}}};
  if (url === '/api/sources') return {ok:true, async json(){
    return {sources:[{indexed}]};
  }};
  if (url === '/api/import-files') return {ok:true, async json(){
    return {status:'ok',copied:JSON.parse(opts.body).files.length,source_id:'space_demo'};
  }};
  if (url === '/api/index-batch') {
    const payload = JSON.parse(opts.body);
    if (payload.space_id !== 'space_demo') throw new Error('wrong import scope');
    indexCalls++;
    indexed += indexCalls === 1 ? 1 : 3;
    return {ok:true, async json(){return indexCalls === 1 ? {
      status:'partial',indexed_this_pass:1,failed:[{path:'broken.pdf'}],
      page_has_more:false,remaining_in_sample:3,
    } : {
      status:'ok',indexed_this_pass:3,failed:[],
      page_has_more:false,remaining_in_sample:0,
    }}};
  }
  throw new Error('unexpected fetch '+url);
}
class FileReader {
  readAsDataURL() {
    this.result='data:text/plain;base64,dGVzdA==';
    this.onload();
  }
}
const store = {getItem:()=>null,setItem(){}};
const ctx = vm.createContext({
  document, localStorage:store, fetch, FileReader, URLSearchParams,
  window:{location:{pathname:'/',search:''}},
});
vm.runInContext(js, ctx, {timeout:2000});
ctx.selection=Array.from({length:5},(_,i)=>({name:'demo'+i+'.md',size:4}));
vm.runInContext('importSelectedFiles(selection,false)',ctx,{timeout:2000}).then(()=>{
  const imports=requests.filter(x=>x==='/api/import-files').length;
  const batches=requests.filter(x=>x==='/api/index-batch').length;
  process.stdout.write(JSON.stringify({
    imports,batches,indexed,
    processedNotice: elements['source-import-status'].textContent.includes('teilweise abgeschlossen'),
  }));
}).catch(e=>{process.stderr.write(e.stack);process.exitCode=1;});
"""
    out = subprocess.run(
        ["node", "-e", harness], input=script, text=True,
        capture_output=True, timeout=10, check=False,
    )
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data == {"imports": 2, "batches": 2, "indexed": 4,
                    "processedNotice": True}
