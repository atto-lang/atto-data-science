# Canonical NdArray / owned storage ABI v1 — proposed acceptance contract

Status: **DESIGN + HOST REFERENCE ONLY; NOT AN EXECUTED ORESLANG GUEST ABI.**

Canonical source-level owner: `oreslang-data-science` ([issue #9](https://github.com/ores-truffle-oreslang/oreslang-data-science/issues/9)).
`oreslang-tensor` ([issue #2](https://github.com/ores-truffle-oreslang/oreslang-tensor/issues/2)) wraps canonical owned storage with tensor operations and layouts, and `oreslang-autograd` ([issue #2](https://github.com/ores-truffle-oreslang/oreslang-autograd/issues/2)) consumes immutable saved-forward views. **No independent second ndarray allocator.**

## Descriptor and resource obligations

- A nominal `NdArray<T>` owns one contiguous `Array<T>` storage authority. The runtime validates dtype, itemsize, storage extent, alignment, generation and tenant/actor ownership before making any view.
- Rank is bounded; rank-zero tensors contain one scalar; any zero extent yields zero elements *after every shape dimension has been validated*. Shapes are nonnegative integer extents, not float-coerced values.
- Every arithmetic operation involving shape product, element/byte count, offset, and stride is checked before allocation or dereference. Reject overflow and unsupported dtype/device with a typed error.
- For the host ABI reference, strides and offsets use **bytes**; typed tensor APIs may describe strides in elements but must convert to bytes using checked multiplication at a single boundary. Descriptor conversions must not silently change units.
- A zero-element view has no reachable elements but must still validate **all** stride types/ranges/alignment and its owner-bound aligned offset.
- A mutable view requires compiler-verifiable exclusive write authority and address non-overlap, not just a bounding interval. Read-only broadcast/zero-stride views may be allowed; mutable broadcast aliases are rejected.
- Owner generations and lease tokens may never wrap or be reused. A failed acquisition does not publish a loan; a taken/retired owner invalidates old generations and all outstanding derived authority.
- `rt borrow`, `rt take`, and `rt share` are explicit Oreslang semantics; do not expose `&`, `*` pointer forms, runtime reflection, or implicit conversions in guest APIs.
- Cross-actor or cross-tenant ownership changes must authenticate the destination and atomically revoke the sender's writable authority; a Python `BorrowBook` token is a model, not a runtime capability.

## Smallest conformance matrix

| Case | Positive | Negative |
|---|---|---|
| Scalar / zero | rank 0 has one element; zero extent has none | invalid dimension after zero; invalid strides on empty view |
| Bounds | aligned row-major and reversed views | overflow, out-of-storage offset, unaligned byte stride, mismatched rank |
| Aliasing | exclusive disjoint mutable slices | overlapping mutable writes, zero-stride broadcast writer |
| Lifetime | borrow, release, take, legitimate fresh generation | duplicate release, stale generation, exhausted lease token, use-after-take |
| Integration | tensor matmul and autograd saved-forward view | alias into optimizer output; cross-actor stale view; guest rejection oracle |

## Evidence hierarchy / release gate

1. `scripts/verify_ndarray_layout.py` and `tests/test_ndarray_*.py` are **host reference** evidence only.
2. A nonzero-step, exact-head source-org test run is needed even for the host model; `steps=[]` is runner admission failure.
3. Compile and execute exact-source `.ores` positive and negative fixtures against reviewed Java/Graal and LLVM compiler SHAs. Bind source and compiler tree SHA, target, stdout/exit status and runtime job steps.
4. Do not claim compile-time borrow exclusivity, physical actor heap isolation, LLVM parity, or native tensor storage until those corresponding tests actually execute.

Do not export private source into a different organization merely to obtain Actions minutes. A mirror requires separate destination-specific authorization and exact-tree verification.
