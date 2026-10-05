# oreslang-data-science

Native Oreslang libraries for numerical computing, columnar data, data pipelines, and data-oriented programming.

The core library is intentionally implemented in **Oreslang**, not Java. The target is Python-class ergonomics with a data-oriented execution model that can grow toward NumPy/Polars-class numeric and columnar performance while preserving Oreslang ownership, AOT, actor isolation, scheduler semantics, and CPU/GPU placement.

## Native core

The current compiler-facing implementation provides:

- scalar math helpers and checked square root;
- numerically stable Welford mean/variance reductions;
- borrowed, allocation-free reductions such as `sum` and `dot`;
- owned in-place vector transforms such as `scale`, `axpy`, and L2 normalization;
- row-major `DenseMatrixF64` with caller-provided output buffers;
- nullable columnar `FloatColumn` and `FloatFrame`;
- allocation-conscious map/filter pipeline primitives;
- Struct-of-Arrays point-cloud and particle data models.

Current core `main` represents typed sequences as `List<T>`. Oreslang object values are references and ordinary arguments are passed by reference: passing `values` does not copy the object and does not require address-of syntax. Oreslang source does **not** expose raw pointers: `&` is not an address-of/borrow operator, unary `*` is not a dereference operator, and pointer arithmetic is not part of userland Oreslang. (`*` remains the ordinary multiplication operator.)

Ownership and access changes are explicit operations: `rt copy`, `rt borrow`, `rt take`, and `rt share`. Mutation authority is expressed with `mut`, not with `&mut` or pointer types. `@Structural` remains reserved for explicit shape-based compatibility when a callable intentionally accepts values across nominal representation categories. Mutable buffers are used for transforms so a future dedicated contiguous `Array<T>` can replace the storage primitive without changing the higher-level execution model.

## Example

```ores
import fnc mean from './src/math/reductions';
import fnc scale from './src/math/vector';

val List<float> values = arr[1.0, 2.0, 3.0, 4.0];
val List<float> doubled = scale(values, 2.0);

// Ordinary object arguments are references. No '&' or '*' pointer syntax is used.
val Result<float, String> average = mean(doubled);
stdio.stdout.println(average.expect("mean failed"));
```

## Native tests

The repository uses the Oreslang-native framework from core PR #233. A pinned copy is kept at `vendor/oreslang/testing.ores` so tests need no Java/JUnit dependency and no cross-repository token.

```sh
ORESLANG_BIN=/path/to/oreslang ./scripts/test.sh
```

The suite in `tests/main.ores` covers scalar math, stable reductions, shape errors, vector normalization, dense matvec, nullable column means, and SoA particle energy.

See [Architecture](docs/ARCHITECTURE.md) and [Roadmap](ROADMAP.md).
