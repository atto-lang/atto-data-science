# CPU column-to-ML batch and reverse-gradient bridge

**Status:** Draft. This adds real Oreslang source algorithms on the existing `List<float>` / `List<int>` reference substrate. It does not yet prove executable Java/GraalVM or LLVM guest compilation and is not `Tensor<T>`/Arrow/GPU support.

## New API

- `compact_valid_f64_into(FloatColumn, values_out, source_rows_out)`: prevalidate mask, selected values, capacity and aliasing, then write a stable compacted dense batch and original row IDs.
- `scatter_add_f64_into(gradients, source_rows, count, destination, scratch)`: bounds/finite prevalidation, scratch copy, duplicate-aware gradient accumulation into scratch, then publish into destination only after every contribution is finite.

These are **CPU data kernels**; no new runtime or actor type is invented. Both APIs use explicitly mutable caller-provided output buffers and preserve original source storage. Scatter makes destination failure-atomic, but scratch may be altered on a failed arithmetic operation; a caller must treat scratch as expendable. Buffer memory and count caps must be enforced by the caller until native bounded `Array<T>` allocation is available. Empty inputs are legal. Values under false validity bits are excluded; present NaN/Infinity values fail closed.

## End-to-end example

`examples/nullable_ml_batch_scatter.ores` demonstrates nullable feature input `[2,null,4,6]` compacted to `[2,4,6]` with source rows `[0,2,3]`, and gradient rows `[0,2,2,3]` accumulating `[1,3,5,7]` into `[1,0,8,7]`. Expected success marker: `ORES_ML_BATCH_PASS`.

In a model, row identities must be carried in versioned training-context messages (run, graph, step, microbatch, edge, actor epoch, parameter version). On backward, autograd computes gradients outside actor-state loans, then the data bridge scatter-adds into an owned gradient buffer before state publication. The data stage's persistent user-owned buffers/cursors/receipts belong to its **sole** `state { ... }`, accessed only through `with` effect bounds and lexical `using` / sealed `handle_state`. No state loan survives I/O, select, await or an actor send. A reader-writer gate protects actor state transactions, not the numerical kernel's full execution time.

## Boundary to existing repos

- `oreslang-tensor` remains the authority for generic n-dimensional tensor descriptors, contiguous storage, shape checks and accelerated kernels.
- `oreslang-autograd` owns graph VJPs, versioned saved activations, reverse-edge accumulation and gradient tape.
- `oreslang-ml` owns model/layer/optimizer semantics and actor pipeline training.
- `oreslang-data-science` owns ingestion, columnar validity, tabular transforms, batch materialization and row-provenance preservation.
- `oreslang-common-source` owns language/effect/actor-state declarations, typed message contracts and compiler/back-end conformance.

The batch bridge is an adapter, **not a second tensor implementation**; future `Array<T>`, Arrow validity/offset buffers, independent row index leases and tensor-owned storage should replace the temporary list-backed reference without changing the shape/lineage/error contract.

## Verification and launch gates

1. The isolated host-only numerical oracle exercises mask/overflow/error atomicity, repeated-index scatter and finite difference gradients. This is a reference, not compiled Oreslang guest behavior.
2. Run `node --test tests/ml_batch_bridge_oracle.test.mjs` using an available Node 22 runner; the workflow labels evidence `HOST_ONLY`.
3. Compile/run `examples/nullable_ml_batch_scatter.ores` on pinned current GraalVM Java source. Require exactly `ORES_ML_BATCH_PASS` and negative error/alias fixtures.
4. Integrate with `oreslang-tensor` contiguous buffers and `oreslang-autograd` verified VJPs, then test real actor stages, cancellation, backpressure and parameter version fences.
5. LLVM AOT parity, SIMD/columnar benchmarks, device-lease/copy tests and multi-shard distributed training remain independent gates.

Never treat passing a JS oracle or a proposed source contract as proof of an Oreslang compiler, GPU or external Arrow/Parquet interoperability. Private Git trees must not be mirrored outside authorized organizations for CI without explicit authorization.
