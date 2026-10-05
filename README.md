# oreslang-data-science

Native Oreslang libraries for numerical computing, columnar data, statistics, data pipelines, and data-oriented programming.

The core library is intentionally implemented in **Oreslang**, not Java. The long-term target is a fast, ergonomic data-science stack with NumPy/pandas/Polars-class workflows while preserving Oreslang's scheduler, ownership, AOT, actor isolation, and heterogeneous CPU/GPU design.

## Initial native core

This first slice provides:

- scalar math helpers and checked square root;
- numerically stable reductions using Welford accumulation;
- dense vector transforms and BLAS-style operations such as `dot` and `axpy`;
- a contiguous row-major `DenseMatrixF64`;
- columnar `FloatColumn` / `FloatFrame` data structures;
- composable functional pipelines for map/filter/batching;
- Struct-of-Arrays data structures for data-oriented workloads.

All hot-path data is represented as typed `Array<float>` columns instead of boxed row objects.

## Example

```ores
import { mean, variance_sample } from "./src/math/reductions.ores";
import { scale } from "./src/math/vector.ores";

let Array<float> xs = new Array<float>(1.0, 2.0, 3.0, 4.0);
let Array<float> doubled = scale(xs, 2.0);

let avg = mean(doubled)?;
let variance = variance_sample(doubled)?;
```

## Design direction

The project is intentionally layered:

1. **math** — scalar math, reductions, dense vectors, matrices;
2. **data** — typed columns, frames, validity masks, chunked batches;
3. **pipeline** — composable transforms over contiguous batches;
4. **dop** — SoA/archetype-friendly layouts for cache-local processing;
5. later: CSV/Arrow/Parquet, lazy query plans, SIMD kernels, GPU placement, statistics, ML, visualization, and interop.

See [Architecture](docs/ARCHITECTURE.md) and [Roadmap](ROADMAP.md).
