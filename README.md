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

## Compiler PR checkpoint (2026-10-06)

A [repository-specific compiler compatibility matrix](docs/compiler-pr-sync.md) tracks the 10 newest `oreslang-source.java` PRs. They remain unmerged upstream; existing demos, build flags, and stable compiler references stay unchanged pending exact-SHA conformance testing.

## Runner CI and native-suite coverage

The `Test runner contracts` workflow checks shell syntax and uses a compiler
test double to prove repository-root execution, paths containing spaces,
explicit compiler selection, PATH fallback, exact output/exit-code propagation,
and failure when the compiler is missing. It uses read-only permissions and no
secrets. The runner now works when launched outside this repository.

This is a launcher gate, not numerical conformance evidence. A 2026-10-07 probe
against compiler `5ffc52d9297d175307094d530293c69f1cafc7cd` stopped at the
unexported `TestCase` class imported from `vendor/oreslang/testing.ores`.
Resolve exports and subsequent ownership diagnostics, then run the complete
native numerical suite before selecting a compiler pin and enabling runtime CI.

## Repository ownership and migration (2026-11-08)

**Current:** `ores-truffle-oreslang/oreslang-data-science` in the old Oreslang org. **Public language:** AttoLang. Retain existing `.ores` files and historical repository/package/CLI aliases until compiler-backed `.atto` support and consumers have been validated.

- **This repo owns:** AttoLang scientific data processing, statistics and tutorial algorithms.
- **Not owned here:** managed notebook product, SaaS tenant administration or cloud billing.
- **Organizations:** [atto-lang](https://github.com/atto-lang) is for language/compiler/tooling, portable ML/scientific libraries, conformance and demonstrations. [atto-co](https://github.com/atto-co) is for independently governed cloud hosting, deployment, tenant identity, billing and commercial services. Similar `atto-*` repo names do not imply transferred source ID or content parity.
- **Migration proposal:** identity-preserving GitHub transfer under the original repository name to `atto-lang/oreslang-data-science` after reviews. No legacy-org direct move to `atto-co` is currently authorized. Later commercialization spinouts need their own signed off runbook.

**Repository transfer gates:** coordinate a single owner/rollback plan at [issue #26](https://github.com/ores-truffle-oreslang/.github/issues/26); consult private [runbook #25](https://github.com/ores-truffle-oreslang/.github/pull/25). Record exact source commit SHA/tree and numeric ID, target visibility and protection/rulesets, source/target admin and independent security approvals, PRs/tags/releases, packages/import consumers, webhooks, GitHub Apps, Actions/billing/runners, secrets and Pages. Never mirror private source without separate approval. After actual GitHub transfer verify identical ID/history/tree, restore protections, update references independently and run exact-head CI with nonzero executed steps. `steps=[]`/`null` is `NOT_EXECUTED`; host/static tests cannot establish compiled AttoLang numerical or guest execution parity.
