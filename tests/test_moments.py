import unittest
from reference.moments import Moments, MomentsError


class OnlineMomentsTest(unittest.TestCase):
    def test_incremental_and_merge(self):
        whole = Moments()
        for x in [1, 2, 3, 4]:
            whole = whole.add(x)
        self.assertEqual(whole.count, 4)
        self.assertAlmostEqual(whole.mean, 2.5)
        self.assertAlmostEqual(whole.population_variance(), 1.25)
        self.assertAlmostEqual(whole.sample_variance(), 5 / 3)

        left = Moments().add(1).add(2)
        right = Moments().add(3).add(4)
        joined = left.merge(right)
        self.assertAlmostEqual(joined.mean, whole.mean)
        self.assertAlmostEqual(joined.sample_variance(), whole.sample_variance())
        self.assertEqual(left.count, 2)  # immutable summary

    def test_empty_and_invalid(self):
        with self.assertRaises(MomentsError):
            Moments().population_variance()
        with self.assertRaises(MomentsError):
            Moments().add(1).sample_variance()
        for x in [float("nan"), float("inf"), True, "2"]:
            with self.assertRaises(MomentsError):
                Moments().add(x)
        with self.assertRaises(MomentsError):
            Moments().add(1e308).add(-1e308)


if __name__ == "__main__":
    unittest.main()
