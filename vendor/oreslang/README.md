# Vendored Oreslang testing framework

`testing.ores` is copied from:

- repository: `ores-truffle-oreslang/oreslang-source.java`
- core revision: `02ca2b2ca141f4570962c3911be5f0c8fd50c6bc`
- source blob: `5eee1995222165c579e4a75d403911e71dcff819`
- source path: `stdlib/testing.ores`

It is vendored so this repository's native tests are reproducible without a
cross-private-repository token.

The vendored file is based on the pinned core blob above, with the explicit
for-of declaration migration applied locally (`for const ... of ...`) so it
remains compatible with the hardened iterator grammar in core PR #239. Until
that grammar change is merged into the canonical testing source, do not claim
the vendored file is byte-for-byte identical to the pinned blob; audit any
additional local delta explicitly.
