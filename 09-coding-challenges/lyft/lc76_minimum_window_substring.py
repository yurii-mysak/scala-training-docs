"""
LC 76 - Minimum Window Substring
https://leetcode.com/problems/minimum-window-substring/

Given strings `s` and `t`, return the smallest substring of `s` that contains
every character of `t`, including duplicates. Return "" if no such window
exists.

Companion doc: lc76-minimum-window-substring.md
"""
from __future__ import annotations

from collections import Counter


def min_window(s: str, t: str) -> str:
    """Return the smallest substring of s containing all characters of t.

    Single-pass variable sliding window. `need` holds, for every character,
    (count still required) - (count collected in the current window). It is
    allowed to go negative for characters that are over-collected or not
    required at all -- that is what makes the O(1)-per-step bookkeeping work
    without a second dict.
    """
    if not s or not t or len(t) > len(s):
        return ""

    need = Counter(t)
    missing = len(t)  # characters still owed, counting multiplicity

    best_len = len(s) + 1
    best_start = 0
    left = 0

    for right, ch in enumerate(s):
        if need[ch] > 0:
            missing -= 1
        need[ch] -= 1

        while missing == 0:
            if right - left + 1 < best_len:
                best_len = right - left + 1
                best_start = left

            left_ch = s[left]
            need[left_ch] += 1
            if need[left_ch] > 0:
                missing += 1
            left += 1

    return "" if best_len == len(s) + 1 else s[best_start:best_start + best_len]


if __name__ == "__main__":
    demos = [
        ("ADOBECODEBANC", "ABC"),
        ("a", "a"),
        ("a", "aa"),
        ("aa", "aa"),
    ]
    for s, t in demos:
        print(f"min_window({s!r}, {t!r}) = {min_window(s, t)!r}")
