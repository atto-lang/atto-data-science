// Host-only independent numerical/property oracle for an Oreslang source bridge.
// This file does NOT execute the Oreslang compiler or guest program.
import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const source=readFileSync(new URL("../src/pipeline/ml_batch_bridge.ores",import.meta.url),"utf8");
function compact(values,valid,capacity){
  if(values.length!==valid.length)throw Error("mask");
  const out=[],rows=[];
  for(let i=0;i<values.length;i++)if(valid[i]){
    if(!Number.isFinite(values[i]))throw Error("nonfinite");
    out.push(values[i]);rows.push(i);
  }
  if(out.length>capacity)throw Error("capacity");
  return {out,rows};
}
function scatter(grad,rows,n,destination){
  if(n<0||n>grad.length||n>rows.length)throw Error("count");
  const next=[...destination];
  if(next.some(x=>!Number.isFinite(x)))throw Error("nonfinite destination");
  for(let i=0;i<n;i++){
    if(!Number.isInteger(rows[i])||rows[i]<0||rows[i]>=next.length)throw Error("index");
    if(!Number.isFinite(grad[i]))throw Error("gradient");
  }
  for(let i=0;i<n;i++){
    const j=rows[i];const value=next[j]+grad[i];
    if(!Number.isFinite(value))throw Error("overflow");
    next[j]=value;
  }
  return next;
}
test("native Oreslang file contains owned-buffer and checked two-pass primitives",()=>{
  assert.match(source,/pub fnc compact_valid_f64_into\(/);
  assert.match(source,/pub fnc scatter_add_f64_into\(/);
  assert.match(source,/source_rows_out\[write_index\] = i/);
  assert.match(source,/scratch\[row\] = updated/);
  assert.match(source,/destination\[j\] = scratch\[j\]/);
  assert.match(source,/if needed > capacity/);
  assert.match(source,/source_rows\[j\] >= output_count/);
  assert.doesNotMatch(source,/\bself\.state\b/);
});
test("nullable input emits original stable row IDs",()=>{
  assert.deepEqual(compact([2,999,4,6],[true,false,true,true],4),
                   {out:[2,4,6],rows:[0,2,3]});
  assert.deepEqual(compact([],[],0),{out:[],rows:[]});
});
test("duplicate indices accumulate rather than overwrite",()=>{
  assert.deepEqual(scatter([1,3,5,7],[0,2,2,3],4,[0,0,0,0]),[1,0,8,7]);
});
test("compaction rejects mask errors, capacity and selected nonfinite",()=>{
  assert.throws(()=>compact([1],[true,false],2),/mask/);
  assert.throws(()=>compact([1,2],[true,true],1),/capacity/);
  assert.throws(()=>compact([Infinity,2],[true,true],2),/nonfinite/);
  assert.deepEqual(compact([Infinity,2],[false,true],2),{out:[2],rows:[1]});
});
test("scatter errors leave original destination untouched",()=>{
  for(const [g,idx,n] of [[[2],[9],1],[[Infinity],[0],1],[[3],[0],2]]){
    const dst=[7,11];
    assert.throws(()=>scatter(g,idx,n,dst));
    assert.deepEqual(dst,[7,11]);
  }
});
test("scatter numeric overflow rejects before original publication",()=>{
  const dst=[Number.MAX_VALUE];
  assert.throws(()=>scatter([Number.MAX_VALUE],[0],1,dst),/overflow/);
  assert.deepEqual(dst,[Number.MAX_VALUE]);
});
test("scatter finite difference check of a gathered sum with repeated indices",()=>{
  const rows=[0,2,2,3],weights=[1,3,5,7],x=[2,4,6,8];
  const f=values=>rows.reduce((s,row,i)=>s+values[row]*weights[i],0);
  const grad=scatter(weights,rows,weights.length,[0,0,0,0]);
  const eps=1e-5;
  for(let i=0;i<x.length;i++){
    const plus=[...x],minus=[...x];plus[i]+=eps;minus[i]-=eps;
    const d=(f(plus)-f(minus))/(2*eps);
    assert(Math.abs(d-grad[i])<1e-7);
  }
});
