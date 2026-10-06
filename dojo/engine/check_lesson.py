#!/usr/bin/env python3
"""check_lesson.py — deterministic quality gate for a written lesson (SPEC §4).

Usage:  python3 dojo/engine/check_lesson.py <lesson-id-or-path> [--strict]

Prints a JSON report {ok, errors, warnings, stats} and exits 0 when ok (1 otherwise).
Checks: front matter parses and carries the required keys; the fixed sections exist in
order; no writer hints (<!-- … -->) remain; 1–2 mermaid blocks; "The idea" has 450–1500
words; Self-check has ≥3 numbered items each with a <details> answer; Sources lists ≥1
http(s) URL with an access date; fresh lessons carry ≥2 blockquote citations; every quoted
blockquote has a citation line (— …, URL); est_min within 15–30.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

SECTIONS = ["Why this matters", "The idea", "Self-check", "Sources"]
EXAMPLE_HEADINGS = ("Worked example", "Lab")
REQUIRED_FM = ["id", "date", "slot", "track", "level", "title", "est_min", "files_to", "status"]


def section_text(body: str, heading: str) -> str:
    m = re.search(rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", body)
    return m.group(1) if m else ""


def words(text: str) -> int:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return len(re.findall(r"\b\w+\b", text))


def check(path: Path, strict: bool = False) -> dict:
    errors, warnings = [], []
    raw = path.read_text(encoding="utf-8")
    try:
        fm, body = common.parse_front_matter(raw)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "errors": [f"front matter does not parse: {exc}"], "warnings": [], "stats": {}}
    for key in REQUIRED_FM:
        if key not in fm or fm[key] in (None, ""):
            errors.append(f"front matter missing {key}")
    est = fm.get("est_min")
    if not isinstance(est, int) or not 15 <= est <= 30:
        errors.append(f"est_min must be an int in 15..30, got {est!r}")

    headings = re.findall(r"(?m)^## (.+?)\s*$", body)
    pos = -1
    for sec in SECTIONS:
        if sec not in headings:
            errors.append(f"missing section '## {sec}'")
            continue
        idx = headings.index(sec)
        if idx < pos:
            errors.append(f"section '## {sec}' is out of order")
        pos = idx
    if not any(h in headings for h in EXAMPLE_HEADINGS):
        errors.append("missing '## Worked example' or '## Lab'")
    if "Next on this track" not in headings and fm.get("slot") == "core":
        warnings.append("core lesson without '## Next on this track'")

    if re.search(r"<!--", body):
        errors.append("writer hints (<!-- … -->) still present")
    if re.search(r"\bTODO\b|\bTBD\b|lorem ipsum", body, re.I):
        errors.append("placeholder text (TODO/TBD/lorem) present")

    mermaid = len(re.findall(r"(?m)^```mermaid\s*$", body))
    if not 1 <= mermaid <= 2:
        errors.append(f"expected 1–2 mermaid blocks, found {mermaid}")

    idea_words = words(section_text(body, "The idea"))
    if idea_words < 450:
        errors.append(f"'The idea' too short: {idea_words} words (min 450)")
    elif idea_words > 1500:
        warnings.append(f"'The idea' long: {idea_words} words (max 1500)")

    sc = section_text(body, "Self-check")
    items = re.findall(r"(?m)^\s*\d+\.\s", sc)
    details = len(re.findall(r"<details", sc))
    if len(items) < 3:
        errors.append(f"Self-check needs ≥3 numbered questions, found {len(items)}")
    if details < min(3, len(items)) :
        errors.append(f"Self-check answers must be in <details>, found {details}")

    src = section_text(body, "Sources")
    urls = re.findall(r"https?://\S+", src)
    if not urls:
        errors.append("Sources lists no URL")
    if urls and not re.search(r"accessed\s+\d{4}-\d{2}-\d{2}", src, re.I):
        errors.append("Sources: every web source needs an 'accessed YYYY-MM-DD' date")

    # Evidence rule (SPEC §4): a quoted blockquote must carry its citation line with a URL;
    # lessons built from the web (anything that is not one of the reader's books) need at
    # least one verbatim quote; fresh lessons need at least two.
    quote_blocks = re.findall(r"(?ms)^>.*?(?=\n[^>]|\Z)", body)
    quoted = [q for q in quote_blocks if re.search(r"[\"“]", q)]
    uncited = [q for q in quoted if not re.search(r"https?://", q)]
    if uncited:
        errors.append(f"{len(uncited)} quoted blockquote(s) without a URL citation line")
    book_tracks = {"ddia", "fp-scala"}
    if fm.get("slot") == "fresh" and len(quoted) < 2:
        errors.append(f"fresh lesson needs ≥2 quoted passages with citations, found {len(quoted)}")
    elif fm.get("slot") == "core" and fm.get("track") not in book_tracks and len(quoted) < 1:
        errors.append("core lesson from web sources needs ≥1 verbatim quoted passage with its citation")
    if fm.get("track") in book_tracks and fm.get("slot") == "core":
        if not re.search(r"\b(ch(apter)?\.?\s*\d+|§|section\s+\d)", body, re.I):
            errors.append("book-based lesson must cite the chapter/section inline (e.g. 'DDIA ch. 3, \"Hash Indexes\"')")

    # Lab rule (SPEC §4): a lab that shows output must explain how to read it and give a verdict.
    lab = section_text(body, "Lab") or section_text(body, "Worked example")
    if re.search(r"(?m)^```(text|console|output)?\s*$", lab) and re.search(r"(?m)^```(python|scala|bash|sh|sql)", lab):
        if not re.search(r"(?mi)^#{3,4} .*reading the output", lab):
            errors.append("Lab shows code output but has no '### Reading the output' section (SPEC §4 Lab rule)")
        if "**Verdict" not in lab:
            errors.append("Lab has no bold **Verdict** after its output (SPEC §4 Lab rule)")
    # Self-contained rule (SPEC §4): no pointing at repo notes instead of explaining.
    body_wo_sources = re.sub(r"(?ms)^## Sources\s*$.*?(?=^## |\Z)", "", body)
    defer = re.search(r"(?i)(repo already has|existing note|already covered in|as covered in|see (the )?(note|section) \d\d|"
                      r"\b\d\d-[a-z-]+/[A-Za-z_-]+\.md)", body_wo_sources)
    if defer:
        errors.append(f"lesson defers to a repo note instead of explaining ('{defer.group(0)}'); restate it (SPEC §4 Self-contained rule)")
    # Book rule (SPEC §4): chapter map + § subheadings for book tracks.
    if fm.get("slot") == "core" and fm.get("track") in book_tracks:
        idea = section_text(body, "The idea")
        if not re.search(r"(?mi)^>\s*Chapter map:", idea):
            errors.append("book lesson: 'The idea' must open with a '> Chapter map: …' line (SPEC §4 Book rule)")
        if len(re.findall(r"(?m)^### .*§\s*\d+\.\d+", idea)) < 1:
            errors.append("book lesson: each '###' in 'The idea' must carry the book's § number (SPEC §4 Book rule)")
    stats = {"idea_words": idea_words, "mermaid_blocks": mermaid, "self_check": len(items),
             "source_urls": len(urls), "quotes": len(quote_blocks), "est_min": est}
    ok = not errors and (not strict or not warnings)
    return {"ok": ok, "errors": errors, "warnings": warnings, "stats": stats}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lesson", help="lesson id (2026-10-06-1) or path to the .md file")
    ap.add_argument("--strict", action="store_true", help="warnings also fail the check")
    args = ap.parse_args(argv)
    path = Path(args.lesson)
    if not path.exists():
        path = common.find_lesson_path(args.lesson)
    report = check(path, strict=args.strict)
    print(common.dumps(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
