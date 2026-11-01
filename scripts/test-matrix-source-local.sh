#!/usr/bin/env bash
# Exact-source, exact-compiler guest execution gate. Source-org only.
# No downloads, tokens, cross-organization checkout or test doubles.
set -euo pipefail

fail() { printf 'MATRIX_GUEST_NOT_CERTIFIED: %s\n' "$*" >&2; exit 65; }
root="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
: "${EXPECTED_SOURCE_SHA:?Set reviewed 40-hex source commit}"
: "${EXPECTED_SOURCE_TREE:?Set reviewed 40-hex root Git tree}"
: "${EXPECTED_COMPILER_SHA256:?Set reviewed 64-hex compiler binary SHA256}"
: "${ORESLANG_BIN:?Set absolute path to reviewed executable}"
: "${MATRIX_EVIDENCE_DIR:?Set absolute output directory outside repo}"

[[ "$EXPECTED_SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "malformed commit identity"
[[ "$EXPECTED_SOURCE_TREE" =~ ^[0-9a-f]{40}$ ]] || fail "malformed root-tree identity"
[[ "$EXPECTED_COMPILER_SHA256" =~ ^[0-9a-f]{64}$ ]] || fail "malformed compiler identity"
[[ "$ORESLANG_BIN" = /* && -f "$ORESLANG_BIN" && -x "$ORESLANG_BIN" ]] || fail "reviewed executable absent"
[[ ! -L "$ORESLANG_BIN" ]] || fail "compiler symlink is not an immutable binary pin"
[[ "$MATRIX_EVIDENCE_DIR" = /* ]] || fail "evidence directory must be absolute"
head_sha="$(git -C "$root" rev-parse --verify HEAD)"
root_tree="$(git -C "$root" rev-parse --verify 'HEAD^{tree}')"
[[ "$head_sha" = "$EXPECTED_SOURCE_SHA" ]] || fail "source commit mismatch"
[[ "$root_tree" = "$EXPECTED_SOURCE_TREE" ]] || fail "source tree mismatch"
[[ -z "$(git -C "$root" status --porcelain --untracked-files=all)" ]] || fail "dirty checkout"

if command -v sha256sum >/dev/null 2>&1; then
  compiler_sha="$(sha256sum "$ORESLANG_BIN" | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
  compiler_sha="$(shasum -a 256 "$ORESLANG_BIN" | awk '{print $1}')"
else
  fail "no SHA-256 binary hashing utility"
fi
[[ "$compiler_sha" = "$EXPECTED_COMPILER_SHA256" ]] || fail "compiler binary SHA-256 mismatch"

mkdir -p -- "$MATRIX_EVIDENCE_DIR"
evidence_root="$(cd -- "$MATRIX_EVIDENCE_DIR" && pwd -P)"
case "$evidence_root/" in
  "$root/"*) fail "evidence output must not modify the source checkout" ;;
esac
out="$(mktemp -d "$evidence_root/matrix-guest.XXXXXXXX")"
log="$out/guest-output.log"
if ! ORESLANG_BIN="$ORESLANG_BIN" "$root/scripts/test.sh" >"$log" 2>&1; then
  printf 'MATRIX_GUEST_FAILED: runner output in %s\n' "$log" >&2
  exit 1
fi
# Every native matrix case must execute exactly once on this pinned tree.
# Duplicate PASS markers cannot manufacture extra credit.
required_matrix_cases=(
  matrix/matvec
  matrix/short-storage
  matrix/valid-get
  matrix/overflow
  matrix/zero-extent
  matrix/bounds-and-negative
  matrix/zero-column-matvec
  matrix/short-matrix-preflight
  matrix/short-vector-preflight
  matrix/rectangular-matvec
  matrix/last-index
  matrix/negative-row-read
  matrix/zero-by-zero
  matrix/zero-rows-matvec
  matrix/short-output-preflight
  matrix/zero-extent-extra-storage
  matrix/negative-column-extent
)
for test_name in "${required_matrix_cases[@]}"; do
  marker_count="$(grep -Fxc "ORES_TEST|PASS|data-science/$test_name|" "$log" || true)"
  [[ "$marker_count" = 1 ]] \
    || fail "expected exactly one guest PASS marker for $test_name; found $marker_count (log $log)"
done
grep -Eq '^ORES_TEST\|SUMMARY\|total=[0-9]+\|passed=[0-9]+\|failed=0\|' "$log" \
  || fail "missing fail-free test summary (log $log)"
# Fail closed if the compiler changed between identity preflight and guest
# execution. This does not transitively certify compiler dependencies.
if command -v sha256sum >/dev/null 2>&1; then
  actual_sha_after="$(sha256sum "$ORESLANG_BIN" | awk '{print $1}')"
else
  actual_sha_after="$(shasum -a 256 "$ORESLANG_BIN" | awk '{print $1}')"
fi
[[ "$actual_sha_after" = "$EXPECTED_COMPILER_SHA256" ]] || fail "compiler binary changed during execution"
[[ "$(git -C "$root" rev-parse --verify HEAD)" = "$EXPECTED_SOURCE_SHA" ]] || fail "source HEAD changed during execution"
[[ "$(git -C "$root" rev-parse --verify 'HEAD^{tree}')" = "$EXPECTED_SOURCE_TREE" ]] || fail "source tree changed during execution"
[[ -z "$(git -C "$root" status --porcelain --untracked-files=all)" ]] || fail "source checkout modified during guest execution"
printf 'MATRIX_GUEST_EXACT_SOURCE=%s\n' "$head_sha"
printf 'MATRIX_GUEST_ROOT_TREE=%s\n' "$root_tree"
printf 'MATRIX_GUEST_COMPILER_SHA256=%s\n' "$compiler_sha"
printf 'MATRIX_GUEST_LOG=%s\n' "$log"
printf 'MATRIX_GUEST_CERTIFICATE=GUEST_EXECUTED_ONLY_NO_BACKEND_PARITY\n'
