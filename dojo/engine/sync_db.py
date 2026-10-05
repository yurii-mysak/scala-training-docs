#!/usr/bin/env python3
"""Produce the JSON documents the dashboard database caches (SPEC §7).

  sync_db.py export <lesson-id> [<lesson-id> ...]   -> dojo/out/db/lessons/<id>.json   (or --all)
  sync_db.py tracks                                 -> dojo/out/db/tracks/<track>.json
  sync_db.py meta                                   -> dojo/out/db/meta/state.json
  sync_db.py all                                    -> every lesson + tracks + meta

This script only writes local files; the scheduled job uploads them with its database tool
(collection `lessons`, `tracks`, `meta`).  The repo stays the single source of truth.  Every command
prints a JSON list of {collection, id, path} so the job knows what to upload.  Run from the repo root.

Field notes
  lessons/{id}   md = lesson body without front matter (HTML scaffold comments removed);
                 summary = the rung's curriculum summary, else the lesson's "Why this matters".
  tracks/{key}   total = rungs in the ladder; done = rungs whose lesson is `passed`;
                 next_title / next_level = the next unsent rung (null when the ladder is finished).
  meta/state     streak = consecutive Kyiv days (ending today, or yesterday while today is still open)
                 on which at least one lesson was marked `passed`.
"""
from __future__ import annotations

import argparse
import datetime as dt

import common
import state as state_mod
from common import DojoError


def _db_dir():
    return common.out_dir() / "db"


def _write(collection: str, doc_id: str, doc: dict) -> dict:
    path = _db_dir() / collection / f"{doc_id}.json"
    common.save_json(path, doc)
    return {"collection": collection, "id": doc_id, "path": common.rel(path)}


# --------------------------------------------------------------------------- lessons

def lesson_day(fm: dict, lessons: list[dict]) -> int | None:
    if isinstance(fm.get("day"), int):
        return fm["day"]
    dates = sorted({str(x["fm"].get("date")) for x in lessons})
    d = str(fm.get("date"))
    return dates.index(d) + 1 if d in dates else None


def lesson_doc(entry: dict, tracks: dict[str, dict], lessons: list[dict]) -> dict:
    fm, body = entry["fm"], entry["body"]
    rung = common.rung_lookup(tracks).get(str(fm.get("rung") or ""))
    md = common.strip_html_comments(body)
    if rung and rung[2].get("summary"):
        summary = common.clean_inline_md(str(rung[2]["summary"]))
    else:
        summary = common.trim_text(common.clean_inline_md(common.section_text(md, "Why this matters")), 300)
    track_key = str(fm.get("track") or "")
    track = tracks.get(track_key)
    return {
        "id": str(fm["id"]),
        "date": str(fm.get("date")),
        "slot": fm.get("slot"),
        "track": track_key,
        "track_name": (track or {}).get("name") or ("Fresh" if track_key == "fresh" else track_key),
        "domain": fm.get("domain"),
        "rung": fm.get("rung"),
        "level": fm.get("level"),
        "title": fm.get("title"),
        "est_min": fm.get("est_min"),
        "status": fm.get("status", "sent"),
        "sent_at": fm.get("sent_at"),
        "marked_at": fm.get("marked_at"),
        "summary": summary,
        "md": md,
        "filed_to": fm.get("filed_to"),
        "review_due": fm.get("review_due"),
        "sources": [{"title": s.get("title"), "url": s.get("url")}
                    for s in (fm.get("sources") or []) if isinstance(s, dict)],
        "day": lesson_day(fm, lessons),
    }


def export_lessons(ids: list[str] | None) -> list[dict]:
    """Write lessons/<id>.json for the given ids (None = every lesson)."""
    tracks = common.load_curriculum()
    lessons = common.load_all_lessons()
    by_id = {str(x["fm"]["id"]): x for x in lessons}
    wanted = list(by_id) if ids is None else [str(common.load_lesson(common.find_lesson_path(i))[0].get("id")) for i in ids]
    return [_write("lessons", i, lesson_doc(by_id[i], tracks, lessons)) for i in wanted]


# --------------------------------------------------------------------------- tracks

