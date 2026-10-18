"""Source-local guard against stale/non-public vendored Oreslang test exports.

This verifies syntax/provenance only; it does not invoke a guest compiler.
"""
from pathlib import Path
import hashlib
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor/oreslang/testing.ores"
PINNED_GIT_BLOB = "677754a41983167bb4f8ba5ffa8551bb87aaf9f7"
EXPORTED_CLASSES = ("TestOutcome", "TestCase", "TestSuite",
                    "TestOptions", "RunSummary")


class CanonicalTestingModuleContractTests(unittest.TestCase):
    def test_canonical_blob_matches_pinned_source_contract(self):
        data = VENDOR.read_bytes()
        header = ("blob " + str(len(data)) + "\0").encode("ascii")
        self.assertEqual(hashlib.sha1(header + data).hexdigest(),
                         PINNED_GIT_BLOB)

    def test_imported_classes_are_public_in_a_module(self):
        source = VENDOR.read_text(encoding="utf-8")
        self.assertTrue(source.startswith("define module testing as\n"))
        self.assertTrue(source.rstrip().endswith("\nend"))
        for name in EXPORTED_CLASSES:
            self.assertEqual(len(re.findall(
                r"(?m)^pub define class " + name + r" as$", source)), 1, name)
        guest = (ROOT / "tests/main.ores").read_text(encoding="utf-8")
        for name in EXPORTED_CLASSES:
            self.assertIn(name, guest.split("\n", 1)[0])

    def test_runner_invokes_real_oreslang_entrypoint(self):
        runner = (ROOT / "scripts/test.sh").read_text(encoding="utf-8")
        self.assertIn("tests/main.ores", runner)
        self.assertIn("ORESLANG_BIN", runner)
        self.assertNotIn("python3", runner)


if __name__ == "__main__":
    unittest.main()
