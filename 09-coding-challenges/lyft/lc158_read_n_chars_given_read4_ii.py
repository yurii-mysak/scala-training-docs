"""
LC 158 - Read N Characters Given Read4 II - Call Multiple Times
https://leetcode.com/problems/read-n-characters-given-read4-ii-call-multiple-times/

The underlying file can only be read through `read4(buf4)`, which fills up
to 4 characters into buf4 and returns how many it actually wrote (< 4 only
at end-of-file). `read(buf, n)` must return exactly n characters -- or fewer
only at EOF -- and, critically, `read` may be called *multiple times on the
same object*. Characters fetched by read4 but not consumed by a short `n`
must survive into the next call. This file-under-buffered-primitive shape is
also the shape of a paginated API client: see
../../17-lyft-laptop-round/01-stateful-paginated-fetch.md for the laptop-round
version of the same statefulness problem.

Companion doc: lc158-read-n-chars-given-read4-ii.md
"""
from __future__ import annotations

from typing import List


class FileReader4:
    """Stands in for "a file exposed only through a 4-char read primitive."

    The object under test (Solution, below) only ever sees read4 -- never
    the underlying string -- exactly as LeetCode's judge only exposes read4
    to the submitted class.
    """

    def __init__(self, data: str) -> None:
        self._data = data
        self._pos = 0

    def read4(self, buf4: List[str]) -> int:
        """Write up to 4 chars into buf4 in place; return count written.

        Resumes from wherever the previous read4 call left off. Returns
        fewer than 4 only when the source is exhausted.
        """
        count = 0
        while count < 4 and self._pos < len(self._data):
            buf4[count] = self._data[self._pos]
            count += 1
            self._pos += 1
        return count


class Solution:
    """read(buf, n) is safe to call repeatedly on the same instance.

    All the difficulty is in what persists *between* calls: buf4 itself,
    how many valid characters it holds, and how far into it we have already
    consumed. Get any one of those three wrong and either characters are
    dropped or duplicated on the second call -- correctness only shows up
    once you call read() more than once, which is exactly what a
    single-call test suite would miss.
    """

    def __init__(self, reader: FileReader4) -> None:
        self.reader = reader
        self.buf4: List[str] = [""] * 4
        self.buf4_len = 0   # valid characters currently sitting in self.buf4
        self.buf4_ptr = 0   # index of the next not-yet-consumed char in buf4

    def read(self, buf: List[str], n: int) -> int:
        total = 0
        while total < n:
            if self.buf4_ptr == self.buf4_len:
                # Leftover buffer exhausted: pull a fresh block. This is the
                # only place read4 is ever called.
                self.buf4_len = self.reader.read4(self.buf4)
                self.buf4_ptr = 0
                if self.buf4_len == 0:
                    break  # underlying source exhausted
            while total < n and self.buf4_ptr < self.buf4_len:
                buf[total] = self.buf4[self.buf4_ptr]
                total += 1
                self.buf4_ptr += 1
        return total


if __name__ == "__main__":
    reader = FileReader4("abcdefgh")  # 8 chars, does not divide evenly by 4
    solver = Solution(reader)
    buf: List[str] = [""] * 10

    for call_n in (1, 1, 1, 4, 1, 1):
        got = solver.read(buf, call_n)
        print(f"read(buf, {call_n}) -> {got} chars: {''.join(buf[:got])!r}")
