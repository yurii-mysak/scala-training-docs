#!/usr/bin/env python3
"""File a passed lesson into the knowledge base (SPEC §8).

  file_passed.py 2026-10-06-1
  file_passed.py --all-passed-unfiled

For a lesson whose status is `passed`:

 1. creates the target section folder (front matter `files_to`) with a README.md in the shape of
    10-networking/README.md when it does not exist yet;
 2. writes <files_to>/<slug>.md: the lesson body under a one-line `> Source: IT Iaido lesson ...`
    header block, without the dojo front matter and without "Next on this track";
 3. appends a row to the right level table of the section README (`#` continues across the
    Beginner / Intermediate / Advanced tables);
 4. adds `[Title](section/file.md)` to the section's `| B |` / `| I |` / `| A |` row in the root
    README.md - creating the row, or the whole `### [NN - Title](folder/)` block after the last
    numbered block, when missing;
 5. sets `filed_to` in the lesson front matter and logs a `filed` event.

Idempotent: a lesson whose `filed_to` file exists is skipped, and README rows / links that are already
present are never duplicated.  Run from the repo root.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import common
from common import DojoError

# Sections the engine creates on first filing (SPEC §2): section number -> (title, description).
NEW_SECTIONS = {
    "24": ("AI / ML Foundations",
           "Machine-learning foundations: what models optimise, how they are trained and evaluated, "
           "and how modern LLM systems are built and used."),
    "25": ("Software Architecture & Design",
           "Software architecture and design: boundaries, modularity, trade-offs, and the patterns "
           "behind systems that stay easy to change."),
    "26": ("Rust",
           "Rust for a JVM engineer: ownership, borrowing, lifetimes, traits, and the tooling "
           "around them."),
}
DEFAULT_DESCRIPTION = "Notes filed from the IT Iaido daily lessons."

TABLE_HEADER = "| # | Topic | File | Interview Focus |"
TABLE_RULE = "|---|-------|------|-----------------|"
ROOT_TABLE_HEADER = "| Level | Topics |"
ROOT_TABLE_RULE = "|-------|--------|"
QUESTIONS_HEADING = "## Key Interview Questions by Level"
QUESTIONS_PLACEHOLDER = "_Questions will be added as lessons in this section are passed._"

FOCUS_TARGET = 80      # "Interview Focus" is trimmed to about this many characters ...
FOCUS_SLACK = 10       # ... joined key points may run this much over before the next one is dropped
DASH_CELLS = ("", "—", "–", "-")


# --------------------------------------------------------------------------- section README

def section_info(folder: str, tracks: dict[str, dict]) -> tuple[str, str]:
    """(title, one-line description) for a section folder that has no README yet."""
    m = re.match(r"^(\d+)-(.*)$", folder)
    if m and m.group(1) in NEW_SECTIONS:
        return NEW_SECTIONS[m.group(1)]
    for t in tracks.values():
        if str(t.get("files_to", "")).strip("/") == folder:
            desc = common.first_sentence(str(t.get("description") or ""), 200) or DEFAULT_DESCRIPTION
            return str(t.get("name") or folder), desc
    slug = m.group(2) if m else folder
    return slug.replace("-", " ").title(), DEFAULT_DESCRIPTION


def new_readme_text(title: str, description: str) -> str:
    """A fresh section README, exactly the shape of 10-networking/README.md with empty tables."""
    out = [f"# {title}", "", description, ""]
    for level in common.LEVEL_ORDER:
        out += [f"## {common.LEVELS[level]}", "", TABLE_HEADER, TABLE_RULE, ""]
    out += [QUESTIONS_HEADING, ""]
    for level in common.LEVEL_ORDER:
        out += [f"**{common.LEVELS[level]}**: {QUESTIONS_PLACEHOLDER}", ""]
    return "\n".join(out).rstrip("\n") + "\n"


def _level_heading_index(lines: list[str], level: str) -> int | None:
    pat = re.compile(rf"^##\s+{common.LEVELS[level]}\b", re.I)   # '###' sub-headings do not match
    for i, line in enumerate(lines):
        if pat.match(line):
            return i
    return None


def _section_end(lines: list[str], start: int) -> int:
    """Index of the next '## ' heading after `start` (or len(lines))."""
    for i in range(start + 1, len(lines)):
        if re.match(r"^##\s", lines[i]):
            return i
    return len(lines)


def next_row_number(lines: list[str]) -> int:
    nums = [int(m.group(1)) for line in lines if (m := re.match(r"^\|\s*(\d+)\s*\|", line))]
    return max(nums, default=0) + 1


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def add_readme_row(text: str, level: str, topic: str, filename: str, focus: str) -> tuple[str, int]:
    """Append a topic row to the right level table.  Returns (new text, row number).

    Works on the standard shape (## Level / one table) and also on READMEs whose level has several
    `###` sub-tables (the row goes under the last one).  A missing level heading or table is created.
    """
    lines = text.splitlines()
    number = next_row_number(lines)
    if f"({filename})" in text:                       # already listed: keep the existing row
        m = next((re.match(r"^\|\s*(\d+)\s*\|", l) for l in lines if f"({filename})" in l), None)
        return text, int(m.group(1)) if m else number
    row = f"| {number} | {_md_cell(topic)} | [{filename}]({filename}) | {_md_cell(focus)} |"

    head = _level_heading_index(lines, level)
    if head is None:                                  # create the level section in order
        block = [f"## {common.LEVELS[level]}", "", TABLE_HEADER, TABLE_RULE, row, ""]
        later = [i for lv in common.LEVEL_ORDER[common.LEVEL_ORDER.index(level) + 1:]
                 if (i := _level_heading_index(lines, lv)) is not None]
        qh = next((i for i, l in enumerate(lines) if l.strip().lower().startswith(QUESTIONS_HEADING.lower())), None)
        at = min(later) if later else qh if qh is not None else len(lines)
        if at > 0 and lines[at - 1].strip():
            block.insert(0, "")
        lines[at:at] = block
        return "\n".join(lines).rstrip("\n") + "\n", number

    end = _section_end(lines, head)
    last_table: tuple[int, int] | None = None         # (first line, last line) of the last '#' table
    i = head + 1
    while i < end:
        if lines[i].startswith("|"):
            j = i
            while j + 1 < end and lines[j + 1].startswith("|"):
                j += 1
            if re.match(r"^\|\s*#\s*\|", lines[i]):
                last_table = (i, j)
            i = j + 1
        else:
            i += 1
    if last_table is None:                            # heading without a table: add one right below it
        lines[head + 1:head + 1] = ["", TABLE_HEADER, TABLE_RULE, row]
    else:
        lines.insert(last_table[1] + 1, row)
    return "\n".join(lines).rstrip("\n") + "\n", number


# --------------------------------------------------------------------------- root README

_BLOCK_RE = re.compile(r"^###\s+\[(?P<label>[^\]]+)\]\((?P<path>[^)]*)\)\s*$")
_ROW_RE = re.compile(r"^\|\s*(?P<lv>[BIA])\s*\|(?P<cell>.*?)\|\s*$")


# Which "## group" of the root README a new section block belongs to (SPEC §8.4).
ROOT_GROUP_FOR = {
    "24-ai-ml-foundations": "AI & Machine Learning",
    "25-software-architecture": "Infrastructure & Operations",
    "26-rust": "Core Language & Programming",
}


def _group_end(lines: list[str], group: str) -> int | None:
    """Index just after the last table of `## group` (before its trailing --- / next ## heading), or None."""
    start = next((i for i, l in enumerate(lines) if l.strip() == f"## {group}"), None)
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## ") or lines[j].strip() == "---":
            end = j
            break
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return end


def _blocks(lines: list[str]) -> list[dict]:
    """Every `### [..](folder/)` block with the span of its table: {start, folder, number, tstart, tend}."""
    out = []
    for i, line in enumerate(lines):
        m = _BLOCK_RE.match(line)
        if not m:
            continue
        n = re.match(r"^(\d+)\b", m.group("label"))
        b = {"start": i, "folder": m.group("path").strip("/"), "number": int(n.group(1)) if n else None,
             "tstart": None, "tend": i + 1}
        j = i + 1
        while j < len(lines) and not lines[j].startswith("|") and not re.match(r"^(#|---)", lines[j]):
            j += 1                                      # optional description lines before the table
        if j < len(lines) and lines[j].startswith("|"):
            k = j
            while k < len(lines) and lines[k].startswith("|"):
                k += 1
            b["tstart"], b["tend"] = j, k
        out.append(b)
    return out


def add_root_link(text: str, folder: str, section_title: str, level: str, link_text: str,
                  link_path: str) -> tuple[str, bool]:
    """Add `[link_text](link_path)` to the level row of the section's block in the root README.

    Returns (new text, changed).  Creates the row, or the whole block (after the last numbered block,
    keeping section numbers in order), when missing.
    """
    if f"({link_path})" in text:
        return text, False
    lines = text.splitlines()
    link = f"[{link_text.replace('[', '(').replace(']', ')').replace('|', '/')}]({link_path})"
    blocks = _blocks(lines)
    block = next((b for b in blocks if b["folder"] == folder), None)

    if block is None:
        m = re.match(r"^(\d+)-", folder)
        num = int(m.group(1)) if m else None
        label = f"{m.group(1)} — {section_title}" if m else section_title
        new = ["", f"### [{label}]({folder}/)", ROOT_TABLE_HEADER, ROOT_TABLE_RULE, f"| {level} | {link} |"]
        group = ROOT_GROUP_FOR.get(folder)
        at = _group_end(lines, group) if group else None
        if at is None and group:                        # group heading missing: create it before Domain-Specific
            new = ["", f"## {group}"] + new
            dom = next((i for i, l in enumerate(lines) if l.strip() == "## Domain-Specific"), None)
            at = dom - 1 if dom is not None and dom > 0 and lines[dom - 1].strip() == "---" else (dom if dom is not None else None)
            if at is not None:
                new = new + ["", "---"] if lines[at].strip() == "---" else new
        if at is None:
            numbered = [b for b in blocks if b["number"] is not None]
            before = [b for b in numbered if num is None or b["number"] < num]
            anchor = before[-1] if before else (numbered[-1] if numbered else None)   # last one in file order
            at = anchor["tend"] if anchor else len(lines)
            if not anchor and lines and lines[-1].strip():
                new.insert(0, "")
        lines[at:at] = new
        return "\n".join(lines).rstrip("\n") + "\n", True

    if block["tstart"] is None:                         # block without a table: add one under the heading
        lines[block["start"] + 1:block["start"] + 1] = [ROOT_TABLE_HEADER, ROOT_TABLE_RULE, f"| {level} | {link} |"]
        return "\n".join(lines).rstrip("\n") + "\n", True

    rows = [(i, _ROW_RE.match(lines[i])) for i in range(block["tstart"], block["tend"])]
    rows = [(i, m) for i, m in rows if m]
    for i, m in rows:
        if m.group("lv") == level:                      # extend the existing row
            cell = m.group("cell").strip()
            lines[i] = f"| {level} | {link if cell in DASH_CELLS else cell + ', ' + link} |"
            return "\n".join(lines).rstrip("\n") + "\n", True
    order = common.LEVEL_ORDER
    later = [i for i, m in rows if order.index(m.group("lv")) > order.index(level)]
    at = min(later) if later else block["tend"]
    lines.insert(at, f"| {level} | {link} |")
    return "\n".join(lines).rstrip("\n") + "\n", True


# --------------------------------------------------------------------------- filed copy

def interview_focus(fm: dict, body: str, tracks: dict[str, dict]) -> str:
    """First 2-3 key points of the rung, else the first sentence of 'Why this matters' (~80 chars)."""
    rung = common.rung_lookup(tracks).get(str(fm.get("rung") or ""))
    points = [common.clean_inline_md(str(k)).rstrip(".") for k in ((rung[2].get("key_points") or []) if rung else [])]
    points = [p for p in points if p]
    if points:
        chosen: list[str] = []
        for p in points[:3]:
            if chosen and len(", ".join(chosen + [p])) > FOCUS_TARGET + FOCUS_SLACK:
                break
            chosen.append(p)
        return common.trim_text(", ".join(chosen), FOCUS_TARGET + FOCUS_SLACK)
    why = common.strip_html_comments(common.section_text(body, "Why this matters"))
    why = "\n".join(l for l in why.splitlines() if not l.lstrip().startswith(">"))
    return common.first_sentence(why, FOCUS_TARGET) or common.trim_text(str(fm.get("title") or ""), FOCUS_TARGET)


def passed_on(fm: dict) -> str:
    try:
        if fm.get("marked_at"):
            return common.kyiv_date_of(fm["marked_at"]).isoformat()
    except ValueError:
        pass
    return common.kyiv_today().isoformat()


def track_label(fm: dict, tracks: dict[str, dict]) -> str:
    domain = str(fm.get("domain") or fm.get("track") or "")
    name = str((tracks.get(domain) or {}).get("name") or domain)
    return f"Fresh · {name}" if fm.get("slot") == "fresh" else name


def build_filed_text(fm: dict, body: str, tracks: dict[str, dict]) -> str:
    """Lesson body + the `> Source:` header block; no front matter, no 'Next on this track'."""
    body = common.drop_section(common.strip_html_comments(body), "Next on this track")
    lines = body.lstrip("\n").splitlines()
    header = (f"> Source: IT Iaido lesson {fm['id']} · {track_label(fm, tracks)} · "
              f"{common.level_name(fm.get('level'))} · passed on {passed_on(fm)}")
    if lines and lines[0].startswith("# "):
        title_line, rest = lines[0], lines[1:]
    else:
        title_line, rest = f"# {fm.get('title')}", lines
    while rest and not rest[0].strip():
        rest = rest[1:]
    return "\n".join([title_line, "", header, ""] + rest).rstrip("\n") + "\n"


def _kb_filename(section_dir: Path, slug: str, lesson_id: str) -> str:
    """<slug>.md, unless another lesson already owns that name (then <slug>-<id>.md)."""
    name = f"{slug}.md"
    p = section_dir / name
    if p.exists() and f"IT Iaido lesson {lesson_id} " not in p.read_text(encoding="utf-8")[:600]:
        return f"{slug}-{lesson_id}.md"
    return name


# --------------------------------------------------------------------------- orchestration

def file_lesson(ref: str, by: str = "job") -> dict:
    path = common.find_lesson_path(ref)
    fm, body = common.load_lesson(path)
    lid = str(fm.get("id"))
    status = fm.get("status", "sent")
    if status != "passed":
        raise DojoError(f"lesson {lid} has status {status!r}: only passed lessons are filed")
    existing = fm.get("filed_to")
    if existing and (common.repo_root() / str(existing)).exists():
        return {"id": lid, "filed": False, "reason": "already filed", "filed_to": existing}

    tracks = common.load_curriculum()
    folder = str(fm.get("files_to") or common.track_files_to(tracks, fm.get("domain") or fm.get("track")) or "").strip("/")
    if not folder:
        raise DojoError(f"lesson {lid} has no files_to and its domain has no default section")
    level = str(fm.get("level") or "B").upper()
    if level not in common.LEVELS:
        raise DojoError(f"lesson {lid}: level {level!r} is not B, I or A")

    section_dir = common.repo_root() / folder
    readme = section_dir / "README.md"
    title, description = section_info(folder, tracks)
    created_section = not readme.exists()
    if created_section:
        section_dir.mkdir(parents=True, exist_ok=True)
        common.atomic_write(readme, new_readme_text(title, description))

    filename = _kb_filename(section_dir, common.lesson_slug(path), lid)
    common.atomic_write(section_dir / filename, build_filed_text(fm, body, tracks))
    kb_path = f"{folder}/{filename}"

    focus = interview_focus(fm, body, tracks)
    new_readme, number = add_readme_row(readme.read_text(encoding="utf-8"), level, str(fm["title"]), filename, focus)
    common.atomic_write(readme, new_readme)

    root = common.repo_root() / "README.md"
    root_changed = False
    if root.exists():
        section_title = readme.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip() or title
        new_root, root_changed = add_root_link(root.read_text(encoding="utf-8"), folder, section_title,
                                               level, str(fm["title"]), kb_path)
        if root_changed:
            common.atomic_write(root, new_root)

    fm["filed_to"] = kb_path
    common.save_lesson(path, fm, body)
    common.log_event("filed", lid, by, kb_path)
    return {"id": lid, "filed": True, "filed_to": kb_path, "section": folder, "section_created": created_section,
            "readme_row": number, "level": level, "root_readme_updated": root_changed, "interview_focus": focus}


def unfiled_passed() -> list[str]:
    return [str(x["fm"]["id"]) for x in common.load_all_lessons()
            if x["fm"].get("status") == "passed" and not x["fm"].get("filed_to")]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="File passed lessons into the knowledge base (section folder, README rows, root README).",
        epilog="Examples:\n"
               "  python3 dojo/engine/file_passed.py 2026-10-06-1\n"
               "  python3 dojo/engine/file_passed.py --all-passed-unfiled",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lessons", nargs="*", metavar="LESSON_ID", help="passed lesson id(s) or file path(s)")
    ap.add_argument("--all-passed-unfiled", action="store_true",
                    help="file every passed lesson whose filed_to is still empty")
    ap.add_argument("--by", default="job", choices=["job", "dashboard", "chat"], help="who triggered it (log)")
    args = ap.parse_args(argv)
    ids = list(args.lessons) + (unfiled_passed() if args.all_passed_unfiled else [])
    if not ids:
        if args.all_passed_unfiled:
            print(common.dumps([]))
            return 0
        ap.error("give a lesson id or --all-passed-unfiled")
    results = [file_lesson(i, args.by) for i in ids]
    print(common.dumps(results[0] if len(results) == 1 and not args.all_passed_unfiled else results))
    return 0


if __name__ == "__main__":
    common.run_cli(main)
