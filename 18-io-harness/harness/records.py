"""
harness.records — light parsing helpers for turning raw text fields into typed data.

Three pieces, meant to be used together: coerce a raw string field to a concrete type,
split a CSV-ish line into fields without choking on quotes, and build a small typed
record (dataclass) out of a row of fields. Standard library only (Python 3.10+).
"""
from __future__ import annotations

import csv
import dataclasses
import re
from typing import Any, Callable, Dict, List, Sequence, Union

Scalar = Union[int, float, bool, None, str]

_TRUE_STRINGS = {"true", "yes", "y", "1"}
_FALSE_STRINGS = {"false", "no", "n", "0"}

# Deliberately stricter than Python's own int()/float(): those also accept "1_000"
# (PEP 515 grouping), "inf", "nan", "Infinity" — all surprising if a data field happens
# to contain that literal text. Only "looks like a plain number" matches here.
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")


# --------------------------------------------------------------------------------------
# typed field coercion
# --------------------------------------------------------------------------------------


def coerce(value: str) -> Scalar:
    """Best-effort type inference for one raw field: int, then float, then true/false,
    then None for blank/whitespace-only, else the original string unchanged.

    Numeric/boolean recognition tolerates surrounding whitespace; a non-numeric fallback
    returns the original string exactly as given (whitespace included).

    Example: coerce('42') -> 42; coerce('3.5') -> 3.5; coerce('true') -> True; coerce('') -> None
    """
    text = value.strip()
    if text == "":
        return None
    lowered = text.lower()
    if lowered in _TRUE_STRINGS:
        return True
    if lowered in _FALSE_STRINGS:
        return False
    if _INT_RE.match(text):
        return int(text)
    if _FLOAT_RE.match(text):
        return float(text)
    return value


def coerce_row(fields: Sequence[str]) -> List[Scalar]:
    """Apply coerce() to every field in a row.

    Example: coerce_row(['1', 'a', '']) -> [1, 'a', None]
    """
    return [coerce(f) for f in fields]


def coerce_as(value: str, converter: Callable[[str], Any]) -> Any:
    """Apply a specific converter (int, float, str, or your own function) to one field,
    raising a ValueError with the offending value in the message on failure — easier to
    debug mid-round than a bare "invalid literal for int() with base 10: ...".

    Example: coerce_as('42', int) -> 42
    """
    try:
        return converter(value)
    except (ValueError, TypeError) as exc:
        name = getattr(converter, "__name__", repr(converter))
        raise ValueError(f"cannot parse {value!r} as {name}") from exc


# --------------------------------------------------------------------------------------
# tolerant CSV splitting
# --------------------------------------------------------------------------------------


def split_csv_line(line: str, delimiter: str = ",") -> List[str]:
    """Split one line of CSV-ish text into fields, honoring quoted fields and delimiters
    embedded inside them (built on the stdlib csv module — do not hand-roll a
    line.split(',') for real CSV, it breaks on the first quoted comma).

    Pass a single line (no embedded newline); a trailing '\\n' or '\\r\\n' is tolerated.
    A malformed/unbalanced quote does not raise — it reads to the end of the line as
    part of the open field, same as Python's csv module does everywhere else.

    Example: split_csv_line('a,"b,c",d') -> ['a', 'b,c', 'd']
    """
    line = line.rstrip("\r\n")
    return next(csv.reader([line], delimiter=delimiter), [])


# --------------------------------------------------------------------------------------
# fixed-schema record factory
# --------------------------------------------------------------------------------------


def record_factory(
    name: str, field_types: Dict[str, Callable[[str], Any]], frozen: bool = False
) -> Callable[[Sequence[str]], Any]:
    """Build a factory that turns a row of raw string fields into a typed record
    (a dataclass under the hood). Field order follows field_types' insertion order.

    Example:
        make_point = record_factory('Point', {'x': int, 'y': int})
        p = make_point(['3', '4'])
        (p.x, p.y) == (3, 4)

    Pass frozen=True for an immutable/hashable record (e.g. to use as a dict key or in
    a set); the default is a plain mutable record, which is what most interview
    solutions want.
    """
    field_names = list(field_types.keys())
    converters = list(field_types.values())
    record_cls = dataclasses.make_dataclass(name, field_names, frozen=frozen)

    def build(row: Sequence[str]) -> Any:
        if len(row) != len(field_names):
            raise ValueError(
                f"{name}: expected {len(field_names)} field(s) {field_names}, got {len(row)}: {row!r}"
            )
        values = [coerce_as(raw, conv) for conv, raw in zip(converters, row)]
        return record_cls(*values)

    build.record_class = record_cls  # type: ignore[attr-defined]
    return build
