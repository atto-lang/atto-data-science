# oreslang-data-science

Native Oreslang libraries for numerical computing, columnar data, data pipelines, embeddings/vector retrieval, and data-oriented programming.

The core library is intentionally implemented in **Oreslang**, not Java. The target is Python-class ergonomics with a data-oriented execution model that can grow toward NumPy/Polars-class numeric and columnar performance while preserving Oreslang ownership, AOT, actor isolation, scheduler semantics, and CPU/GPU placement.

## Native core

The current compiler-facing implementation provides:

- scalar math helpers and checked square root;
- numerically stable Welford mean/variance reductions;
- borrowed, allocation-free reductions such as `sum` and `dot`;
- owned in-place vector transforms such as `scale`, `axpy`, and L2 normalization;
- row-major `DenseMatrixF64` with caller-provided output buffers;
- row-major `EmbeddingBatch` values with model/revision identity;\n- padded `TokenEmbeddingBatch` hidden states plus attention masks;\n- mask-aware mean pooling with optional fused L2 normalization;\n- a batch-first `EmbeddingBackend` contract with caller-owned output buffers;
- embedding row normalization plus batch dot, cosine, and squared-L2 kernels;
- stable row-wise top-k selection;
- fused dot + top-k retrieval without materializing a full query-by-corpus score matrix;
- nullable columnar `FloatColumn` and `FloatFrame`;
- allocation-conscious map/filter pipeline primitives;
- Struct-of-Arrays point-cloud and particle data models.

Current core `main` represents typed sequences as `List<T>`. Read-only kernels use explicit borrows of the concrete list type; `@Structural` is reserved for explicit shape-based compatibility when a callable intentionally accepts values across nominal representation categories. Owned mutable buffers are used for transforms so a future dedicated contiguous `Array<T>` can replace the storage primitive without changing the higher-level execution model.

For embedding workloads, `List<float>` is explicitly the semantic reference representation, not the final hot-path layout. The performance target is aligned contiguous `Array<f32>` / `Array<f16>` / `Array<bf16>` storage with SIMD, multicore, and accelerator lowering.

## Example

```ores
import class EmbeddingBatch from './src/ml/embeddings';
import fnc top_k_dot_into from './src/ml/embeddings';

val EmbeddingBatch query = new EmbeddingBatch(
  1,
  3,
  arr[0.6, 0.8, 0.0],
  true,
  "my-model",
  "v1"
);

val EmbeddingBatch corpus = new EmbeddingBatch(
  3,
  3,
  arr[
    0.6, 0.8, 0.0,
    1.0, 0.0, 0.0,
    0.0, 0.0, 1.0
  ],
  true,
  "my-model",
  "v1"
);

val List<int> indices = arr[0, 0];
val List<float> scores = arr[0.0, 0.0];

top_k_dot_into(&query, &corpus, 2, indices, scores)
  .expect("retrieval failed");
```

For normalized embeddings, cosine ranking is dot-product ranking. Normalize once after model pooling, then reuse `top_k_dot_into` for repeated retrieval.

See [Embedding architecture](docs/EMBEDDINGS.md) for the batch inference, actor microbatching, contiguous-array, SIMD, and GPU direction.

## Native tests

The repository uses the Oreslang-native framework from core PR #233. A pinned copy is kept at `vendor/oreslang/testing.ores` so tests need no Java/JUnit dependency and no cross-repository token.

```sh
ORESLANG_BIN=/path/to/oreslang ./scripts/test.sh
```

The test script runs both the numerical/data suite and the embedding/vector suite.

See [Architecture](docs/ARCHITECTURE.md) and [Roadmap](ROADMAP.md).
