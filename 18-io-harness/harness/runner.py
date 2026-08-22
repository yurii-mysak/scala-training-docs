"""
harness.runner — the CLI scaffold. solution.py imports main() from here and never needs
to touch argparse, resolve_input(), or output-writing directly.

    --input FILE     read from FILE instead of stdin
    --output FILE    write to FILE instead of stdout
    --format FMT     how to split each input line into a record: lines | whitespace | csv
    --verbose        print record counts to stderr (never to stdout — that would corrupt
                      the graded output)

Run this file directly for a smoke test of the scaffold itself (see USAGE.md):
    python3 -m harness.runner --format whitespace <<< $'1 2\\n3 4'
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional

# Make the absolute `harness.*` imports below resolve even if this file is ever run
# directly as `python3 harness/runner.py` (which puts harness/, not the project root,
# on sys.path). No effect on the documented invocations (python3 solution.py,
# python3 -m harness.runner, python3 -m unittest discover tests).
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from harness.io_utils import resolve_input, split_fields, strip_line_ending, write_file, write_stdout
from harness.records import split_csv_line

Solve = Callable[[List[Any]], Iterable[str]]

_FORMATS = ("lines", "whitespace", "csv")


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the harness's argparse parser.

    Example: build_arg_parser().parse_args(['--input', 'in.txt', '--format', 'csv'])
    """
    parser = argparse.ArgumentParser(
        prog="solution.py",
        description="Read --input or stdin, parse per --format, call solve(), write --output or stdout.",
    )
    parser.add_argument("--input", default=None, metavar="PATH", help="path to read; omit to read stdin")
    parser.add_argument("--output", default=None, metavar="PATH", help="path to write; omit to write stdout")
    parser.add_argument(
        "--format",
        choices=_FORMATS,
        default="lines",
        help="'lines' = raw string per line (default); 'whitespace' = list[str] split on "
        "whitespace; 'csv' = list[str], quote-aware comma split",
    )
    parser.add_argument("--verbose", action="store_true", help="log record counts/timing to stderr")
    return parser


def parse_record(line: str, fmt: str) -> Any:
    """Turn one raw (newline-stripped) line into a record per --format.

    Example: parse_record('a,b', 'csv') -> ['a', 'b']
    """
    if fmt == "lines":
        return line
    if fmt == "whitespace":
        return split_fields(line)
    if fmt == "csv":
        return split_csv_line(line)
    raise ValueError(f"unknown format: {fmt!r} (expected one of {_FORMATS})")


def load_records(input_path: Optional[str], fmt: str) -> List[Any]:
    """Resolve --input/stdin and parse every line into a record per --format.

    Example: load_records(None, 'lines')  # reads and parses stdin
    """
    with resolve_input(input_path) as stream:
        return [parse_record(strip_line_ending(raw), fmt) for raw in stream]


def main(solve: Solve, argv: Optional[List[str]] = None) -> None:
    """Parse argv, load records, call solve(records), write the result. This is the one
    call solution.py needs: `if __name__ == "__main__": main(solve)`.

    Example: main(solve)  # uses sys.argv[1:]
    """
    args = build_arg_parser().parse_args(argv)
    start = time.perf_counter()

    records = load_records(args.input, args.format)
    if args.verbose:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(
            f"[runner] loaded {len(records)} record(s) from {args.input or 'stdin'} "
            f"(format={args.format}) in {elapsed_ms:.1f}ms",
            file=sys.stderr,
        )

    result = solve(records)

    if args.output:
        write_file(args.output, result)
    else:
        write_stdout(result)

    if args.verbose:
        print(f"[runner] wrote output to {args.output or 'stdout'}", file=sys.stderr)


if __name__ == "__main__":
    # Smoke-test the scaffold on its own, independent of solution.py: echo each parsed
    # record back out as a string.
    main(lambda records: (str(r) for r in records))
