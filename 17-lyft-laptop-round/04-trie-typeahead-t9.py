"""17-lyft-laptop-round / 04-trie-typeahead-t9

Part 1: trie-backed typeahead / autocomplete -- top-k suggestions for a prefix,
ranked by frequency.
Part 2: the T9 numeric-keypad variant -- this is the exact problem reported from
the Kyiv loop as "word analyzer (T9)": given a digit sequence typed on an old phone
keypad, return the dictionary word(s) that sequence could mean.

Relation to known problems: Part 1 is LeetCode 642 (Design Search Autocomplete
System) minus the "record queries as you go" streaming twist, built over a trie the
way LeetCode 208 (Implement Trie) sets up. Part 2 reuses the exact same trie
structure, just keyed by digits instead of letters.

Run directly to see a demo:
    python3 04-trie-typeahead-t9.py
"""

from __future__ import annotations

import sys
from typing import Dict, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# Part 1 -- letter trie, frequency-ranked typeahead
# --------------------------------------------------------------------------- #


class _TrieNode:
    __slots__ = ("children", "is_word", "frequency")

    def __init__(self) -> None:
        self.children: Dict[str, "_TrieNode"] = {}
        self.is_word = False
        self.frequency = 0


class Typeahead:
    """Trie-backed autocomplete: add_word(word, frequency), then suggest(prefix, k)
    returns the top-k known words starting with prefix, most frequent first, ties
    broken alphabetically (for deterministic output -- always pick an explicit tie
    -break rule, "whatever the sort happens to do" is not a rule).
    """

    def __init__(self) -> None:
        self._root = _TrieNode()

    def add_word(self, word: str, frequency: int = 1) -> None:
        if not word:
            raise ValueError("word must not be empty")
        node = self._root
        for ch in word:
            node = node.children.setdefault(ch, _TrieNode())
        node.is_word = True
        node.frequency += frequency

    def suggest(self, prefix: str, k: int = 5) -> List[str]:
        if k <= 0:
            return []
        node = self._root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        matches: List[Tuple[int, str]] = []
        self._collect(node, prefix, matches)
        matches.sort(key=lambda pair: (-pair[0], pair[1]))
        return [word for _, word in matches[:k]]

    def _collect(self, node: _TrieNode, prefix: str, out: List[Tuple[int, str]]) -> None:
        if node.is_word:
            out.append((node.frequency, prefix))
        for ch, child in node.children.items():
            self._collect(child, prefix + ch, out)


# --------------------------------------------------------------------------- #
# Part 2 -- T9: digits typed on a phone keypad -> matching dictionary words
# --------------------------------------------------------------------------- #

_T9_MAP = {
    "a": "2", "b": "2", "c": "2",
    "d": "3", "e": "3", "f": "3",
    "g": "4", "h": "4", "i": "4",
    "j": "5", "k": "5", "l": "5",
    "m": "6", "n": "6", "o": "6",
    "p": "7", "q": "7", "r": "7", "s": "7",
    "t": "8", "u": "8", "v": "8",
    "w": "9", "x": "9", "y": "9", "z": "9",
}
_VALID_DIGITS = set("23456789")


def word_to_digits(word: str) -> str:
    """Maps a lowercase alphabetic word to its T9 digit encoding, e.g. "cab" and
    "abc" both encode to "222" -- that collision is real T9 behavior, not a bug."""
    try:
        return "".join(_T9_MAP[ch] for ch in word.lower())
    except KeyError as exc:
        raise ValueError(f"word contains a non-alphabetic character: {word!r}") from exc


class _T9Node:
    __slots__ = ("children", "words")

    def __init__(self) -> None:
        self.children: Dict[str, "_T9Node"] = {}
        self.words: List[Tuple[int, str]] = []  # every word whose digit path ends here


class T9Typeahead:
    """Same trie shape as Typeahead, keyed by digits instead of letters. Because
    multiple words can share a digit encoding ("cab" and "abc" -> "222"), a
    terminal node holds a *list* of (frequency, word) pairs, not a single word.
    """

    def __init__(self) -> None:
        self._root = _T9Node()

    def add_word(self, word: str, frequency: int = 1) -> None:
        digits = word_to_digits(word)
        node = self._root
        for d in digits:
            node = node.children.setdefault(d, _T9Node())
        node.words.append((frequency, word.lower()))

    def suggest(self, digits: str, k: int = 5) -> List[str]:
        """Exact-length T9 lookup: words whose full digit encoding equals `digits`.
        This is the classic "multi-tap disambiguation" behavior -- typing all the
        digits for a word and getting back the words that share that exact code.
        """
        self._validate_digits(digits)
        if k <= 0:
            return []
        node = self._walk(digits)
        if node is None:
            return []
        return self._ranked(node.words, k)

    def suggest_including_longer(self, digits: str, k: int = 5) -> List[str]:
        """Like suggest(), but also includes longer words that start with this
        digit sequence -- e.g. digits for "hi" also offering "hint" if present.
        Useful when the UI wants live completions as the user keeps typing, not
        just exact-length matches. Confirm which behavior is actually wanted
        before building both -- see 00-protocol.md.
        """
        self._validate_digits(digits)
        if k <= 0:
            return []
        node = self._walk(digits)
        if node is None:
            return []
        collected: List[Tuple[int, str]] = []
        self._collect(node, collected)
        return self._ranked(collected, k)

    def _walk(self, digits: str) -> Optional[_T9Node]:
        node = self._root
        for d in digits:
            if d not in node.children:
                return None
            node = node.children[d]
        return node

    def _collect(self, node: _T9Node, out: List[Tuple[int, str]]) -> None:
        out.extend(node.words)
        for child in node.children.values():
            self._collect(child, out)

    @staticmethod
    def _ranked(candidates: List[Tuple[int, str]], k: int) -> List[str]:
        ranked = sorted(candidates, key=lambda pair: (-pair[0], pair[1]))
        return [word for _, word in ranked[:k]]

    @staticmethod
    def _validate_digits(digits: str) -> None:
        if not digits:
            return
        invalid = set(digits) - _VALID_DIGITS
        if invalid:
            raise ValueError(f"invalid T9 digit(s): {sorted(invalid)} (only 2-9 are valid)")


def main() -> None:
    """Builds a small T9 dictionary and answers one query per stdin line (or a
    file path given as argv[1]) -- each line is a digit sequence, printed back as
    a comma-separated ranked suggestion list.
    """
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        lines = sys.stdin.read().splitlines()

    t9 = T9Typeahead()
    for word, frequency in [("cab", 3), ("abc", 5), ("act", 2), ("bat", 4)]:
        t9.add_word(word, frequency)

    for raw_line in lines:
        digits = raw_line.strip()
        if not digits:
            continue
        print(",".join(t9.suggest(digits)))


if __name__ == "__main__":
    main()
