"""17-lyft-laptop-round / 02-versioned-kv-store

set(key, value) increments that key's version and stores the new value under it.
get(key, version) returns the value recorded at that version, or -- if that exact
version doesn't exist for the key -- the value at the latest version smaller than
the one asked for.

Relation to a known problem: this is LeetCode 981, Time Based Key-Value Store, with
an auto-incrementing per-key integer version standing in for an externally supplied
timestamp. The core algorithmic move is identical either way: binary search for the
rightmost recorded version/timestamp <= the one requested.

Run directly to see a demo:
    python3 02-versioned-kv-store.py
"""

from __future__ import annotations

import sys
from bisect import bisect_right
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


class VersionedKVStore:
    """Per key, keeps a strictly increasing list of (version, value) pairs in
    insertion order. Because set() always assigns the next integer version for
    that key, the list is already sorted by construction -- no re-sorting needed,
    just append.

    get(key, version) finds the rightmost entry whose version is <= the requested
    one via binary search (bisect), which is exactly "the value at that version if
    it exists, otherwise the latest smaller version" -- those collapse into the same
    operation because per-key versions are contiguous integers with no gaps.
    """

    def __init__(self) -> None:
        self._history: Dict[str, List[Tuple[int, Any]]] = defaultdict(list)
        self._latest_version: Dict[str, int] = {}

    def set(self, key: str, value: Any) -> int:
        """Stores value under the next version for key. Returns the new version."""
        version = self._latest_version.get(key, 0) + 1
        self._latest_version[key] = version
        self._history[key].append((version, value))
        return version

    def get(self, key: str, version: int) -> Optional[Any]:
        """Returns the value at `version`, or the latest version < the requested
        one if there's no exact match, or None if the key has no version that old
        (including: the key was never set)."""
        versions = self._history.get(key)
        if not versions:
            return None
        # bisect_right's key= extracts just the version number for comparison,
        # so this never has to compare stored *values* against each other (they
        # could be any type). idx-1 is the rightmost entry with
        # entry_version <= version -- exactly "exact match, or latest smaller".
        idx = bisect_right(versions, version, key=lambda pair: pair[0]) - 1
        if idx < 0:
            return None
        return versions[idx][1]

    def latest_version(self, key: str) -> Optional[int]:
        return self._latest_version.get(key)


class VersionedKVStoreDictBacked:
    """The other implementation candidates reach for: an exact-version dict plus
    a separate sorted list of version numbers for the predecessor query. Included
    here purely to make the read/write trade-off concrete -- see the "Read vs
    write" section in 02-versioned-kv-store.md. This is *not* the recommended
    default; VersionedKVStore above is simpler and just as fast for the common
    case.
    """

    def __init__(self) -> None:
        self._by_version: Dict[str, Dict[int, Any]] = defaultdict(dict)
        self._sorted_versions: Dict[str, List[int]] = defaultdict(list)
        self._latest_version: Dict[str, int] = {}

    def set(self, key: str, value: Any) -> int:
        version = self._latest_version.get(key, 0) + 1
        self._latest_version[key] = version
        self._by_version[key][version] = value
        self._sorted_versions[key].append(version)  # still append-only: O(1)
        return version

    def get(self, key: str, version: int) -> Optional[Any]:
        exact = self._by_version.get(key, {})
        if version in exact:
            return exact[version]  # O(1) fast path for an exact hit
        versions = self._sorted_versions.get(key)
        if not versions:
            return None
        idx = bisect_right(versions, version) - 1
        if idx < 0:
            return None
        return exact[versions[idx]]


def main() -> None:
    """Reads newline-delimited commands from stdin by default, or from a file
    path given as argv[1]. Commands:
        SET key value
        GET key version
    Prints one line per GET: the value, or NULL if there's no version that old.
    Example input:
        SET a 1
        SET a 2
        SET a 3
        GET a 2
        GET a 99
        GET b 1
    """
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        lines = sys.stdin.read().splitlines()

    store = VersionedKVStore()
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        cmd = parts[0].upper()
        if cmd == "SET" and len(parts) >= 3:
            store.set(parts[1], " ".join(parts[2:]))
        elif cmd == "GET" and len(parts) == 3:
            value = store.get(parts[1], int(parts[2]))
            print(value if value is not None else "NULL")


if __name__ == "__main__":
    main()
