# Architecture

## Objective

Make data science a first-class Oreslang workload instead of wrapping a Java or Python implementation.

The public API should feel concise enough for notebook-style exploration while the storage/execution model remains friendly to AOT compilation, CPU caches, vectorization, parallel scheduling, and eventually GPU placement.

## Principles

### Native Oreslang userland

Core algorithms live in `.ores` files. Java is not the implementation language for the data-science library. Runtime intrinsics are allowed later as compiler/runtime optimizations, but they must preserve the same Oreslang API and semantics.

### Columnar by default

Rows are convenient at boundaries; columns are the execution representation. Typed columns use contiguous arrays plus validity metadata. This allows reductions and transforms to walk dense memory instead of chasing object references.

### Data-oriented layouts

Performance-sensitive multi-field data uses Struct-of-Arrays layouts. Components remain data-only and systems are free functions. This matches the wider Oreslang ECS/DOP direction and gives the compiler analyzable read/write sets.

### Batch pipelines

Pipelines operate on arrays and batches, not individual boxed records. The first implementation is eager and simple. The API is designed so later compiler/library work can fuse adjacent maps/filters, choose chunk sizes, vectorize kernels, or place work on CPU/GPU without rewriting user programs.

### Explicit errors

Shape mismatches, empty reductions, invalid frames, and invalid numeric domains return `Result<T,E>`. Data-science code should not silently invent dimensions or coerce malformed inputs.

## Layers

- `src/math/scalar.ores`: scalar primitives.
- `src/math/reductions.ores`: stable reductions.
- `src/math/vector.ores`: vector transforms and BLAS-style primitives.
- `src/math/matrix.ores`: contiguous dense matrix foundation.
- `src/data/columnar.ores`: typed columns and frames.
- `src/pipeline/pipeline.ores`: composable array/batch stages.
- `src/dop/soa.ores`: explicit SoA types and systems.

## Performance direction

The important future optimization boundary is not “call Java.” It is “recognize Oreslang kernels.”

Candidate compiler/runtime intrinsics can specialize:

- reduction loops;
- dot/axpy/matvec;
- validity-mask scans;
- map/filter fusion;
- chunked parallel execution;
- SIMD;
- GPU task placement when effects/data access make that safe.

The pure Oreslang implementation remains the semantic reference.
