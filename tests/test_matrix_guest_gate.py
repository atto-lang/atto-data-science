"""Fail-closed source-local matrix guest runner contracts.

No private source export and no real compiler are used by these tests.
"""
import os
from pathlib import Path
import shutil
import subprocess
import unittest
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/test-matrix-source-local.sh"


class MatrixGuestGateTests(unittest.TestCase):
    def test_script_is_valid_bash(self):
        bash = shutil.which("bash")
        self.assertIsNotNone(bash)
        run = subprocess.run([bash, "-n", str(GATE)],
                             capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_missing_approvals_reject_before_binary_execution(self):
        run = subprocess.run(["bash", str(GATE)],
                             env={"PATH": os.environ.get("PATH", "")},
                             cwd=str(ROOT), capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("EXPECTED_SOURCE_SHA", run.stderr)

    def test_bad_identity_fails_closed(self):
        env = {
            "PATH": os.environ.get("PATH", ""),
            "EXPECTED_SOURCE_SHA": "a" * 39,
            "EXPECTED_SOURCE_TREE": "b" * 40,
            "EXPECTED_COMPILER_SHA256": "c" * 64,
            "ORESLANG_BIN": "/bin/true",
            "MATRIX_EVIDENCE_DIR": "/tmp/matrix-no-execution",
        }
        run = subprocess.run(["bash", str(GATE)],
                             env=env, cwd=str(ROOT),
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 65)
        self.assertIn("malformed commit identity", run.stderr)

    def test_symlinked_compiler_rejected_before_checkout(self):
        with tempfile.TemporaryDirectory() as folder:
            executable = Path(folder) / "compiler"
            executable.symlink_to("/bin/true")
            env = {
                "PATH": os.environ.get("PATH", ""),
                "EXPECTED_SOURCE_SHA": "a" * 40,
                "EXPECTED_SOURCE_TREE": "b" * 40,
                "EXPECTED_COMPILER_SHA256": "c" * 64,
                "ORESLANG_BIN": str(executable),
                "MATRIX_EVIDENCE_DIR": folder,
            }
            run = subprocess.run(["bash", str(GATE)], env=env,
                                 cwd=str(ROOT), capture_output=True, text=True)
            self.assertEqual(run.returncode, 65)
            self.assertIn("compiler symlink", run.stderr)

    def test_post_execution_revalidates_source_and_compiler(self):
        source = GATE.read_text(encoding="utf-8")
        for check in ("compiler binary changed during execution",
                      "source HEAD changed during execution",
                      "source tree changed during execution",
                      "source checkout modified during guest execution"):
            self.assertIn(check, source)

    def test_native_gate_requires_every_matrix_fixture_exactly_once(self):
        source = GATE.read_text(encoding="utf-8")
        for case in (
            "matrix/matvec",
            "matrix/short-storage",
            "matrix/valid-get",
            "matrix/overflow",
            "matrix/zero-extent",
            "matrix/bounds-and-negative",
            "matrix/zero-column-matvec",
            "matrix/short-matrix-preflight",
            "matrix/short-vector-preflight",
            "matrix/rectangular-matvec",
            "matrix/last-index",
            "matrix/negative-row-read",
            "matrix/zero-by-zero",
            "matrix/zero-rows-matvec",
            "matrix/short-output-preflight",
            "matrix/zero-extent-extra-storage",
            "matrix/negative-column-extent",
        ):
            with self.subTest(case=case):
                self.assertIn("  " + case + "\n", source)
        self.assertIn('grep -Fxc "ORES_TEST|PASS|data-science/$test_name|"', source)
        self.assertIn('[[ "$marker_count" = 1 ]]', source)

    def test_no_source_export_or_test_double_is_in_gate(self):
        source = GATE.read_text(encoding="utf-8")
        for required in ("git -C", "HEAD^{tree}", "sha256sum",
                         "ORES_TEST|PASS|data-science/$test_name|",
                         "GUEST_EXECUTED_ONLY_NO_BACKEND_PARITY"):
            self.assertIn(required, source)
        for forbidden in ("git clone", "curl ", "wget ", "pip install",
                          "GITHUB_TOKEN", "gh repo fork"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
