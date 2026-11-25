> **AI agent instructions (organization-wide):** Before working on code, issues, or pull requests, read and follow the [organization `AGENTS.md`](https://github.com/atto-lang/.github/blob/main/AGENTS.md), including its **merge-first stealth-development policy**. Honor any repository-local `AGENTS.md`, explicit holds, and GitHub-enforced rules.

# atto-data-science

Data analysis, scientific computing, and statistical programming tools for AttoLang.

## Naming migration and language authority

This repository is maintained at [atto-lang/atto-data-science](https://github.com/atto-lang/atto-data-science); use `https://github.com/atto-lang/atto-data-science.git` for Git remotes and canonical `.atto` source examples. The normative language contract is [atto-spec](https://github.com/atto-lang/atto-spec), with executable guest evidence tracked by [atto-platform-conformance](https://github.com/atto-lang/atto-platform-conformance). Follow current ownership, borrowing, effects, actor, and syntax rules there; do not infer implemented features from a README or unexecuted CI.

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

AttoLang is the canonical project name; new source, examples and documentation use `.atto` and the `atto-lang` repository organization. This README defines scope, not feature readiness.

**Acceptance:** name exact source SHA/tree, runtime/toolchain, positive and negative checks and execution receipt before claiming support. Host-only tests and empty CI steps do not prove guest execution.

## Online statistics reference (host-only)

`reference/moments.py` implements immutable incremental Welford mean/population and sample variance, plus deterministic pairwise summary merging for partitioned data. It rejects nonfinite/boolean samples, arithmetic overflow and unsupported sample counts. Run `python3 -m unittest discover -s tests -v` to exercise simple, partitioned and invalid-input cases.

This is a Python numerical reference, **not** an AttoLang guest implementation. Floating-point reduction ordering can change results; future backend conformance needs explicitly pinned numeric precision, sample order, tolerances and actual target execution receipts.

## Legacy migration and verification gates

The historical predecessor was `ores-truffle-oreslang/oreslang-data-science`. This repository is now maintained in `atto-lang`; naming or imported history does not establish preservation of the original numeric repository ID, code parity or compiler support. Preserve working legacy `.ores` inputs and historical package/CLI aliases until replacement paths have been verified; new source follows canonical `.atto` contracts.

Scientific data processing, statistics and tutorial algorithms belong here; managed notebook products, tenant administration and cloud billing do not. [atto-lang](https://github.com/atto-lang) owns language, tooling and portable libraries; [atto-co](https://github.com/atto-co) separately governs commercial deployment, tenant infrastructure, identity, registry and billing. Any further original-ID transfer or managed-product carve-out requires separate owner authorization. This document authorizes no direct legacy-org transfer to atto-co.

Before an actual transfer, coordinate through [migration issue #26](https://github.com/ores-truffle-oreslang/.github/issues/26) and authorized source/target administrators and independent security reviewers. Inventory repository numeric ID, exact head/tree, history, visibility, access, rulesets, open PRs, releases, packages, CI/runners, secrets, deploy keys, apps, webhooks, Pages, consumers and rollback ownership. Never mirror private source without authorization. Verify unchanged ID/history/tree and restored controls after transfer, then execute exact-head tests before changing consumer references. Zero-step CI is NOT_EXECUTED; host-only and source-free tests are not compiled guest evidence.
