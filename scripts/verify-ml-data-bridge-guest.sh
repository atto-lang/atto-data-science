#!/bin/sh
# Fail-closed real Oreslang guest gate. Invocation:
# ORESLANG_BIN=/path/to/pinned/oreslang sh scripts/verify-ml-data-bridge-guest.sh
# Unlike the Node oracles, this actually invokes the guest compiler/runtime.
set -eu
if [ -z "${ORESLANG_BIN:-}" ]; then
  echo "ORESLANG_BIN must point to the audited pinned Oreslang CLI" >&2
  exit 64
fi
if ! [ -x "$ORESLANG_BIN" ]; then
  echo "ORESLANG_BIN does not identify an executable file" >&2
  exit 64
fi
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT INT TERM
for case_name in nullable_ml_batch_scatter supervised_ml_batch; do
  input="$root/examples/$case_name.ores"
  case "$case_name" in
    nullable_ml_batch_scatter) marker=ORES_ML_BATCH_PASS ;;
    supervised_ml_batch) marker=ORES_SUPERVISED_ML_BATCH_PASS ;;
    *) echo "unexpected fixture" >&2; exit 70 ;;
  esac
  printf '%s\n' "$marker" > "$tmp/expected"
  if ! "$ORESLANG_BIN" "$input" > "$tmp/actual" 2> "$tmp/stderr"; then
    cat "$tmp/stderr" >&2
    echo "ORESLANG_GUEST_EXECUTION=FAILED fixture=$case_name" >&2
    exit 1
  fi
  if ! cmp -s "$tmp/expected" "$tmp/actual"; then
    diff -u "$tmp/expected" "$tmp/actual" >&2 || true
    cat "$tmp/stderr" >&2
    echo "ORESLANG_GUEST_OUTPUT_MISMATCH fixture=$case_name" >&2
    exit 1
  fi
  echo "ORESLANG_GUEST_FIXTURE_PASS fixture=$case_name"
done
echo "ORESLANG_GUEST_OUTPUT_GATE_PASS count=2"
