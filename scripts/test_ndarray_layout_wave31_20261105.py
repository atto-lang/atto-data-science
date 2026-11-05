"""Host-only borrow/layout reference negatives; no Oreslang compiler execution."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_ndarray_layout import (
    BorrowBook, LayoutError, checked_elements, contiguous_bytes,
    validate_view, validate_unique_write_view,
)


class LayoutBoundaryWave31(unittest.TestCase):
    def test_reverse_stride_is_bounded_and_nonoverlapping(self):
        self.assertEqual(validate_view([3], [-8], 16, 24, 8), (0, 24))
        self.assertEqual(validate_unique_write_view([3], [-8], 16, 24, 8), (0, 24))

    def test_zero_stride_and_overlapping_mutable_axes_denied(self):
        self.assertEqual(validate_view([2], [0], 0, 16, 8), (0, 8))
        with self.assertRaisesRegex(LayoutError, "overlapping"):
            validate_unique_write_view([2], [0], 0, 16, 8)
        with self.assertRaisesRegex(LayoutError, "overlapping"):
            validate_unique_write_view([2, 2], [8, 8], 0, 24, 8)

    def test_zero_length_owner_boundary_but_not_beyond(self):
        self.assertEqual(validate_view([0], [8], 24, 24, 8), (24, 24))
        with self.assertRaisesRegex(LayoutError, "outside owner"):
            validate_view([0], [8], 32, 24, 8)
        self.assertEqual(checked_elements([2, 0, 2**50]), 0)
        self.assertEqual(contiguous_bytes([2, 0, 2**50], 8), 0)

    def test_generation_fenced_borrow_lifetime_and_reissue(self):
        book = BorrowBook()
        book.register("owner", 1)
        lease = book.borrow_view("owner", 1, mutable=True, shape=[2],
                                 strides_bytes=[8], offset_bytes=0,
                                 storage_bytes=16, itemsize=8)
        with self.assertRaisesRegex(LayoutError, "live views"):
            book.drop_owner("owner", 1)
        book.release(lease)
        with self.assertRaisesRegex(LayoutError, "already released"):
            book.release(lease)
        book.drop_owner("owner", 1)
        with self.assertRaisesRegex(LayoutError, "monotonically"):
            book.register("owner", 1)
        book.register("owner", 2)
        with self.assertRaisesRegex(LayoutError, "stale or alien"):
            book.borrow("owner", 1, mutable=False, start=0, end=8)


if __name__ == "__main__":
    unittest.main()
