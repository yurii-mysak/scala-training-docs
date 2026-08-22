#!/usr/bin/env python3
"""
solution.py — this is the file you edit during the round. Everything else in this
project (harness/) is scaffolding; you should not need to touch it.

Already wired up for you:
    - stdin, or --input PATH, is read line by line (harness/runner.py)
    - --format controls how each line becomes a record (default 'lines' = raw string;
      see harness/runner.py for 'whitespace' and 'csv')
    - solve(records) is called with the parsed records; whatever it returns (an
      iterable of strings) is written to stdout, or --output PATH

Confirm the actual I/O channel and format with the interviewer first (USAGE.md has the
first-five-minutes checklist) — then delete the worked example below and replace it.

Try it right now, with no changes:
    $ printf '1 2 3\\n4 5\\n\\n6\\n' | python3 solution.py
    6
    9
    0
    6
"""
from __future__ import annotations

from typing import Iterable, List

from harness.runner import main


def solve(records: List[str]) -> Iterable[str]:
    """Replace this body with the actual problem. Keep the signature: a list of raw
    input lines in, an iterable of output lines out.

    Worked example (so the harness demonstrably runs before you change anything):
    sum the whitespace-separated integers on each line. A blank line sums to 0.
    """
    for line in records:
        yield str(sum(int(token) for token in line.split()))


if __name__ == "__main__":
    main(solve)
