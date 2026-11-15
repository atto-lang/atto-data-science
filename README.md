# atto-data-science

Data analysis, scientific computing, and statistical programming tools for AttoLang.

## Scope

Data processing, numerical utilities, scientific workflows, and portable computing examples.

## API and portability principles

- Specify numerical/semantic behavior before assuming support on every backend.
- Document input types, error behavior, shape and memory ownership requirements as applicable.
- Distinguish CPU execution, SIMD, GPU offload, and other target-specific capabilities.

## Verification

Use checked-in tests, documented tolerances, and exact-commit runtime evidence. Host-only or compilation tests are not equivalent to executed AttoLang guest tests. Record backend gaps explicitly.

## Development status

This describes the repository's intended purpose, not a verified list of implemented features. Refer to checked-in code and CI for current functionality and validated commands.

## Related

- [AttoLang](https://github.com/atto-lang)
- [ML conformance](https://github.com/atto-lang/atto-ml-conformance)
- [Language specification](https://github.com/atto-lang/atto-spec)

## Repository ownership and contribution routing

**Belongs here:** AttoLang statistical and scientific workflows, data tables/transformations, numerical recipes and reproducible analysis examples.

**Belongs elsewhere:** Tensor kernels in atto-tensor; model training in atto-ml; differentiation in atto-autograd.

**Security and portability boundary:** Define missing-data, overflow, precision, provenance and resource-limit behavior; check example results against pinned executed backend fixtures.

AttoLang is the public name; preserve existing Oreslang/.ores compatibility and use canonical .atto for new portable library source. This README defines scope, not feature readiness.

**Acceptance:** name exact source SHA/tree, runtime/toolchain, positive and negative checks and execution receipt before claiming support. Host-only tests and empty CI steps do not prove guest execution.

## Online statistics reference (host-only)

`reference/moments.py` implements immutable incremental Welford mean/population and sample variance, plus deterministic pairwise summary merging for partitioned data. It rejects nonfinite/boolean samples, arithmetic overflow and unsupported sample counts. Run `python3 -m unittest discover -s tests -v` to exercise simple, partitioned and invalid-input cases.

This is a Python numerical reference, **not** an AttoLang guest implementation. Floating-point reduction ordering can change results; future backend conformance needs explicitly pinned numeric precision, sample order, tolerances and actual target execution receipts.
