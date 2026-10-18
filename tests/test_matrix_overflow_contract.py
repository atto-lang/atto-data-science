"""Host model and source-contract regression for DenseMatrixF64 overflow.

This is not compiler execution. True Graal/LLVM guest execution is required.
"""
from pathlib import Path
import random
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src/math/matrix.ores"
I64_MAX = (1 << 63) - 1


def checked_product(rows, cols):
    """Independent reference of the integer-only Oreslang shift/add algorithm."""
    if rows < 0 or cols < 0 or rows > I64_MAX or cols > I64_MAX:
        return None
    addend, remaining, product = rows, cols, 0
    while remaining:
        if remaining % 2:
            if addend > I64_MAX - product:
                return None
            product += addend
        remaining >>= 1
        if remaining:
            if addend > I64_MAX - addend:
                return None
            addend += addend
    return product


class MatrixIndexContractTests(unittest.TestCase):
    def test_no_floating_division_as_overflow_guard(self):
        source = SOURCE.read_text(encoding="utf-8")
        method = source.split("fnc checked_matrix_element_count", 1)[1].split(
            "pub fnc validate_matrix", 1)[0]
        statements = [line.strip() for line in method.splitlines()
                      if line.strip() and not line.lstrip().startswith("//")]
        self.assertNotIn("/", " ".join(statements))
        self.assertIn("remaining = remaining >> 1", method)
        self.assertIn("addend > 9223372036854775807 - product", method)
        self.assertIn("addend > 9223372036854775807 - addend", method)
        self.assertNotIn("matrix.rows * matrix.cols", source)
        self.assertEqual(source.count("checked_matrix_element_count("), 3)

    def test_storage_admission_precedes_matrix_get_dereference(self):
        source = SOURCE.read_text(encoding="utf-8")
        body = source.split("pub fnc matrix_get", 1)[1].split("pub fnc matvec_into", 1)[0]
        self.assertLess(body.index("validate_matrix(matrix)"),
                        body.index("matrix.values[index_result.unwrap()]"))

    def test_guest_negative_regressions_are_registered(self):
        guest = (SOURCE.parents[2] / "tests/main.ores").read_text(encoding="utf-8")
        for name in ("matrix/short-storage", "matrix/valid-get", "matrix/overflow"):
            self.assertIn('new TestCase("' + name + '"', guest)
        self.assertIn("matrix_get(truncated, 0, 1)", guest)
        self.assertIn("3037000500, 3037000500", guest)

    def test_boundary_products(self):
        for a, b in ((0, I64_MAX), (I64_MAX, 0), (I64_MAX, 1),
                     (1, I64_MAX), (3037000499, 3037000499)):
            self.assertEqual(checked_product(a, b), a * b)
        for a, b in ((3037000500, 3037000500), (I64_MAX, 2),
                     (-1, 1), (1, -1), (I64_MAX + 1, 1)):
            self.assertIsNone(checked_product(a, b))

    def test_precision_loss_counterexample_to_old_guard(self):
        cols = 3
        bad_rows = I64_MAX // cols + 1
        self.assertGreater(bad_rows * cols, I64_MAX)
        self.assertFalse(float(bad_rows) > float(I64_MAX) / float(cols))
        self.assertIsNone(checked_product(bad_rows, cols))

    def test_ten_thousand_random_differential_cases(self):
        rng = random.Random(20261018)
        for _ in range(10000):
            a = rng.randint(0, I64_MAX)
            b = rng.randint(0, I64_MAX)
            exact = a * b
            self.assertEqual(checked_product(a, b),
                             exact if exact <= I64_MAX else None)

    def test_valid_and_boundary_factor_pairs(self):
        rng = random.Random(20261018)
        for _ in range(25000):
            a = rng.randint(0, I64_MAX)
            upper = I64_MAX if a == 0 else I64_MAX // a
            b = rng.randint(0, upper)
            self.assertEqual(checked_product(a, b), a * b)
        for _ in range(25000):
            b = rng.randint(2, 10000)
            q = I64_MAX // b
            for a in (max(0, q - 1), q, q + 1, min(I64_MAX, q + 2)):
                exact = a * b
                self.assertEqual(checked_product(a, b),
                                 exact if exact <= I64_MAX else None)


if __name__ == "__main__":
    unittest.main()
