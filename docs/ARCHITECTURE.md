# Architecture

## Objective

Make data science and embedding/vector workloads first-class Oreslang workloads instead of wrapping a Java or Python implementation.

The public API should remain concise enough for exploratory work while the storage/execution model stays friendly to AOT compilation, CPU caches, vectorization, parallel scheduling, actor isolation, and GPU placement.

## Principles

### Native Oreslang userland

Core algorithms and tests live in `.ores` files. Java is not the implementation language for this library. Runtime/compiler intrinsics may later optimize recognized kernels while preserving the Oreslang reference semantics.

### Borrowed reads, owned writes

Read-only sequence kernels accept borrowed concrete lists such as `List<float>` on the current core surface. `@Structural` is a type-compatibility escape hatch for intentionally shape-matched class/interface/trait contracts; it is not an ownership or read-only marker for ordinary collections. Transforms take ownership of mutable buffers and return them. Matrix, embedding, filtering, and SoA kernels accept caller-provided destination buffers rather than requiring hidden allocation.

This keeps access/ownership semantics separate from nominal-versus-structural type compatibility and remains a clean lowering boundary for a future native contiguous `Array<T>`.

### Columnar and row-major numeric storage

Rows are convenient at boundaries; columns are the execution representation for dataframe work. Nullable columns store values separately from validity metadata, so reductions scan dense numeric buffers rather than boxed row objects.

Dense matrix and embedding workloads use flat row-major numeric storage. An embedding batch is `[rows, dimensions]`, not a list of boxed vector objects. That layout maps directly to SIMD loops, GEMM-like kernels, tiled multicore execution, and device buffers.

### Embeddings are batch-first

Single-text embedding is an ergonomic special case of batch embedding, not the runtime primitive. The target flow is tokenizer -> batch builder -> model inference -> pooling -> normalization -> `EmbeddingBatch`.

A resident embedding model should be actor-owned. Concurrent callers send work to the model actor, which may coalesce mailbox requests into microbatches before inference and resolve individual Futures afterward. Actor ownership keeps model/session/device state isolated and gives the scheduler a natural place to enforce quotas and cancellation.

Queued requests must be removable immediately on cancellation. Running device work should use backend cancellation when supported; no design should depend on cooperative polling for cancellation correctness.

### Retrieval avoids unnecessary materialization

Pairwise score matrices are useful, so dot/cosine/L2 kernels support caller-owned `[query_rows, corpus_rows]` outputs.

For the common retrieval case, `top_k_dot_into` fuses score computation and ranking. It keeps only `[query_rows, k]` indices/scores and does not allocate the full score matrix. For normalized embeddings this is also the preferred cosine-retrieval path.

### Data-oriented layouts

Performance-sensitive multi-field data uses Struct-of-Arrays layouts. Current core `main` expresses these as data-only classes; behavior remains in free systems/functions. Once source-level structs are finalized, the container syntax can migrate without changing the DOP layout.

### Batch pipelines

Pipelines operate on typed buffers rather than boxed records. The current implementation favors in-place map and destination-buffer compaction. Later compiler/library work can fuse adjacent kernels, vectorize, choose chunk sizes, and place work on CPU/GPU.

### Explicit errors

Shape mismatches, empty reductions, invalid frames, invalid embedding batches, zero-norm cosine inputs, and undersized destination buffers return `Result<T,E>`.

## Native testing

`tests/main.ores` and `tests/embeddings.ores` use the core native testing framework, pinned under `vendor/oreslang/testing.ores`. Tests are ordinary Oreslang code and emit the stable `ORES_TEST|...` event protocol.

## Performance direction

Candidate compiler/runtime intrinsics can specialize:

- Welford reductions;
- dot/axpy/matvec;
- embedding row normalization;
- pairwise dot/cosine/squared-L2;
- fused dot + top-k;
- pooling + normalization;
- validity-mask scans;
- map/filter fusion;
- chunked parallel execution;
- SIMD;
- GPU task placement when data/effects make that safe.

Known embedding dimensions are especially attractive AOT specialization points because loop trip counts and alignment/tile decisions can be fixed ahead of time while retaining a generic dynamic-dimension fallback.

The pure Oreslang implementation remains the semantic reference.
