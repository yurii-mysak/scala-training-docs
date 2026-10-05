#!/usr/bin/env python3
"""Shared helpers for the IT Iaido engine (see dojo/SPEC.md).

Everything here is stdlib + PyYAML.  The repo root is located relative to this
file (dojo/engine/common.py -> repo root is two levels up).  The environment
variable DOJO_REPO overrides it (used by the tests); DOJO_NOW overrides "now"
with an ISO timestamp so runs can be reproduced.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

import yaml

# --------------------------------------------------------------------------- constants

LEVELS = {"B": "Beginner", "I": "Intermediate", "A": "Advanced"}
LEVEL_ORDER = ["B", "I", "A"]
# Tie-break / display order of tracks (SPEC §1 priorities); unknown tracks come after.
TRACK_ORDER = ["ai-ml", "claude-academy", "fp-scala", "ddia", "architecture", "networking", "rust"]
STATUSES = ("sent", "passed", "review", "skipped")
DEFAULT_REPO_URL = "https://github.com/yurii-mysak/scala-training-docs"
# YYYY-MM-DD-N-<slug>.md
LESSON_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d+)-(.+)\.md$")
RECENT_FRESH_WINDOW = 8


class DojoError(Exception):
    """A user-facing error: the CLIs print it as `error: ...` and exit 2."""


# --------------------------------------------------------------------------- paths

def repo_root() -> Path:
    env = os.environ.get("DOJO_REPO")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[2]


def dojo_dir() -> Path:
    return repo_root() / "dojo"


def curriculum_dir() -> Path:
    return dojo_dir() / "curriculum"


def progress_dir() -> Path:
    return dojo_dir() / "progress"


def state_path() -> Path:
    return progress_dir() / "state.json"


def log_path() -> Path:
    return progress_dir() / "log.jsonl"


def lessons_dir() -> Path:
    return dojo_dir() / "lessons"


def assets_dir() -> Path:
    return lessons_dir() / "assets"


def out_dir() -> Path:
    return dojo_dir() / "out"


def feeds_path() -> Path:
    return dojo_dir() / "feeds.yaml"


def templates_dir() -> Path:
    # Templates live next to the scripts, wherever the scripts were copied to.
    return Path(__file__).resolve().parent / "templates"


def rel(path: Path | str) -> str:
    """Path relative to the repo root (POSIX style) when possible."""
    p = Path(path).resolve()
    try:
        return p.relative_to(repo_root()).as_posix()
    except ValueError:
        return p.as_posix()


# --------------------------------------------------------------------------- time (UTC + Kyiv)

class _KyivFallback(dt.tzinfo):
    """Europe/Kyiv without tzdata: UTC+2, UTC+3 between the last Sundays of Mar/Oct (01:00 UTC)."""

    @staticmethod
    def _last_sunday(year: int, month: int) -> dt.datetime:
        d = dt.datetime(year, month, 31, 1, tzinfo=dt.timezone.utc)
        return d - dt.timedelta(days=(d.weekday() + 1) % 7)

    def _is_dst_utc(self, utc: dt.datetime) -> bool:
        return self._last_sunday(utc.year, 3) <= utc < self._last_sunday(utc.year, 10)

    def utcoffset(self, d: dt.datetime | None):
        if d is None:
            return dt.timedelta(hours=2)
        naive_local = d.replace(tzinfo=None)
        # Approximate: interpret local time as UTC+2 to find the UTC instant.
        utc = (naive_local - dt.timedelta(hours=2)).replace(tzinfo=dt.timezone.utc)
        return dt.timedelta(hours=3 if self._is_dst_utc(utc) else 2)

    def dst(self, d):
        return dt.timedelta(hours=1) if self.utcoffset(d) == dt.timedelta(hours=3) else dt.timedelta(0)

    def fromutc(self, d):
        utc = d.replace(tzinfo=dt.timezone.utc)
        return (utc + dt.timedelta(hours=3 if self._is_dst_utc(utc) else 2)).replace(tzinfo=self)

    def tzname(self, d):
        return "EEST" if self.dst(d) else "EET"


def kyiv_tz() -> dt.tzinfo:
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Kyiv")
    except Exception:  # tzdata missing
        return _KyivFallback()


def parse_ts(value: str | dt.datetime | dt.date) -> dt.datetime:
    """Parse an ISO timestamp / date into an aware UTC datetime (naive input = UTC)."""
    if isinstance(value, dt.datetime):
        d = value
    elif isinstance(value, dt.date):
        d = dt.datetime(value.year, value.month, value.day)
    else:
        s = str(value).strip()
        if len(s) == 10:
            s += "T00:00:00"
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def now_utc() -> dt.datetime:
    env = os.environ.get("DOJO_NOW")
    if env:
        return parse_ts(env).replace(microsecond=0)
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso_z(d: dt.datetime) -> str:
    return d.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_iso() -> str:
    return iso_z(now_utc())


def to_kyiv(d: dt.datetime) -> dt.datetime:
    return d.astimezone(kyiv_tz())


def kyiv_today() -> dt.date:
    return to_kyiv(now_utc()).date()


def kyiv_date_of(ts: str | dt.datetime) -> dt.date:
    return to_kyiv(parse_ts(ts)).date()


def parse_date(s: str | dt.date) -> dt.date:
    if isinstance(s, dt.datetime):
        return s.date()
    if isinstance(s, dt.date):
        return s
    return dt.date.fromisoformat(str(s)[:10])


def human_date(d: dt.date) -> str:
    """'Tue 6 Oct 2026' (no platform-specific strftime flags)."""
    return f"{d.strftime('%a')} {d.day} {d.strftime('%b %Y')}"


# --------------------------------------------------------------------------- YAML / JSON

_TS_TAG = "tag:yaml.org,2002:timestamp"


def _no_timestamps(resolvers: dict) -> dict:
    return {k: [(t, r) for (t, r) in v if t != _TS_TAG] for k, v in resolvers.items()}


class _Loader(yaml.SafeLoader):
    """SafeLoader that keeps dates/timestamps as plain strings (SPEC front matter is textual)."""


class _Dumper(yaml.SafeDumper):
    """SafeDumper that emits dates unquoted and multi-line text as literal blocks."""


_Loader.yaml_implicit_resolvers = _no_timestamps(yaml.SafeLoader.yaml_implicit_resolvers)
_Dumper.yaml_implicit_resolvers = _no_timestamps(yaml.SafeDumper.yaml_implicit_resolvers)


def _repr_str(dumper: yaml.SafeDumper, data: str):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _repr_str)


def load_yaml_text(text: str) -> Any:
    return yaml.load(text, Loader=_Loader)


def dump_yaml(data: Any) -> str:
    return yaml.dump(data, Dumper=_Dumper, sort_keys=False, allow_unicode=True,
                     default_flow_style=False, width=100000)


def load_yaml(path: Path) -> Any:
    return load_yaml_text(Path(path).read_text(encoding="utf-8"))


def save_yaml(path: Path, data: Any) -> None:
    atomic_write(path, dump_yaml(data))


def load_json(path: Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise DojoError(f"{rel(p)} is not valid JSON: {e}")


def save_json(path: Path, data: Any) -> None:
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def atomic_write(path: Path | str, text: str) -> None:
    """Write text via a temp file + rename so a crash never leaves a half-written file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=f".{p.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# --------------------------------------------------------------------------- front matter & lessons

