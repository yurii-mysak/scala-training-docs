import os
import random
import sys
import unittest
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lc480_sliding_window_median import median_sliding_window


def brute_force_median_sliding_window(nums: List[int], k: int) -> List[float]:
    """O(n * k log k) reference: sort each window from scratch. Slow, but
    obviously correct -- exactly the kind of baseline worth writing first
    on this problem, and the one the fast version is checked against here.
    """
    result: List[float] = []
    for i in range(len(nums) - k + 1):
        window = sorted(nums[i:i + k])
        if k % 2:
            result.append(float(window[k // 2]))
        else:
            result.append((window[k // 2 - 1] + window[k // 2]) / 2.0)
    return result


class TestSlidingWindowMedian(unittest.TestCase):
    def test_leetcode_example(self) -> None:
        self.assertEqual(
            median_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3),
            [1.0, -1.0, -1.0, 3.0, 5.0, 6.0],
        )

    def test_k_equals_array_length(self) -> None:
        self.assertEqual(median_sliding_window([2, 1, 4, 7], 4), [3.0])

    def test_k_equals_one_median_is_each_element(self) -> None:
        self.assertEqual(median_sliding_window([5, 1, 9], 1), [5.0, 1.0, 9.0])

    def test_even_window_size_averages_middle_two(self) -> None:
        self.assertEqual(median_sliding_window([1, 2], 2), [1.5])
        self.assertEqual(median_sliding_window([2, 3, 4], 2), [2.5, 3.5])

    def test_duplicate_values(self) -> None:
        self.assertEqual(
            median_sliding_window([1, 1, 1, 1], 2),
            [1.0, 1.0, 1.0],
        )

    def test_negative_and_mixed_values(self) -> None:
        self.assertEqual(
            median_sliding_window([-5, -3, -1, 0, 2], 3),
            brute_force_median_sliding_window([-5, -3, -1, 0, 2], 3),
        )

    def test_matches_brute_force_on_fixed_tricky_sequences(self) -> None:
        cases = [
            ([1, 4, 2, 3], 4),
            ([0, 0, 0, 0, 0], 3),
            ([5, -1, -1, 5, -1, 5], 2),
            ([7, 2, 4], 3),
        ]
        for nums, k in cases:
            with self.subTest(nums=nums, k=k):
                self.assertEqual(
                    median_sliding_window(nums, k),
                    brute_force_median_sliding_window(nums, k),
                )

    def test_matches_brute_force_on_random_sequences(self) -> None:
        rng = random.Random(42)
        for _trial in range(300):
            n = rng.randint(1, 20)
            nums = [rng.randint(-10, 10) for _ in range(n)]
            k = rng.randint(1, n)
            with self.subTest(nums=nums, k=k):
                self.assertEqual(
                    median_sliding_window(nums, k),
                    brute_force_median_sliding_window(nums, k),
                )


if __name__ == "__main__":
    unittest.main()
