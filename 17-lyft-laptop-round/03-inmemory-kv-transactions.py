"""17-lyft-laptop-round / 03-inmemory-kv-transactions

Part 1: SET / GET / DELETE on an in-memory key-value store.
Part 2: BEGIN / COMMIT / ROLLBACK on top of Part 1, with nested transactions.

This is the family with the most concretely reported failure mode in this whole
section: a candidate finished Part 1, believed they were done, and was told "we
expect that part to be covered" -- meaning Part 2 (transactions) was assumed
in-scope from the start, not an optional stretch goal. Treat SET/GET/DELETE as the
opening 15-20 minutes of the problem, not the whole problem. See
03-inmemory-kv-transactions.md and 00-protocol.md.

Run directly to see a demo against a short command script:
    python3 03-inmemory-kv-transactions.py
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Iterable, List, Optional


class _Missing:
    """Sentinel: this key was explicitly DELETEd within the current transaction
    frame, as distinct from "never touched in this frame" (which is just absence
    from the frame's dict). Needed because a plain dict can't otherwise tell apart
    "shadow the outer value with nothing" from "no opinion, look further out."
    """

    def __repr__(self) -> str:
        return "<deleted>"


_MISSING = _Missing()


class TransactionalKVStore:
    """Part 1 (SET/GET/DELETE) plus Part 2 (BEGIN/COMMIT/ROLLBACK, nested).

    Design: a base committed dict, plus a stack of "frames" -- one dict per open
    transaction, innermost last. A write inside a transaction only touches the top
    frame. A read walks the stack from innermost to outermost, returning the first
    frame that has an opinion about the key (including "deleted"), falling back to
    the committed store only if no open frame mentions the key at all.

    COMMIT on a nested transaction merges its frame into its *parent* frame -- it
    only reaches the committed store once the outermost transaction commits.
    COMMIT with no open transaction is the same as committing directly to the
    committed store (SET/DELETE with no BEGIN behave exactly this way already).
    ROLLBACK discards the top frame outright, undoing everything done inside it,
    including any nested COMMITs that never reached an outer scope.
    """

    def __init__(self) -> None:
        self._committed: Dict[str, Any] = {}
        self._stack: List[Dict[str, Any]] = []

    # ---- Part 1 ----

    def set(self, key: str, value: str) -> None:
        if self._stack:
            self._stack[-1][key] = value
        else:
            self._committed[key] = value

    def get(self, key: str) -> Optional[str]:
        for frame in reversed(self._stack):
            if key in frame:
                value = frame[key]
                return None if value is _MISSING else value
        return self._committed.get(key)

    def delete(self, key: str) -> None:
        if self._stack:
            self._stack[-1][key] = _MISSING
        else:
            self._committed.pop(key, None)

    # ---- Part 2 ----

    def begin(self) -> None:
        self._stack.append({})

    def commit(self) -> None:
        if not self._stack:
            raise RuntimeError("COMMIT with no active transaction")
        frame = self._stack.pop()
        if self._stack:
            self._stack[-1].update(frame)  # merge into the parent frame
        else:
            for key, value in frame.items():
                if value is _MISSING:
                    self._committed.pop(key, None)
                else:
                    self._committed[key] = value

    def rollback(self) -> None:
        if not self._stack:
            raise RuntimeError("ROLLBACK with no active transaction")
        self._stack.pop()  # discard the whole frame, nothing more to do

    @property
    def in_transaction(self) -> bool:
        return bool(self._stack)

    @property
    def transaction_depth(self) -> int:
        return len(self._stack)


def run_commands(lines: Iterable[str], store: Optional[TransactionalKVStore] = None) -> List[str]:
    """Executes newline-style commands against a TransactionalKVStore and returns
    the output lines: one per GET (the value, or the literal string "NULL" for a
    missing key), and one per COMMIT/ROLLBACK issued with no open transaction (an
    error line, rather than raising and losing the rest of the script -- a command
    stream should not exception the whole program over one bad command). These are
    this file's chosen conventions -- confirm the exact expected strings with the
    interviewer rather than assuming; see 00-protocol.md.

    Commands (whitespace-separated, case-insensitive keyword):
        SET key value
        GET key
        DELETE key
        BEGIN
        COMMIT
        ROLLBACK
    """
    if store is None:
        store = TransactionalKVStore()
    output: List[str] = []
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
            output.append(value if value is not None else "NULL")
        elif cmd == "DELETE" and len(parts) == 2:
            store.delete(parts[1])
        elif cmd == "BEGIN" and len(parts) == 1:
            store.begin()
        elif cmd == "COMMIT" and len(parts) == 1:
            try:
                store.commit()
            except RuntimeError as exc:
                output.append(str(exc))
        elif cmd == "ROLLBACK" and len(parts) == 1:
            try:
                store.rollback()
            except RuntimeError as exc:
                output.append(str(exc))
        else:
            output.append(f"ERROR unrecognized command: {line}")
    return output


def main() -> None:
    """Reads commands from stdin by default, or from a file path given as
    argv[1] -- confirm which one the interviewer wants (see 00-protocol.md); this
    file supports both."""
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        lines = sys.stdin.read().splitlines()

    for output_line in run_commands(lines):
        print(output_line)


if __name__ == "__main__":
    main()
