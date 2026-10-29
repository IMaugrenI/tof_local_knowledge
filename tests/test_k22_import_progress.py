"""Focused browser-state regression for multi-page progress and rejected uploads."""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from tof_cli.ui import app


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js unavailable")
def test_index_continues_across_two_empty_scan_pages_before_valid_files():
    js = app.HTML.split("<script>", 1)[1].split("</script>", 1)[0]
    harness = r"""
const vm=require('vm'),fs=require('fs');
const script=fs.readFileSync(0,'utf8'),requests=[],elements={};
function el(){
 return {textContent:'',value:'',innerHTML:'',disabled:false,style:{},children:[],
  classList:{add(){},remove(){},toggle(){}},addEventListener(){},
  replaceChildren(...c){this.children=c},appendChild(c){this.children.push(c)},
  focus(){},querySelectorAll(){return []},setAttribute(){}};
}
for(const id of ['simple-home','qa-result','source-import-status',
 'source-import-progress','source-import-errors','source-import-error-list',
 'overview-status-title','overview-status-detail','language-toggle',
 'theme-toggle','log'])elements[id]=el();
const document={documentElement:{},body:{classList:{toggle(){}}},
 querySelectorAll:()=>[],querySelector:()=>({textContent:'Wissen'}),
 getElementById:id=>elements[id]||null,createElement:()=>el(),title:''};
let n=0;
async function fetch(url,options={}){
 if(url==='/api/summary')return {ok:true,json:async()=>({})};
 if(url==='/api/sources')return {ok:true,json:async()=>({sources:[{indexed:1}]})};
 if(url==='/api/index-batch'){
  const request=JSON.parse(options.body);requests.push(request);
  const cursor=['null','after_first','after_second'][n];
  if(n===0 && request.cursor!==null)throw Error('first cursor wrong');
  if(n===1 && request.cursor!=='after_first')throw Error('second cursor wrong');
  if(n===2 && request.cursor!=='after_second')throw Error('third cursor wrong');
  n++;
  return {ok:true,json:async()=>n===1?{
   status:'ok',indexed_this_pass:0,failed:[],page_has_more:true,
   next_cursor:'after_first',remaining_in_sample:0}:n===2?{
   status:'ok',indexed_this_pass:0,failed:[],page_has_more:true,
   next_cursor:'after_second',remaining_in_sample:0}:{
   status:'ok',indexed_this_pass:1,failed:[],page_has_more:false,
   next_cursor:null,remaining_in_sample:0}};
 }
 throw Error('unexpected '+url);
}
const ctx=vm.createContext({document,localStorage:{getItem:()=>null,setItem(){}},
 fetch,URLSearchParams,window:{location:{pathname:'/',search:''}}});
vm.runInContext(script,ctx,{timeout:2000});
vm.runInContext("indexImportedSource('space_demo')",ctx).then(()=>{
 process.stdout.write(JSON.stringify({passes:n,notice:elements['source-import-status'].textContent,
 messageCount:elements['qa-result'].children.length}));
}).catch(e=>{process.stderr.write(e.stack);process.exitCode=1;});
"""
    out = subprocess.run(["node", "-e", harness], input=js, text=True,
                         capture_output=True, timeout=10, check=False)
    assert out.returncode == 0, out.stderr
    response = json.loads(out.stdout)
    assert response["passes"] == 3
    assert "Dateien bereit" in response["notice"]
    assert response["messageCount"] == 1


def test_ui_marks_skipped_only_batches_as_not_ready():
    source = app.HTML
    assert "if (!candidates.length)" in source
    assert "output.textContent = t('sourceAllRejected')" in source
    assert "complete && !failures && !skippedDetails.length" in source
    assert "nextCursor && nextCursor !== cursor" in source
    assert "const failures = new Set(failedPaths).size" in source
