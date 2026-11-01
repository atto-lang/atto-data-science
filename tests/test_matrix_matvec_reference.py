"""Independent Python mathematical model for Oreslang matrix-vector test vectors.

These are host-only oracle checks, NOT tests of compiled `.ores` code.
They deliberately expose the aliasing obligation tracked by Data Science #20.
"""
import random
import unittest

MAX_I64 = (1 << 63) - 1


def checked_shape_product(rows, cols):
    if type(rows) is not int or type(cols) is not int or rows < 0 or cols < 0:
        raise ValueError("invalid matrix dimensions")
    if rows > MAX_I64 or cols > MAX_I64 or rows * cols > MAX_I64:
        raise ValueError("matrix extent overflow")
    return rows * cols


def matvec_oracle(rows, cols, values, vector):
    """Exact small-integer algebra independent of Oreslang evaluation order."""
    expected = checked_shape_product(rows, cols)
    if len(values) != expected or len(vector) != cols:
        raise ValueError("invalid matrix or vector extent")
    return [sum(values[row * cols + col] * vector[col]
                for col in range(cols)) for row in range(rows)]


def matvec_source_order(rows, cols, values, vector, output):
    """Mirror of source-loop read/write order, not execution of `.ores`."""
    expected = checked_shape_product(rows, cols)
    if len(values) != expected or len(vector) != cols or len(output) != rows:
        raise ValueError("invalid matrix or vector or destination extent")
    for row in range(rows):
        total = 0
        for col in range(cols):
            total += values[row * cols + col] * vector[col]
        output[row] = total
    return output


class MatrixMatvecHostOracle(unittest.TestCase):
    def test_checked_products_match_independent_integer_arithmetic(self):
        rng = random.Random(0xA115)
        cases = [(0, 0), (MAX_I64, 0), (0, MAX_I64),
                 (MAX_I64, 1), (1, MAX_I64), (MAX_I64, 2),
                 (3037000499, 3037000499), (3037000500, 3037000500)]
        cases.extend((rng.randrange(MAX_I64 + 1), rng.randrange(MAX_I64 + 1))
                     for _ in range(10000))
        for rows, cols in cases:
            exact = rows * cols
            if exact <= MAX_I64:
                self.assertEqual(checked_shape_product(rows, cols), exact)
            else:
                with self.assertRaises(ValueError):
                    checked_shape_product(rows, cols)

    def test_random_disjoint_output_matches_exact_mathematical_oracle(self):
        rng = random.Random(0x53175)
        for _ in range(8000):
            rows, cols = rng.randrange(7), rng.randrange(7)
            values = [rng.randrange(-20, 21) for _ in range(rows * cols)]
            vector = [rng.randrange(-20, 21) for _ in range(cols)]
            initial = [999 for _ in range(rows)]
            got = matvec_source_order(rows, cols, values, vector, initial)
            expected = matvec_oracle(rows, cols, values, vector)
            self.assertEqual(got, expected)

    def test_zero_column_matrix_clears_existing_destination(self):
        result = [91, 92]
        self.assertIs(matvec_source_order(2, 0, [], [], result), result)
        self.assertEqual(result, [0, 0])
        self.assertEqual(matvec_oracle(2, 0, [], []), [0, 0])

    def test_bad_lengths_refused_before_any_destination_mutation(self):
        invalid = [(2, 2, [1], [1, 2]),
                   (2, 2, [1, 2, 3, 4], [1]),
                   (2, 2, [1, 2, 3, 4], [1, 2, 3])]
        for rows, cols, values, vector in invalid:
            output = [91, 92]
            with self.assertRaises(ValueError):
                matvec_source_order(rows, cols, values, vector, output)
            self.assertEqual(output, [91, 92])

    def test_shared_input_and_output_is_not_alias_safe_without_compiler_fence(self):
        matrix = [1, 1, 1, 1]
        vector = [1, 2]
        self.assertEqual(matvec_oracle(2, 2, matrix, vector), [3, 3])
        self.assertEqual(matvec_source_order(2, 2, matrix, vector, vector), [3, 5])
        # This asserts a safety proof obligation, not actual compiler admission.

    def test_shared_matrix_and_output_requires_borrow_proof(self):
        # With a 1-column matrix, the destination length equals matrix storage;
        # this alias currently happens to be mathematically safe for these rows.
        # It still requires a formal owned/borrowed ABI contract.
        values = [3, 4]
        self.assertEqual(matvec_source_order(2, 1, values, [2], values), [6, 8])


if __name__ == "__main__":
    unittest.main()
