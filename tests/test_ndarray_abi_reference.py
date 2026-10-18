"""Contiguous shape and disjoint view ABI adversarial vectors."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_ndarray_layout import (BorrowBook, LayoutError, checked_elements,
                                  contiguous_bytes, validate_view)


class NdArrayAbiTests(unittest.TestCase):
    def test_contiguous_bytes_and_zero_sized_dimension(self):
        self.assertEqual(contiguous_bytes((2,3),8),48)
        self.assertEqual(contiguous_bytes((),8),8)
        self.assertEqual(contiguous_bytes((3,0,4),8),0)

    def test_allocation_overflow_and_boolean_dimension_rejected(self):
        for bad in ((1<<62,8), (-1,2), (True,2)):
            with self.subTest(shape=bad), self.assertRaises(LayoutError):
                checked_elements(bad)
        with self.assertRaises(LayoutError):
            contiguous_bytes((1<<62,),8)

    def test_strided_transpose_with_valid_owned_extent(self):
        self.assertEqual(validate_view((3,2),(8,24),0,48,8),(0,48))
        self.assertEqual(validate_view((3,2),(-8,24),16,48,8),(0,48))

    def test_oob_unaligned_and_rank_mismatch_rejected(self):
        for params in [((3,2),(8,24),0,40,8),
                       ((2,2),(1,8),0,48,8),
                       ((2,2),(8,),0,48,8),
                       ((2,2),(-8,16),0,48,8)]:
            with self.subTest(params=params), self.assertRaises(LayoutError):
                validate_view(*params)

    def test_empty_view_still_has_bounded_offset(self):
        self.assertEqual(validate_view((0,), (8,), 48,48,8),(48,48))
        with self.assertRaises(LayoutError):
            validate_view((0,), (8,), 56,48,8)

    def test_exclusive_overlapping_borrows_and_disjoint_writer(self):
        b=BorrowBook(); b.register("actor1",2)
        read=b.borrow("actor1",2,mutable=False,start=0,end=16)
        read2=b.borrow("actor1",2,mutable=False,start=0,end=16)
        with self.assertRaises(LayoutError):
            b.borrow("actor1",2,mutable=True,start=8,end=24)
        write=b.borrow("actor1",2,mutable=True,start=16,end=32)
        with self.assertRaises(LayoutError):
            b.drop_owner("actor1",2)
        for loan in (read,read2,write): b.release(loan)
        b.drop_owner("actor1",2)
        with self.assertRaises(LayoutError):
            b.borrow("actor1",2,mutable=False,start=0,end=8)

    def test_owner_reuse_requires_strictly_new_generation(self):
        book=BorrowBook()
        book.register("tensor", 9)
        first=book.borrow("tensor", 9, mutable=False, start=0, end=8)
        book.release(first)
        book.drop_owner("tensor", 9)
        with self.assertRaises(LayoutError):
            book.register("tensor", 9)
        with self.assertRaises(LayoutError):
            book.register("tensor", 8)
        book.register("tensor", 10)
        with self.assertRaises(LayoutError):
            book.borrow("tensor", 9, mutable=False, start=0, end=8)
        with self.assertRaises(LayoutError):
            book.drop_owner("tensor", True)
        book.drop_owner("tensor", 10)

    def test_invalid_release_type_is_protocol_error(self):
        book=BorrowBook()
        with self.assertRaises(LayoutError):
            book.release([])
        with self.assertRaises(LayoutError):
            book.release({"owner":"fabricated"})

    def test_old_generation_and_double_release_refused(self):
        b=BorrowBook(); b.register("array",7)
        with self.assertRaises(LayoutError):
            b.borrow("array",6,mutable=True,start=0,end=8)
        loan=b.borrow("array",7,mutable=True,start=0,end=8)
        b.release(loan)
        with self.assertRaises(LayoutError):
            b.release(loan)


if __name__ == "__main__":
    unittest.main()
