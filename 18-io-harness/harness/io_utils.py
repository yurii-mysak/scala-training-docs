"""
harness.io_utils — every I/O channel the 90-minute laptop round has been reported to use.

The round's dominant failure mode is I/O handling, not algorithms (see ../README.md). These
functions exist so you never have to improvise stdin/file plumbing live: read the whole input,
stream it line by line, read from a file, parse a line into fields or a `CMD arg1 arg2` command,
write the result out. `resolve_input()` is the one to remember — it lets the exact same
`solve()` function satisfy a "read from stdin" problem and a "read from a file" problem.

Everything here is standard library only (Python 3.10+). No third-party imports.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import IO, Iterable, Iterator, List, Optional, Tuple


def strip_line_ending(line: str) -> str:
    """Remove one trailing line terminator: '\\r\\n', lone '\\n', or lone '\\r'.

    Deliberately does NOT rely on the stream having already normalized this: open()
    on a real file applies universal-newline translation (CRLF -> LF) automatically,
    but a piped sys.stdin does not on every platform/runtime -- a raw '\\r' can survive
    a naive line.rstrip('\\n') and then silently break a dict-key lookup or an exact
    string comparison later on (RUNBOOK.md's gotcha list). This function is safe to
    call whether or not that translation already happened.

    Example: strip_line_ending('abc\\r\\n') -> 'abc'
    """
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1]
    return line


# --------------------------------------------------------------------------------------
# stdin
# --------------------------------------------------------------------------------------


def read_stdin_all() -> str:
    """Read all of stdin into one string. Use for small/whole-input problems.

    Example: text = read_stdin_all()
    """
    return sys.stdin.read()


def iter_stdin_lines(strip_newline: bool = True, skip_blank: bool = False) -> Iterator[str]:
    """Yield stdin one line at a time. Memory-safe: never buffers the whole input.

    Blank lines come through as '' by default (not dropped) — pass skip_blank=True to
    filter them out.

    Example: for line in iter_stdin_lines(): handle(line)
    """
    for raw_line in sys.stdin:
        line = strip_line_ending(raw_line) if strip_newline else raw_line
        if skip_blank and line == "":
            continue
        yield line


# --------------------------------------------------------------------------------------
# files
# --------------------------------------------------------------------------------------


def read_file(path: str) -> str:
    """Read an entire file's contents as text (UTF-8). Use for small/whole-file problems.

    Example: text = read_file('input.txt')
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def iter_file_lines(path: str, strip_newline: bool = True, skip_blank: bool = False) -> Iterator[str]:
    """Stream a file one line at a time; never loads the whole file into memory.

    Use this instead of read_file(...).splitlines() for a "large file" or "large log"
    problem. Blank lines come through as '' by default — pass skip_blank=True to filter.

    Example: for line in iter_file_lines('big.log'): handle(line)
    """
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = strip_line_ending(raw_line) if strip_newline else raw_line
            if skip_blank and line == "":
                continue
            yield line


# --------------------------------------------------------------------------------------
# the channel-agnostic helper
# --------------------------------------------------------------------------------------


@contextmanager
def resolve_input(path: Optional[str] = None) -> Iterator[IO[str]]:
    """Yield a readable text stream for `path`, or stdin if path is None or '-'.

    This is the one helper that lets a single solve() satisfy both I/O channels the
    interviewer might name: wire --input straight through and stop worrying about which
    channel you're on.

    Only closes the stream it opened itself — stdin is left alone.

    Example:
        with resolve_input(args.input) as stream:
            for line in stream:
                handle(line)
    """
    if path is None or path == "-":
        yield sys.stdin
    else:
        f = open(path, "r", encoding="utf-8")
        try:
            yield f
        finally:
            f.close()


# --------------------------------------------------------------------------------------
# parsing a line into fields / a command
# --------------------------------------------------------------------------------------


def split_fields(line: str, delimiter: Optional[str] = None, strip_fields: bool = False) -> List[str]:
    """Split one line into fields. delimiter=None splits on any run of whitespace
    (like str.split()); pass ',' or any other literal delimiter for fixed-delimiter data.

    This is the fast, non-quote-aware splitter for whitespace/comma/custom-delimited
    records. For real CSV with quoted fields, use harness.records.split_csv_line instead.

    Example: split_fields('a, b ,c', delimiter=',', strip_fields=True) -> ['a', 'b', 'c']
    """
    fields = line.split() if delimiter is None else line.split(delimiter)
    return [f.strip() for f in fields] if strip_fields else fields


def parse_command(line: str) -> Tuple[str, List[str]]:
    """Parse a 'CMD arg1 arg2' line into (command, args). Whitespace-delimited; the
    command's case is preserved as written (call .upper() yourself if the grammar is
    case-insensitive). An empty/blank line returns ('', []).

    This is the shape used by the KV-store-with-transactions and job-scheduler problem
    families: SET/GET/DELETE, BEGIN/COMMIT/ROLLBACK, SCHEDULE/CANCEL, etc.

    Example: parse_command('SET x 5') -> ('SET', ['x', '5'])
    """
    parts = line.split()
    if not parts:
        return "", []
    return parts[0], parts[1:]


# --------------------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------------------


def _write_lines(stream: IO[str], lines: Iterable[str]) -> None:
    for line in lines:
        stream.write(line)
        stream.write("\n")


def write_stdout(lines: Iterable[str], stream: Optional[IO[str]] = None) -> None:
    """Write each item to stdout, one per line.

    `stream` defaults to whatever sys.stdout is AT CALL TIME (not import time) — this is
    what makes it work correctly under contextlib.redirect_stdout in tests. Never write
    `stream: IO[str] = sys.stdout` as a default value; that captures stdout once, at
    function-definition time (see RUNBOOK.md's gotcha list).

    Example: write_stdout(['a', 'b'])  # prints a\\nb\\n
    """
    _write_lines(stream if stream is not None else sys.stdout, lines)


def write_file(path: str, lines: Iterable[str]) -> None:
    """Write each item to a file, one per line, overwriting any existing content.

    Example: write_file('out.txt', ['a', 'b'])
    """
    with open(path, "w", encoding="utf-8") as f:
        _write_lines(f, lines)
