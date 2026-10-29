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
    assert 'data-i18n="chatClear"' in html
    assert "payload.recent_questions = chatGroundedQuestions.slice(0, 4)" in app.HTML
    assert "chatGroundedQuestions = []" in app.HTML
    assert 'class="chat-feed"' in html
    assert 'id="qa-send-button"' in html
    assert 'id="chat-evidence-panel"' in html
    assert "role=\"log\"" in html
    assert 'id="simple-dropzone"' in html
    assert "initSimpleChat()" in app.HTML
    assert "if (onChat) panel.hidden = false" in app.HTML
    assert "data-i18n=\"chatHint\"" in html
    assert '<details class="simple-more">' in html
    assert '<nav class="page-nav"' in html
    assert 'id="index-batch-button"' not in html
    assert 'id="source-result"' not in html
    assert 'id="overview-status-title"' in html
    assert "data-i18n=\"simpleMore\"" in html
    assert "id=\"source-import-status\"" in html
    assert 'id="source-import-progress"' in html
    assert 'id="source-import-errors"' in html
    assert 'id="source-import-error-list"' in html
    assert "entry.textContent = path" in app.HTML
    assert "showImportFailures([...skippedDetails, ...failedPaths])" in app.HTML
    assert "showImportProgress('index')" in app.HTML
    assert "bar.removeAttribute('value')" in app.HTML
    assert "sourceRejectedSize: 'Datei größer als 12 MiB'" in app.HTML
    assert "showImportFailures([...skippedDetails, ...failedPaths])" in app.HTML


