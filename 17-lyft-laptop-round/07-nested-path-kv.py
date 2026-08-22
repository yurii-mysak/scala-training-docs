"""17-lyft-laptop-round / 07-nested-path-kv

A key-value store where keys are dot-delimited paths ("a.b.c") and intermediate
segments are auto-created as nested "branches". Built in the order this problem
typically escalates in the actual round -- each stage below is a natural follow-up
to the one before it, which is itself worth narrating to the interviewer as you go:

  1. set(path, value) / get(path) / delete(path), with intermediates auto-created.
  2. children(prefix) -- sorted immediate child segment names under a path.
  3. flatten() -- every leaf as a flat {"a.b.c": value} dict.
  4. Strict type checking: a path cannot be both a branch (has children) and a leaf
     (holds a value) at once, in either direction.

Only 2 independent first-hand reports for this family -- lower priority than the
others, but a good synthesis exercise: it combines the dict-of-dicts manipulation
from the trie family with the "confirm behavior on ambiguous inputs" discipline
this whole section is about.

Run directly to see a demo:
    python3 07-nested-path-kv.py
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Tuple

# A node is a plain dict. A *leaf* node is {_LEAF: value} and nothing else. A
# *branch* node maps child segment name -> child node, and never contains _LEAF.
# A node is never both -- that invariant is what "strict type checking" enforces.
_LEAF = "__leaf__"


class NestedPathKV:
    """set/get/delete with dot-delimited paths and auto-created intermediates,
    plus children(), flatten(), and strict branch/leaf type checking.
    """

    def __init__(self) -> None:
        self._root: Dict[str, Any] = {}

    @staticmethod
    def _split(path: str) -> List[str]:
        if not path:
            raise ValueError("path must not be empty")
        return path.split(".")

    # ---- stage 1: set / get / delete ----

    def set(self, path: str, value: Any) -> None:
        segments = self._split(path)
        node = self._root
        for segment in segments[:-1]:
            child = node.get(segment)
            if child is None:
                child = {}
                node[segment] = child
            elif _LEAF in child:
                raise TypeError(f"{segment!r} is already a leaf; cannot descend into it")
            node = child

        last = segments[-1]
        existing = node.get(last)
        if existing is not None and _LEAF not in existing:
            raise TypeError(f"{last!r} is already a branch; cannot overwrite it with a leaf")
        node[last] = {_LEAF: value}

    def get(self, path: str) -> Any:
        node = self._navigate(path)
        if node is None or _LEAF not in node:
            return None
        return node[_LEAF]

    def delete(self, path: str) -> None:
        segments = self._split(path)
        node = self._root
        parents: List[Tuple[Dict[str, Any], str]] = []
        for segment in segments[:-1]:
            child = node.get(segment)
            if child is None:
                return  # path doesn't exist -- nothing to delete
            parents.append((node, segment))
            node = child
        node.pop(segments[-1], None)
        # prune now-empty ancestor branches so children()/flatten() don't surface
        # dangling former-branches with nothing under them
        for parent, segment in reversed(parents):
            if not parent[segment]:
                del parent[segment]
            else:
                break

    # ---- stage 2: children ----

    def children(self, prefix: str = "") -> List[str]:
        """Sorted immediate child segment names directly under prefix (not full
        paths, not recursive). prefix="" lists top-level keys. A path that is a
        leaf, or doesn't exist, has no children -- returns [], not an error."""
        node = self._root if prefix == "" else self._navigate(prefix)
        if node is None:
            return []
        return sorted(key for key in node.keys() if key != _LEAF)

    # ---- stage 3: flatten ----

    def flatten(self) -> Dict[str, Any]:
        """Every leaf in the store as a flat {"a.b.c": value} dict."""
        result: Dict[str, Any] = {}
        self._flatten_into(self._root, [], result)
        return result

    def _flatten_into(self, node: Dict[str, Any], prefix_segments: List[str], out: Dict[str, Any]) -> None:
        for key, child in node.items():
            if key == _LEAF:
                continue
            path_segments = prefix_segments + [key]
            if _LEAF in child:
                out[".".join(path_segments)] = child[_LEAF]
            else:
                self._flatten_into(child, path_segments, out)

    # ---- shared navigation ----

    def _navigate(self, path: str) -> Optional[Dict[str, Any]]:
        node = self._root
        for segment in self._split(path):
            node = node.get(segment)
            if node is None:
                return None
        return node


def main() -> None:
    """Reads newline-delimited commands from stdin by default, or from a file
    path given as argv[1]. Commands:
        SET path value
        GET path
        DELETE path
        CHILDREN [prefix]
        FLATTEN
    Prints one line per GET (value or NULL), CHILDREN (comma-joined, possibly
    empty), and FLATTEN (one "path=value" pair per line, sorted by path).
    """
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        lines = sys.stdin.read().splitlines()

    store = NestedPathKV()
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        cmd = parts[0].upper()
        if cmd == "SET" and len(parts) >= 3:
            store.set(parts[1], " ".join(parts[2:]))
        elif cmd == "GET" and len(parts) == 2:
            value = store.get(parts[1])
            print(value if value is not None else "NULL")
        elif cmd == "DELETE" and len(parts) == 2:
            store.delete(parts[1])
        elif cmd == "CHILDREN":
            prefix = parts[1] if len(parts) > 1 else ""
            print(",".join(store.children(prefix)))
        elif cmd == "FLATTEN":
            for path, value in sorted(store.flatten().items()):
                print(f"{path}={value}")


if __name__ == "__main__":
    main()