def track_doc(key: str, track: dict, state: dict, lessons: list[dict]) -> dict:
    rung_ids = {str(r.get("id")) for r in track["rungs"]}
    done = {str(x["fm"].get("rung")) for x in lessons if x["fm"].get("status") == "passed"} & rung_ids
    idx = int(state.get("next_rung", {}).get(key, 0))
    nxt = track["rungs"][idx] if idx < len(track["rungs"]) else None
    return {
        "key": key,
        "name": track.get("name", key),
        "weight": track.get("weight", 1),
        "total": len(track["rungs"]),
        "done": len(done),
        "next_title": nxt.get("title") if nxt else None,
        "next_level": nxt.get("level") if nxt else None,
        "files_to": track.get("files_to"),
    }


def export_tracks() -> list[dict]:
    tracks = common.require_curriculum()
    state = state_mod.load_state(tracks)
    lessons = common.load_all_lessons()
    return [_write("tracks", key, track_doc(key, t, state, lessons)) for key, t in tracks.items()]


# --------------------------------------------------------------------------- meta

def compute_streak(lessons: list[dict], today: dt.date) -> int:
    days = set()
    for x in lessons:
        fm = x["fm"]
        if fm.get("status") == "passed" and fm.get("marked_at"):
            try:
                days.add(common.kyiv_date_of(fm["marked_at"]))
            except ValueError:
                pass
    d = today if today in days else today - dt.timedelta(days=1)
    n = 0
    while d in days:
        n += 1
        d -= dt.timedelta(days=1)
    return n


def last_run_summary(state: dict, lessons: list[dict]) -> str:
    if state.get("last_run_summary"):
        return str(state["last_run_summary"])
    if not lessons:
        return "No lessons sent yet."
    last_date = max(str(x["fm"].get("date")) for x in lessons)
    todays = [x["fm"] for x in lessons if str(x["fm"].get("date")) == last_date]
    titles = "; ".join(str(f.get("title")) for f in todays)
    return f"{last_date}: {len(todays)} lesson{'s' if len(todays) != 1 else ''} sent: {titles}"


def meta_doc() -> dict:
    tracks = common.load_curriculum()
    state = state_mod.load_state(tracks)
    lessons = common.load_all_lessons()
    state_mod.recount(state, lessons)   # lesson files are the truth for the counters
    return {
        "day": state.get("day", 0),
        "lessons_sent": state["lessons_sent"],
        "lessons_passed": state["lessons_passed"],
        "open": state["open"],
        "last_run_at": state.get("last_run_at"),
        "last_run_summary": last_run_summary(state, lessons),
        "trigger_id": state.get("trigger_id"),
        "reminder_trigger_id": state.get("reminder_trigger_id"),
        "repo_url": state.get("repo_url") or common.DEFAULT_REPO_URL,
        "streak": compute_streak(lessons, common.kyiv_today()),
    }


def export_meta() -> list[dict]:
    return [_write("meta", "state", meta_doc())]


# --------------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Write dashboard-database JSON documents (SPEC §7) under dojo/out/db/.",
        epilog="Examples:\n"
               "  python3 dojo/engine/sync_db.py export 2026-10-06-1 2026-10-06-2\n"
               "  python3 dojo/engine/sync_db.py tracks\n"
               "  python3 dojo/engine/sync_db.py meta\n"
               "  python3 dojo/engine/sync_db.py all",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("export", help="lessons/<id>.json for the given lesson ids")
    p.add_argument("ids", nargs="*", metavar="LESSON_ID")
    p.add_argument("--all", action="store_true", help="export every lesson")
    sub.add_parser("tracks", help="tracks/<track>.json for every curriculum track")
    sub.add_parser("meta", help="meta/state.json")
    sub.add_parser("all", help="every lesson, every track and meta")
    args = ap.parse_args(argv)

    if args.cmd == "export":
        if not args.ids and not args.all:
            raise DojoError("give lesson ids or --all")
        written = export_lessons(None if args.all else args.ids)
    elif args.cmd == "tracks":
        written = export_tracks()
    elif args.cmd == "meta":
        written = export_meta()
    else:
        written = export_lessons(None) + export_tracks() + export_meta()
    print(common.dumps(written))
    return 0


if __name__ == "__main__":
    common.run_cli(main)
