import os
import sys
import unittest
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lc158_read_n_chars_given_read4_ii import FileReader4, Solution


class TestReadN(unittest.TestCase):
    def test_single_call_shorter_than_source(self) -> None:
        solver = Solution(FileReader4("abc"))
        buf: List[str] = [""] * 4
        n = solver.read(buf, 4)
        self.assertEqual(n, 3)
        self.assertEqual("".join(buf[:n]), "abc")

    def test_single_call_exact_multiple_of_four(self) -> None:
        solver = Solution(FileReader4("abcdefgh"))
        buf: List[str] = [""] * 8
        n = solver.read(buf, 8)
        self.assertEqual(n, 8)
        self.assertEqual("".join(buf[:n]), "abcdefgh")

    def test_read_more_than_available_returns_only_what_exists(self) -> None:
        solver = Solution(FileReader4("ab"))
        buf: List[str] = [""] * 10
        n = solver.read(buf, 10)
        self.assertEqual(n, 2)
        self.assertEqual("".join(buf[:n]), "ab")

    def test_zero_length_read_touches_nothing(self) -> None:
        solver = Solution(FileReader4("abcd"))
        buf: List[str] = [""] * 4
        self.assertEqual(solver.read(buf, 0), 0)

    def test_leftover_bytes_survive_across_calls(self) -> None:
        # 8 chars means read4 boundaries fall at 4 and 8, which does not
        # line up with 1-character reads -- this is what forces buf4 state
        # to persist between calls instead of being re-derived each time.
        solver = Solution(FileReader4("abcdefgh"))
        buf: List[str] = [""] * 1
        collected = []
        for _ in range(8):
            n = solver.read(buf, 1)
            self.assertEqual(n, 1)
            collected.append(buf[0])
        self.assertEqual("".join(collected), "abcdefgh")
        # Source is now exhausted.
        self.assertEqual(solver.read(buf, 1), 0)

    def test_call_sizes_do_not_align_with_read4_blocks(self) -> None:
        solver = Solution(FileReader4("abcdefgh"))
        buf: List[str] = [""] * 10
        results = []
        for call_n in (3, 3, 2):
            n = solver.read(buf, call_n)
            results.append("".join(buf[:n]))
        self.assertEqual(results, ["abc", "def", "gh"])

    def test_calls_after_exhaustion_return_zero_repeatedly(self) -> None:
        solver = Solution(FileReader4("a"))
        buf: List[str] = [""] * 4
        self.assertEqual(solver.read(buf, 4), 1)
        self.assertEqual(solver.read(buf, 4), 0)
        self.assertEqual(solver.read(buf, 4), 0)

    def test_empty_source(self) -> None:
        solver = Solution(FileReader4(""))
        buf: List[str] = [""] * 4
        self.assertEqual(solver.read(buf, 4), 0)

    def test_independent_instances_do_not_share_state(self) -> None:
        solver_a = Solution(FileReader4("aaaa"))
        solver_b = Solution(FileReader4("bbbb"))
        buf_a: List[str] = [""] * 2
        buf_b: List[str] = [""] * 2
        solver_a.read(buf_a, 2)
        solver_b.read(buf_b, 2)
        self.assertEqual("".join(buf_a), "aa")
        self.assertEqual("".join(buf_b), "bb")


if __name__ == "__main__":
    unittest.main()
