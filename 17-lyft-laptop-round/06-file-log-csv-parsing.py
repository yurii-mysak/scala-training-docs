"""17-lyft-laptop-round / 06-file-log-csv-parsing

Three related I/O-heavy sub-problems bundled into one family, because they're
reported together and share the same underlying lesson: this round's dominant
failure mode is input/output handling, not algorithms. See 00-protocol.md.

  (a) kth_non_empty_line -- print the K-th non-empty line of a large UTF-8 file
      without loading it into memory.
  (b) split_csv_line -- split one CSV-style line into fields, honoring a custom
      delimiter and quoted fields, hand-rolled rather than via the csv module (the
      point of the exercise is demonstrating you can write the state machine, not
      that you know the stdlib exists).
  (c) percentile / aggregate_latencies -- log-aggregation variant computing p50/p95
      over a file of latency values.

Ask which of the three is actually wanted before building all three -- see
00-protocol.md's first-five-minutes checklist.

Run directly to see a demo of all three:
    python3 06-file-log-csv-parsing.py
"""

from __future__ import annotations

import math
import sys
from typing import Dict, List, Optional, Sequence


# --------------------------------------------------------------------------- #
# (a) K-th non-empty line of a large file, without loading it into memory
# --------------------------------------------------------------------------- #


def kth_non_empty_line(path: str, k: int, encoding: str = "utf-8") -> Optional[str]:
    """Returns the k-th (1-indexed) non-empty line of a file, streaming it one
    line at a time -- iterating a file object in Python is already lazy/buffered,
    it does not read the whole file into memory at once. Returns None if the file
    has fewer than k non-empty lines.

    "Empty" here means blank or whitespace-only after stripping the line ending --
    confirm with the interviewer whether a whitespace-only line should count as
    empty; that's a real ambiguity, not a solved question.

    A missing trailing newline on the last line needs no special handling: Python's
    line iteration yields that final line exactly once either way.
    """
    if k <= 0:
        raise ValueError("k must be >= 1")
    count = 0
    with open(path, "r", encoding=encoding) as f:
        for raw_line in f:
            line = raw_line.rstrip("\n\r")
            if line.strip() == "":
                continue
            count += 1
            if count == k:
                return line
    return None


# --------------------------------------------------------------------------- #
# (b) CSV line splitting: custom separator, quoted fields, escaped quotes
# --------------------------------------------------------------------------- #


def split_csv_line(line: str, delimiter: str = ",", quote: str = '"') -> List[str]:
    """Splits one CSV-style line into fields by hand (no csv module -- that is
    the point of this exercise). Honors:
      - a custom delimiter (comma, tab, pipe, whatever is asked for)
      - quoted fields, which may contain the delimiter or embedded newlines-as-text
      - "" inside a quoted field as an escaped literal quote character (RFC 4180)

    Permissive on malformed input: an unmatched trailing quote just ends the field
    at end-of-line rather than raising. Add strict validation if the interviewer
    wants RFC 4180 compliance rather than best-effort parsing.
    """
    fields: List[str] = []
    field_chars: List[str] = []
    in_quotes = False
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if in_quotes:
            if ch == quote:
                if i + 1 < n and line[i + 1] == quote:
                    field_chars.append(quote)  # escaped literal quote
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            field_chars.append(ch)
            i += 1
        else:
            if ch == quote and not field_chars:
                in_quotes = True
                i += 1
            elif ch == delimiter:
                fields.append("".join(field_chars))
                field_chars = []
                i += 1
            else:
                field_chars.append(ch)
                i += 1
    fields.append("".join(field_chars))
    return fields


# --------------------------------------------------------------------------- #
# (c) Log aggregation: p50 / p95 over a file of latency values
# --------------------------------------------------------------------------- #


def percentile(sorted_values: Sequence[float], p: float) -> float:
    """Nearest-rank percentile over an already-sorted ascending sequence. p is a
    percentage in [0, 100]. Uses the nearest-rank method (index =
    ceil(p/100 * n), 1-indexed then clamped) -- the common convention for ops
    dashboards; confirm if the interviewer wants linear interpolation instead,
    that's a different (and slightly more involved) formula.
    """
    if not sorted_values:
        raise ValueError("percentile of an empty sequence is undefined")
    if not 0 <= p <= 100:
        raise ValueError("p must be within [0, 100]")
    n = len(sorted_values)
    rank = max(1, math.ceil(p / 100 * n))
    return sorted_values[min(rank, n) - 1]


def aggregate_latencies(path: str, encoding: str = "utf-8") -> Dict[str, Optional[float]]:
    """Streams a log file of one latency value per line -- either a bare number,
    or a "timestamp,latency_ms" row (only the last comma-separated field is used,
    so both formats work unmodified) -- and returns count/p50/p95. Malformed lines
    are skipped rather than aborting the whole aggregation; an all-malformed or
    empty file returns None for the percentiles rather than raising, since "no
    data" is a normal outcome for a log aggregation tool, not an error condition.

    At true production scale you cannot hold every value in memory to compute an
    exact percentile from a firehose; the real answer there is an approximate
    streaming structure (t-digest, HdrHistogram, or reservoir sampling) -- name
    that as the follow-up, this function's exact-and-in-memory approach is the
    right scope for an interview-sized log file.
    """
    values: List[float] = []
    with open(path, "r", encoding=encoding) as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            raw_value = line.split(",")[-1]
            try:
                values.append(float(raw_value))
            except ValueError:
                continue
    if not values:
        return {"count": 0, "p50": None, "p95": None}
    values.sort()
    return {
        "count": len(values),
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
    }


def main() -> None:
    """CLI dispatcher for the three sub-problems above -- confirm with the
    interviewer which one is actually being asked for before building all three.

    Usage:
        python3 06-file-log-csv-parsing.py            # csv mode, reads stdin
        python3 06-file-log-csv-parsing.py csv         # same, explicit
        python3 06-file-log-csv-parsing.py kth <path> <k>
        python3 06-file-log-csv-parsing.py agg <path>

    csv mode is the stdin default (it's naturally line-oriented, works fine over a
    stream); kth/agg take a file path because "without loading it into memory"
    only means something against a real file on disk, not a stream you'd read
    once anyway.
    """
    args = sys.argv[1:]
    mode = args[0] if args else "csv"

    if mode == "kth":
        path, k = args[1], int(args[2])
        line = kth_non_empty_line(path, k)
        print(line if line is not None else "")
    elif mode == "agg":
        path = args[1]
        result = aggregate_latencies(path)
        print(f"count={result['count']} p50={result['p50']} p95={result['p95']}")
    else:
        for raw_line in sys.stdin:
            line = raw_line.rstrip("\n")
            if not line:
                continue
            print("\t".join(split_csv_line(line)))


if __name__ == "__main__":
    main()
