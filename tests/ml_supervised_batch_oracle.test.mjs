// HOST-ONLY reference for supervised nullable column compaction.
// The corresponding .ores program must run on a real compiler separately.
import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const implementation=readFileSync(new URL("../src/pipeline/ml_batch_bridge.ores",import.meta.url),"utf8");

function compactSupervised(feature,target,maskFeature,maskTarget,capacity) {
  if(feature.length!==maskFeature.length || target.length!==maskTarget.length)
    throw Error("INVALID_MASK");
  if(feature.length!==target.length)throw Error("ROW_MISMATCH");
  if(!Number.isSafeInteger(capacity)||capacity<0)throw Error("INVALID_CAPACITY");
  const features=[],targets=[],rows=[];
  for(let row=0;row<feature.length;row++)if(maskFeature[row] && maskTarget[row]){
    if(!Number.isFinite(feature[row]) || !Number.isFinite(target[row]))
      throw Error("NONFINITE_SELECTED_VALUE");
    if(features.length>=capacity)throw Error("BACKPRESSURE");
    features.push(feature[row]);
    targets.push(target[row]);
    rows.push(row);
  }
  return {features,targets,rows,count:features.length};
}

test("source declares supervised batch without a new actor-owned state variable",()=>{
  assert.match(implementation,/define class DenseSupervisedBatchF64/);
  assert.match(implementation,/pub fnc compact_supervised_f64_into\(/);
  assert.match(implementation,/features_out is targets_out/);
  assert.match(implementation,/validate_float_column\(feature\)/);
  assert.match(implementation,/validate_float_column\(target\)/);
  assert.match(implementation,/feature\.valid\[row\] && target\.valid\[row\]/);
  assert.match(implementation,/needed >= capacity/);
  assert.match(implementation,/return Ok\(new DenseSupervisedBatchF64/);
  assert.doesNotMatch(implementation,/define actor|self\.state/);
});
test("mask intersection preserves row provenance and feature/target alignment",()=>{
  const result=compactSupervised([1,2,3,4,5],[10,20,30,40,50],
      [true,false,true,true,true],[true,true,false,true,false],5);
  assert.deepEqual(result,{features:[1,4],targets:[10,40],rows:[0,3],count:2});
});
test("empty or fully null rows produce an empty, valid batch",()=>{
  assert.deepEqual(compactSupervised([],[],[],[],0),{features:[],targets:[],rows:[],count:0});
  assert.deepEqual(compactSupervised([1,2],[10,20],[false,false],[true,true],0),
      {features:[],targets:[],rows:[],count:0});
});
test("nonfinite unselected values cannot poison a selected batch",()=>{
  assert.deepEqual(compactSupervised([Infinity,2],[10,20],[false,true],[true,true],2),
      {features:[2],targets:[20],rows:[1],count:1});
  assert.throws(()=>compactSupervised([Infinity],[3],[true],[true],1),/NONFINITE/);
  assert.throws(()=>compactSupervised([1],[NaN],[true],[true],1),/NONFINITE/);
});
test("shape and capacity failures are fail-closed",()=>{
  assert.throws(()=>compactSupervised([1],[1,2],[true],[true,true],2),/ROW_MISMATCH/);
  assert.throws(()=>compactSupervised([1],[1],[true,true],[true],2),/INVALID_MASK/);
  assert.throws(()=>compactSupervised([1,2],[2,4],[true,true],[true,true],1),/BACKPRESSURE/);
  assert.throws(()=>compactSupervised([1],[1],[true],[true],-1),/INVALID_CAPACITY/);
});
test("arbitrary mask intersections match independently indexed reference",()=>{
  // Stable seeded generator makes this deterministic in any Node version.
  let seed=0x5aa56a3f;
  const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
  for(let trial=0;trial<200;trial++) {
    const n=rand()%36;
    const x=Array.from({length:n},(_,i)=>i+1);
    const y=x.map(v=>7*v+3);
    const xm=x.map(()=>!!(rand()&1));
    const ym=y.map(()=>!!(rand()&2));
    const actual=compactSupervised(x,y,xm,ym,n);
    const expected=x.map((v,i)=>i).filter(i=>xm[i]&&ym[i]);
    assert.deepEqual(actual.rows,expected);
    assert.deepEqual(actual.features,expected.map(i=>x[i]));
    assert.deepEqual(actual.targets,expected.map(i=>y[i]));
    assert.equal(actual.count,expected.length);
  }
});
test("OLS regression gradient over compacted rows matches finite differences",()=>{
  const batch=compactSupervised([1,99,3,4],[5,999,9,11],
      [true,false,true,true],[true,true,true,true],4);
  const loss=w=>batch.features.reduce((s,x,i)=>{
    const err=w*x-batch.targets[i];return s+err*err;
  },0)/batch.count;
  const w=1.75, epsilon=1e-6;
  const grad=batch.features.reduce((sum,x,i)=>
      sum+2*x*(w*x-batch.targets[i]),0)/batch.count;
  assert(Math.abs((loss(w+epsilon)-loss(w-epsilon))/(2*epsilon)-grad)<1e-7);
});
