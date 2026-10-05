#!/usr/bin/env python3
"""Create a lesson scaffold (SPEC §4) and commit the picker state.

  new_lesson.py core  --date 2026-10-06 --n 1 [--new-day]
  new_lesson.py fresh --date 2026-10-06 --n 2 --title "..." --domain ai-ml --level I --est-min 20 [--primer]

Writes dojo/lessons/YYYY-MM-DD-N-<slug>.md from templates/lesson.md (front matter filled, every
SPEC §4 section present with HTML-comment hints for the writer), then updates state.json
(credits / next_rung or last_fresh_domains, lessons_sent, open list, and the day counter when
--new-day is given) and logs a `sent` event.  Prints the lesson path (relative to the repo root).

Idempotent: if a lesson with the same id (date + N) already exists, nothing is changed and the
existing path is printed (a note goes to stderr).  Run from the repo root.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys

import common
import pick as pick_mod
import state as state_mod
from common import DojoError

PRESENTATION_HINTS = {
    "minimal": "Presentation MINIMAL: one idea, one diagram, one tiny example; plain words; about 600 words.",
    "standard": "Presentation STANDARD: the core idea plus one or two supporting points, one or two diagrams, "
                "a worked example with real numbers or code; about 900 words.",
    "deep": "Presentation DEEP: worked examples, a lab, code and a trade-off discussion (when to use it and "
            "when not); up to 1200 words.",
}
LEVEL_PRESENTATION = {"B": "minimal", "I": "standard", "A": "deep"}


def _c(text: object) -> str:
    """Make text safe inside an HTML comment."""
    return re.sub(r"\s+", " ", str(text or "")).strip().replace("--", "- -")


def _existing(lesson_id: str):
    d = common.lessons_dir()
    hits = [p for p in sorted(d.glob(f"{lesson_id}-*.md")) if common.LESSON_FILE_RE.match(p.name)] if d.exists() else []
    return hits[0] if hits else None


def _next_n(date: dt.date, lessons: list[dict]) -> int:
    used = [int(str(x["fm"]["id"]).rsplit("-", 1)[1]) for x in lessons if str(x["fm"].get("date")) == date.isoformat()]
    return max(used, default=0) + 1


def _next_rung_line(tracks: dict, track_key: str | None, next_idx: int, ended_prefix: str, ladder_name: str) -> str:
    t = tracks.get(track_key or "")
    if t and next_idx < len(t["rungs"]):
        r = t["rungs"][next_idx]
        return (f"{ended_prefix}**{r.get('title', r.get('id'))}** "
                f"(rung {next_idx + 1} of {len(t['rungs'])}, {common.level_name(r.get('level'))}).")
    return f"You have reached the end of the {ladder_name} ladder."


def _sources_block(sources: list[dict], today: str) -> str:
    if not sources:
        return f"- <!-- [Title](url) — what it contributed; accessed {today} -->"
    lines = []
    for s in sources:
        loc = f"; locator: {_c(s['locator'])}" if s.get("locator") else ""
        lines.append(f"- [{s.get('title', s.get('url'))}]({s.get('url')}) — "
                     f"<!-- what it contributed{loc}; accessed {today} -->")
    return "\n".join(lines)


def _finish(fm: dict, ctx: dict, date: dt.date, n: int, state: dict, lessons: list[dict], by: str) -> dict:
    """Write the lesson file and persist state; shared by core and fresh."""
    ctx = dict(ctx)
    ctx["title"] = fm["title"]
    ctx["front_matter"] = common.dump_yaml(fm).rstrip("\n")
    ctx["today"] = date.isoformat()
    template = (common.templates_dir() / "lesson.md").read_text(encoding="utf-8")
    text = common.render_template(template, ctx)
    path = common.lessons_dir() / f"{fm['id']}-{common.slugify(fm['title'])}.md"
    common.atomic_write(path, text)
    state_mod.recount(state)  # reads the lesson files, including the one just written
    state_mod.save_state(state)
    common.log_event("sent", fm["id"], by, f"{fm['slot']} · {fm.get('rung') or fm['domain']}")
    return {"path": common.rel(path), "id": fm["id"], "created": True, "front_matter": fm}


def _prepare(args) -> tuple[dt.date, int, list[dict], dict, dict]:
    date = common.parse_date(args.date) if args.date else common.kyiv_today()
    lessons = common.load_all_lessons()
    n = args.n or _next_n(date, lessons)
    tracks = common.load_curriculum()
    state = state_mod.load_state(tracks)
    return date, n, lessons, tracks, state


def _bump_day(state: dict, new_day: bool, date: dt.date, lessons: list[dict]) -> None:
    """Increment the day counter once per calendar date (only when --new-day is passed)."""
    if new_day and not any(str(x["fm"].get("date")) == date.isoformat() for x in lessons):
        state["day"] = int(state.get("day", 0)) + 1


def create_core(args) -> dict:
    tracks = common.require_curriculum()
    date, n, lessons, _, state = _prepare(args)
    lesson_id = f"{date.isoformat()}-{n}"
    hit = _existing(lesson_id)
    if hit:
        return {"path": common.rel(hit), "id": lesson_id, "created": False}

    index = pick_mod.build_sent_index(lessons)
    pick, credits, nxt = pick_mod.pick_next(tracks, state, index, date)
    rung, track = pick["rung"], tracks[pick["track"]]
    _bump_day(state, args.new_day, date, lessons)
    state["credits"], state["next_rung"] = credits, nxt

    needs = "; ".join(f"{p['title']} ({p['id']})" for p in pick["prereqs"]) or "—"
    if pick["primer_needed"]:
        needs += " [not done yet: primer included]"
    level = pick["level"]
    meta = (f"{pick['track_name']} · {common.level_name(level)} · ~{rung.get('est_min', 20)} min · "
            f"rung {pick['rung_index'] + 1} of {pick['total_rungs']} · needs: {needs}")
    fm = {
        "id": lesson_id, "date": date.isoformat(), "day": state["day"],
        "slot": "core", "track": pick["track"], "domain": pick["track"],
        "rung": rung["id"], "level": level, "title": rung["title"],
        "est_min": rung.get("est_min", 20), "files_to": pick["files_to"],
        "status": "sent", "sent_at": common.now_iso(), "marked_at": None,
        "filed_to": None, "review_due": None,
    }
    if pick["primer_needed"]:
        fm["primer_needed"] = True
    fm["sources"] = [{"title": s.get("title"), "url": s.get("url")} for s in (rung.get("sources") or [])]

    ctx = {
        "core": True, "fresh": False, "primer": pick["primer_needed"],
        "meta_line": meta,
        "rung_id": rung["id"], "summary": _c(rung.get("summary")),
        "key_points_list": "\n".join(f" - {_c(k)}" for k in (rung.get("key_points") or [])),
        "diagram": _c(rung.get("diagram")), "example": _c(rung.get("example")),
        "presentation_hint": PRESENTATION_HINTS.get(rung.get("presentation") or LEVEL_PRESENTATION.get(level, "standard"),
                                                    PRESENTATION_HINTS["standard"]),
        "reader_level_name": common.level_name(pick_mod.reader_level(pick["track"], tracks, lessons)),
        "sources_block": _sources_block(rung.get("sources") or [], date.isoformat()),
        "next_line": _next_rung_line(tracks, pick["track"], pick["rung_index"] + 1,
                                     f"Next on {track.get('name')}: ", track.get("name", pick["track"])),
    }
    return _finish(fm, ctx, date, n, state, lessons, args.by)


def create_fresh(args) -> dict:
    date, n, lessons, tracks, state = _prepare(args)
    lesson_id = f"{date.isoformat()}-{n}"
    hit = _existing(lesson_id)
    if hit:
        return {"path": common.rel(hit), "id": lesson_id, "created": False}

    domain = args.domain
    files_to = args.files_to or common.track_files_to(tracks, domain)
    if not files_to:
        raise DojoError(f"domain {domain!r} has no curriculum track to take a default section from; "
                        "pass --files-to <section-folder>")
    level = args.level.upper()
    track = tracks.get(domain)
    domain_name = track.get("name", domain) if track else domain
    _bump_day(state, args.new_day, date, lessons)
    recent = list(state.get("last_fresh_domains", [])) + [domain]
    state["last_fresh_domains"] = recent[-common.RECENT_FRESH_WINDOW:]

    meta = f"Fresh · {domain_name} · {common.level_name(level)} · ~{args.est_min} min · from today's feeds"
    fm = {
        "id": lesson_id, "date": date.isoformat(), "day": state["day"],
        "slot": "fresh", "track": "fresh", "domain": domain,
        "rung": None, "level": level, "title": args.title,
        "est_min": args.est_min, "files_to": files_to,
        "status": "sent", "sent_at": common.now_iso(), "marked_at": None,
        "filed_to": None, "review_due": None,
    }
    if args.primer:
        fm["primer_needed"] = True
    fm["sources"] = []

    next_idx = state.get("next_rung", {}).get(domain, 0)
    ctx = {
        "core": False, "fresh": True, "primer": bool(args.primer),
        "meta_line": meta,
        "presentation_hint": PRESENTATION_HINTS[LEVEL_PRESENTATION.get(level, "standard")],
        "reader_level_name": common.level_name(pick_mod.reader_level(domain, tracks, lessons)),
        "sources_block": _sources_block([], date.isoformat()),
        "next_line": (_next_rung_line(tracks, domain, next_idx,
                                      f"Fresh lessons sit outside the ladder; next on {domain_name}: ", domain_name)
                      if track else "Fresh lessons sit outside the ladder; your next core lesson arrives tomorrow."),
    }
    return _finish(fm, ctx, date, n, state, lessons, args.by)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Create a lesson scaffold from the picker (core) or from researched facts (fresh).",
        epilog="Examples:\n"
               "  python3 dojo/engine/new_lesson.py core --date 2026-10-06 --n 1 --new-day\n"
               "  python3 dojo/engine/new_lesson.py fresh --date 2026-10-06 --n 2 --title 'KV cache explained' \\\n"
               "      --domain ai-ml --level I --est-min 20 --primer",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="kind", required=True)
    for name in ("core", "fresh"):
        p = sub.add_parser(name, help=f"create a {name} lesson",
                           formatter_class=argparse.RawDescriptionHelpFormatter)
        p.add_argument("--date", metavar="YYYY-MM-DD", help="lesson date (default: today in Kyiv)")
        p.add_argument("--n", type=int, help="slot number: 1,2 daily; 3,4 on demand (default: next free)")
        p.add_argument("--new-day", action="store_true",
                       help="increment the day counter (once per date; pass on the first lesson of a daily run)")
        p.add_argument("--by", default="job", choices=["job", "dashboard", "chat"], help="who triggered it (log)")
        p.add_argument("--json", action="store_true", help="print details as JSON instead of only the path")
        if name == "fresh":
            p.add_argument("--title", required=True)
            p.add_argument("--domain", required=True, help="closest track key, e.g. ai-ml")
            p.add_argument("--level", default="B", choices=["B", "I", "A", "b", "i", "a"])
            p.add_argument("--est-min", type=int, default=20)
            p.add_argument("--files-to", help="KB section folder (default: the domain track's files_to)")
            p.add_argument("--primer", action="store_true", help="add the Primer section (item above reader level)")
    args = ap.parse_args(argv)

    result = create_core(args) if args.kind == "core" else create_fresh(args)
    if not result["created"]:
        print(f"note: lesson {result['id']} already exists; nothing changed", file=sys.stderr)
    print(common.dumps(result) if args.json else result["path"])
    return 0


if __name__ == "__main__":
    common.run_cli(main)
