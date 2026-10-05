# Architecture

## Objective

Make data science a first-class Oreslang workload instead of wrapping a Java or Python implementation.

The public API should remain concise enough for exploratory work while the storage/execution model stays friendly to AOT compilation, CPU caches, vectorization, parallel scheduling, and GPU placement.

## Principles

### Native Oreslang userland

Core algorithms and tests live in `.ores` files. Java is not the implementation language for this library. Runtime/compiler intrinsics may later optimize recognized kernels while preserving the Oreslang reference semantics.

### Borrow for reads, own writes

Reductions accept read-only borrows such as `&List<float>`; transforms take ownership of mutable buffers and return them. Matrix, filtering, and SoA kernels accept caller-provided destination buffers rather than requiring hidden allocation.

This is both ownership-safe and a good lowering boundary for a future native contiguous `Array<T>`.

### Columnar by default

Rows are convenient at boundaries; columns are the execution representation. Nullable columns store values separately from validity metadata, so reductions scan dense numeric buffers rather than boxed row objects.

### Data-oriented layouts

Performance-sensitive multi-field data uses Struct-of-Arrays layouts. Current core `main` expresses these as data-only classes; behavior remains in free systems/functions. Once source-level structs are finalized, the container syntax can migrate without changing the DOP layout.

### Batch pipelines

Pipelines operate on typed buffers rather than boxed records. The current implementation favors in-place map and destination-buffer compaction. Later compiler/library work can fuse adjacent kernels, vectorize, choose chunk sizes, and place work on CPU/GPU.

### Explicit errors

Shape mismatches, empty reductions, invalid frames, invalid numeric domains, and undersized destination buffers return `Result<T,E>`.

## Native testing

`tests/main.ores` uses the core native testing framework, pinned under `vendor/oreslang/testing.ores`. Tests are ordinary Oreslang code and emit the stable `ORES_TEST|...` event protocol.

## Performance direction

Candidate compiler/runtime intrinsics can specialize:

- Welford reductions;
- dot/axpy/matvec;
- validity-mask scans;
- map/filter fusion;
- chunked parallel execution;
- SIMD;
- GPU task placement when data/effects make that safe.

The pure Oreslang implementation remains the semantic reference.