def test_original_expert_routes_and_apis_remain():
    assert 'id="search-query"' in app._render_page("/dokumente-durchsuchen")
    assert 'id="index-batch-button"' in app._render_page("/quellen-index")
    assert 'id="evidence-result"' in app._render_page("/beleg-pruefen")
    assert app._render_page("/") == app._render_page("/uebersicht")
    script = app.HTML
    assert "await indexImportedSource(sourceId, skippedDetails)" in script
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
  id, textContent: '', innerHTML: '', disabled: false, children: [], style: {},
  appendChild(child){this.children.push(child);},
  replaceChildren(...children){this.children=children;},
  classList: {add(){},remove(){}},
  addEventListener(){},
  querySelectorAll(){ return []; },
});
const elements = {};
for (const key of [
  'simple-home','simple-dropzone','source-import-status','qa-send-button',
  'source-import-errors','source-import-error-list',
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
  createElement: (tag)=>el(tag),
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
ctx.selection=[{name:'demo.md',size:4},
  {name:'bad.exe',size:4},{name:'huge.pdf',size:13*1024*1024}];
vm.runInContext('importSelectedFiles(selection,false)',ctx,{timeout:2000}).then(()=>{
  const imports=requests.filter(x=>x==='/api/import-files').length;
  const batches=requests.filter(x=>x==='/api/index-batch').length;
  process.stdout.write(JSON.stringify({
    imports,batches,indexed,
    skipped:elements['source-import-error-list'].children.map(x=>x.textContent),
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
    assert data == {"imports": 1, "batches": 1, "indexed": 1,
                    "skipped": ["bad.exe · Dateityp nicht unterstützt",
                                "huge.pdf · Datei größer als 12 MiB"],
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
  id, textContent: '', innerHTML: '', disabled: false, children: [],
  appendChild(child){this.children.push(child);},
  classList: {add(){},remove(){}},
  addEventListener(){},
  querySelectorAll(){ return []; },
});
const elements = {};
for (const key of [
  'simple-home','simple-dropzone','source-import-status','qa-send-button',
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
  createElement: (tag)=>el(tag),
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


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js unavailable")
def test_chat_followups_preserve_topic_and_clear_references_on_new_chat():
    """Bounded question context, sourced answers, reset and local excerpt."""
    script = app.HTML.split("<script>", 1)[1].split("</script>", 1)[0]
    harness = r"""
const vm = require('vm');
const fs = require('fs');
const js = fs.readFileSync(0, 'utf8');
const calls = [];
function el(tag = 'div') {
  return {
    tag, textContent:'', innerHTML:'', value:'', disabled:false,
    style:{}, dataset:{}, hidden:false, children:[],
    classList:{add(){}, remove(){}, toggle(){}},
    addEventListener(name,fn){this[name]=fn;},
    appendChild(child){this.children.push(child);},
    append(...items){this.children.push(...items);},
    replaceChildren(...items){this.children=items;},
    querySelectorAll(){return [];}, setAttribute(){},
    focus(){}, scrollIntoView(){}, scrollTop:0, scrollHeight:100,
  };
}
const ids={};
for (const id of ['simple-home','simple-dropzone','qa-result',
  'qa-question','qa-scope','qa-limit','qa-send-button',
  'source-import-status','chat-evidence-panel',
  'overview-status-title','overview-status-detail',
  'language-toggle','theme-toggle','log']) ids[id]=el();
ids['qa-limit'].value='5';
const document={
  documentElement:{lang:'de'}, body:{classList:{toggle(){}}},
  querySelectorAll:()=>[], querySelector:()=>({textContent:'Wissen'}),
  getElementById:id=>ids[id]||null, createElement:tag=>el(tag), title:'',
};
const storage={getItem:()=>null,setItem(){}};
const fetch=async(url, opts={})=>{
  if(url==='/api/summary') return {ok:true,json:async()=>({})};
  if(url==='/api/sources') return {ok:true,json:async()=>({sources:[]})};
  if(url==='/api/answer'){
    const request=JSON.parse(opts.body); calls.push(request);
    return {ok:true,json:async()=>({
      answer_text:'Answer '+calls.length,
      evidence_signal:{search_strategy:calls.length===1 || calls.length===4 ?
        'original_question' : 'contextual_followup'},
      citations:[{relative_path:'notes.md'}],
      evidence_refs:[{relative_path:'notes.md',segment_id:'seg_a'}],
    })};
  }
  if(url.startsWith('/api/evidence?')){
    return {ok:true,json:async()=>({evidence:{
      citation_label:'Source',relative_path:'notes.md',
      source_id:'source',document_id:'doc',segment_id:'seg_a',
      excerpt:'Synthetic evidence'},
      truncated_to_chars:100})};
  }
  throw Error('unexpected URL '+url);
};
const window={location:{pathname:'/',search:'',assign(){throw Error('navigated');}}};
const ctx=vm.createContext({document,window,localStorage:storage,
  fetch,URLSearchParams});
vm.runInContext(js,ctx,{timeout:2000});
async function test(){
  ids['qa-question'].value='Mietvertrag Kündigung';
  await vm.runInContext('runAnswer()',ctx);
  ids['qa-question'].value='Und welche Frist?';
  await vm.runInContext('runAnswer()',ctx);
  ids['qa-question'].value='Und welche Ausnahmen?';
  await vm.runInContext('runAnswer()',ctx);
  await vm.runInContext("inspectEvidence('seg_a')",ctx);
  vm.runInContext("toggleLanguage()",ctx);
  const inlineEvidence=ids['chat-evidence-panel'].children.length===4;
  const historyBeforeClear=ids['qa-result'].children.length;
  vm.runInContext("clearSimpleChat()",ctx);
  const cleared=ids['qa-result'].children.length===1 &&
    ids['chat-evidence-panel'].hidden===true;
  ids['qa-question'].value='Neues Thema';
  await vm.runInContext('runAnswer()',ctx);
  process.stdout.write(JSON.stringify({
    count:calls.length,
    questions:calls.map(x=>x.question),
    contextByTurn:calls.map(x=>x.recent_questions || []),
    noAnswersInContext:calls.every(x=>!Object.keys(x).includes('answer_text')),
    historyBeforeClear, cleared,
    chatMessages:ids['qa-result'].children.length,
    last:ids['qa-result'].children.at(-1).children[0].textContent,
    inlineEvidence,
    sendEnabled:ids['qa-send-button'].disabled===false,
  }));
}
test().catch(e=>{process.stderr.write(e.stack);process.exitCode=1;});
"""
    out = subprocess.run(
        ["node", "-e", harness], input=script, text=True,
        capture_output=True, timeout=10, check=False,
    )
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data == {
        "count": 4,
        "questions": ["Mietvertrag Kündigung", "Und welche Frist?",
                      "Und welche Ausnahmen?", "Neues Thema"],
        "contextByTurn": [[], ["Mietvertrag Kündigung"],
                          ["Mietvertrag Kündigung", "Und welche Frist?"], []],
        "noAnswersInContext": True,
        "historyBeforeClear": 6, "cleared": True,
        "chatMessages": 3, "last": "Answer 4",
        "inlineEvidence": True, "sendEnabled": True,
    }