_FM_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.S)


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Split a lesson file into (front matter dict, body)."""
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    fm = load_yaml_text(m.group(1)) or {}
    if not isinstance(fm, dict):
        raise DojoError("front matter is not a mapping")
    return fm, text[m.end():]


def build_lesson_text(fm: dict, body: str) -> str:
    return "---\n" + dump_yaml(fm) + "---\n" + body


def load_lesson(path: Path) -> tuple[dict, str]:
    return parse_front_matter(Path(path).read_text(encoding="utf-8"))


def save_lesson(path: Path, fm: dict, body: str) -> None:
    atomic_write(path, build_lesson_text(fm, body))


def lesson_files() -> list[Path]:
    d = lessons_dir()
    if not d.exists():
        return []
    return sorted(p for p in d.glob("*.md") if LESSON_FILE_RE.match(p.name))


def lesson_slug(path: Path) -> str:
    m = LESSON_FILE_RE.match(Path(path).name)
    return m.group(3) if m else Path(path).stem


def load_all_lessons() -> list[dict]:
    """Every lesson as {'path', 'fm', 'body'}, sorted by id (date, then N)."""
    out = []
    for p in lesson_files():
        fm, body = load_lesson(p)
        if not fm.get("id"):
            m = LESSON_FILE_RE.match(p.name)
            fm["id"] = f"{m.group(1)}-{m.group(2)}"
        out.append({"path": p, "fm": fm, "body": body})
    out.sort(key=lambda x: _id_sort_key(x["fm"]["id"]))
    return out


def _id_sort_key(lesson_id: str) -> tuple:
    m = re.match(r"^(\d{4}-\d{2}-\d{2})-(\d+)$", str(lesson_id))
    return (m.group(1), int(m.group(2))) if m else (str(lesson_id), 0)


def find_lesson_path(ref: str | Path) -> Path:
    """Resolve a lesson id (2026-10-06-1) or a path to the lesson file."""
    p = Path(str(ref))
    if p.suffix == ".md":
        for cand in (p, repo_root() / p):
            if cand.exists():
                return cand.resolve()
        raise DojoError(f"lesson file not found: {ref}")
    matches = sorted(lessons_dir().glob(f"{ref}-*.md")) if lessons_dir().exists() else []
    matches = [m for m in matches if LESSON_FILE_RE.match(m.name)]
    if not matches:
        raise DojoError(f"no lesson with id {ref!r} in {rel(lessons_dir())}")
    if len(matches) > 1:
        raise DojoError(f"id {ref!r} matches several files: {[m.name for m in matches]}")
    return matches[0]


# --------------------------------------------------------------------------- progress log

def log_event(event: str, lesson: str | None = None, by: str = "job", note: str = "") -> dict:
    """Append one JSON line to dojo/progress/log.jsonl (append-only)."""
    rec = {"ts": now_iso(), "event": event, "lesson": lesson, "by": by, "note": note}
    p = log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


# --------------------------------------------------------------------------- curriculum

def track_sort_key(key: str) -> tuple:
    return (TRACK_ORDER.index(key), "") if key in TRACK_ORDER else (len(TRACK_ORDER), key)


def load_curriculum() -> dict[str, dict]:
    """All curriculum files as {track_key: data}, ordered by TRACK_ORDER then name.

    Returns {} when the folder is missing or empty (callers decide whether that is fatal).
    Light normalisation only (weight default 1, rungs default []); the schema is not validated here.
    """
    d = curriculum_dir()
    tracks: dict[str, dict] = {}
    if not d.exists():
        return tracks
    for p in sorted(list(d.glob("*.yaml")) + list(d.glob("*.yml"))):
        try:
            data = load_yaml(p)
        except yaml.YAMLError as e:
            raise DojoError(f"{rel(p)} is not valid YAML: {e}")
        if not isinstance(data, dict):
            raise DojoError(f"{rel(p)}: top level must be a mapping")
        key = str(data.get("track") or p.stem)
        data["track"] = key
        data.setdefault("name", key)
        w = data.get("weight", 1)
        data["weight"] = w if isinstance(w, (int, float)) and not isinstance(w, bool) else 1
        data["rungs"] = [r for r in (data.get("rungs") or []) if isinstance(r, dict)]
        data["_file"] = p.name
        tracks[key] = data
    return {k: tracks[k] for k in sorted(tracks, key=track_sort_key)}


def require_curriculum() -> dict[str, dict]:
    tracks = load_curriculum()
    if not tracks:
        raise DojoError(f"no curriculum found: put <track>.yaml files in {rel(curriculum_dir())}/ "
                        "(schema: dojo/SPEC.md section 3)")
    return tracks


def rung_lookup(tracks: dict[str, dict]) -> dict[str, tuple[str, int, dict]]:
    """rung id -> (track key, index in track, rung dict)."""
    out: dict[str, tuple[str, int, dict]] = {}
    for key, t in tracks.items():
        for i, r in enumerate(t["rungs"]):
            if r.get("id"):
                out[str(r["id"])] = (key, i, r)
    return out


def track_files_to(tracks: dict[str, dict], key: str | None) -> str | None:
    t = tracks.get(key or "")
    return t.get("files_to") if t else None


# --------------------------------------------------------------------------- text utilities

def slugify(text: str, max_len: int = 60) -> str:
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    if len(s) > max_len:
        s = s[:max_len].rsplit("-", 1)[0] if "-" in s[:max_len] else s[:max_len]
    return s or "lesson"


def level_name(code: str | None) -> str:
    return LEVELS.get(str(code or "B").upper(), str(code))


_FENCE_BLOCK_RE = re.compile(r"(^```.*?^```[ \t]*$)", re.S | re.M)


def strip_html_comments(md: str) -> str:
    """Remove <!-- ... --> comments (scaffold hints) everywhere except inside fenced code."""
    parts = _FENCE_BLOCK_RE.split(md)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"<!--.*?-->[ \t]*\n?", "", parts[i], flags=re.S)
    out = "".join(parts)
    return re.sub(r"\n{4,}", "\n\n\n", out)


_MERMAID_RE = re.compile(r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)


def find_mermaid_blocks(md: str) -> list[dict]:
    """Mermaid fences in order: [{'k': 1, 'source': str, 'start': int, 'end': int}] (k is 1-based)."""
    return [{"k": i, "source": m.group(1).rstrip("\n"), "start": m.start(), "end": m.end()}
            for i, m in enumerate(_MERMAID_RE.finditer(md), start=1)]


def replace_mermaid_blocks(md: str, repl) -> str:
    """Replace every mermaid fence with repl(block) (block as returned by find_mermaid_blocks)."""
    out, pos = [], 0
    for b in find_mermaid_blocks(md):
        out.append(md[pos:b["start"]])
        out.append(repl(b))
        pos = b["end"]
    out.append(md[pos:])
    return "".join(out)


def split_sections(body: str) -> list[tuple[str | None, list[str]]]:
    """Split a lesson body into (heading, lines) by '## ' headings, ignoring fenced code.

    The first item has heading None and holds everything before the first '## ' (title, meta line).
    """
    sections: list[tuple[str | None, list[str]]] = [(None, [])]
    in_fence = False
    for line in body.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
        m = None if in_fence else re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            sections.append((m.group(1), []))
        else:
            sections[-1][1].append(line)
    return sections


def drop_section(body: str, heading: str) -> str:
    """Remove a '## <heading>' section (to the next '## ' or the end)."""
    out: list[str] = []
    skipping = False
    in_fence = False
    for line in body.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
        if not in_fence and re.match(r"^##\s+", line):
            skipping = bool(re.match(rf"^##\s+{re.escape(heading)}\s*$", line, re.I))
        if not skipping:
            out.append(line)
    return "\n".join(out).rstrip() + "\n"


def clean_inline_md(text: str) -> str:
    """Flatten inline Markdown (links, emphasis, code, html tags) to plain text."""
    t = re.sub(r"<[^>]+>", "", text)
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[`*_]{1,3}", "", t)
    return re.sub(r"\s+", " ", t).strip()


def trim_text(text: str, max_len: int = 80) -> str:
    """Trim to about max_len characters at a word boundary, adding an ellipsis when cut."""
    t = text.strip()
    if len(t) <= max_len:
        return t
    cut = t[:max_len].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return cut + "…"


def first_sentence(text: str, max_len: int = 80) -> str:
    plain = clean_inline_md(text)
    m = re.match(r"(.+?[.!?])(\s|$)", plain)
    return trim_text(m.group(1) if m else plain, max_len)


def section_text(body: str, heading: str) -> str:
    for h, lines in split_sections(body):
        if h and h.lower() == heading.lower():
            return "\n".join(lines).strip()
    return ""


def render_template(text: str, ctx: dict[str, Any]) -> str:
    """Tiny template engine: {{name}} substitution and {{#name}}...{{/name}} conditional blocks.

    Conditional tags should sit on their own line; they and their newline vanish from the output.
    Values are never re-scanned, so inserted text may contain braces safely.
    """
    cond = re.compile(r"\{\{#(\w+)\}\}[ \t]*\n?(.*?)\{\{/\1\}\}[ \t]*\n?", re.S)
    prev = None
    while prev != text:
        prev = text
        text = cond.sub(lambda m: m.group(2) if ctx.get(m.group(1)) else "", text)
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(ctx.get(m.group(1), "")), text)


# --------------------------------------------------------------------------- CLI helpers

def die(message: str, code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def run_cli(main) -> None:
    """Run main() turning DojoError into a clean `error:` line and exit code 2."""
    try:
        rc = main()
    except DojoError as e:
        die(str(e))
    sys.exit(rc or 0)


def dumps(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
