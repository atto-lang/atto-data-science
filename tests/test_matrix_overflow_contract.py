"""Host reference regression for DenseMatrixF64 signed-i64 indexing.

Checks the Oreslang source guard remains in both entrypoints. This is
not compiler execution; Java and LLVM native guest checks remain required.
"""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src/math/matrix.ores"
I64_MAX = (1 << 63) - 1


def safe_shape(rows, cols):
    if rows < 0 or cols < 0:
        return False
    if cols > 0 and rows > I64_MAX // cols:
        return False
    return True


class MatrixIndexContractTests(unittest.TestCase):
    def test_guard_precedes_shape_multiplication_and_index(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(source.count("9223372036854775807 / matrix.cols"), 2)
        validate = source.split("pub fnc validate_matrix", 1)[1].split("pub fnc matrix_index", 1)[0]
        index = source.split("pub fnc matrix_index", 1)[1].split("pub fnc matrix_get", 1)[0]
        self.assertLess(validate.index("9223372036854775807 / matrix.cols"),
                        validate.index("matrix.rows * matrix.cols"))
        self.assertLess(index.index("9223372036854775807 / matrix.cols"),
                        index.index("(row * matrix.cols) + col"))
        self.assertNotIn("validate_matrix(matrix)", index)

    def test_matrix_get_validates_storage_before_dereference(self):
        source = SOURCE.read_text(encoding="utf-8")
        body = source.split("pub fnc matrix_get", 1)[1].split("pub fnc matvec_into", 1)[0]
        self.assertIn("validate_matrix(matrix)", body)
        self.assertLess(body.index("validate_matrix(matrix)"),
                        body.index("matrix.values[index_result.unwrap()]"))

    def test_real_guest_regressions_are_registered(self):
        guest = (SOURCE.parents[2] / "tests/main.ores").read_text(encoding="utf-8")
        for name in ("matrix/short-storage", "matrix/valid-get", "matrix/overflow"):
            self.assertIn('new TestCase("' + name + '"', guest)
        self.assertIn("matrix_get(truncated, 0, 1)", guest)
        self.assertIn("3037000500, 3037000500", guest)

    def test_boundary_products(self):
        self.assertTrue(safe_shape(0, I64_MAX))
        self.assertTrue(safe_shape(I64_MAX, 0))
        self.assertTrue(safe_shape(I64_MAX, 1))
        self.assertTrue(safe_shape(1, I64_MAX))
        self.assertTrue(safe_shape(3037000499, 3037000499))
        self.assertFalse(safe_shape(3037000500, 3037000500))
        self.assertFalse(safe_shape(I64_MAX, 2))
        self.assertFalse(safe_shape(-1, 1))
        self.assertFalse(safe_shape(1, -1))


if __name__ == "__main__":
    unittest.main()
