#!/usr/bin/env python3
"""Mark a lesson passed / review / skipped / sent (the repo-side half of a dashboard or chat mark).

  mark.py 2026-10-06-1 passed  --by chat
  mark.py 2026-10-06-2 review  --by dashboard --at 2026-10-06T18:30:00Z
  mark.py 2026-10-06-2 sent    --by chat          # undo a mark: the lesson is open again

Updates the lesson front matter (status, marked_at, review_due = +7 days for `review`, else null),
re-derives lessons_sent / lessons_passed / open in state.json from the lesson files, and appends the
event to progress/log.jsonl.  Idempotent: marking a lesson with the status it already has changes
nothing (no log line either).  Filing a passed lesson is a separate step (file_passed.py).
"""
from __future__ import annotations

import argparse
import datetime as dt

import common
import state as state_mod

REVIEW_DAYS = 7


def mark(ref: str, status: str, by: str = "job", at: str | None = None, note: str = "") -> dict:
    path = common.find_lesson_path(ref)
    fm, body = common.load_lesson(path)
    lesson_id = str(fm.get("id"))
    previous = fm.get("status", "sent")
    if previous == status:
        return {"id": lesson_id, "status": status, "previous": previous, "changed": False}

    marked_at = common.iso_z(common.parse_ts(at)) if at else common.now_iso()
    fm["status"] = status
    fm["marked_at"] = marked_at
    if status == "review":
        due = common.kyiv_date_of(marked_at) + dt.timedelta(days=REVIEW_DAYS)
        fm["review_due"] = due.isoformat()
    else:
        fm["review_due"] = None
    common.save_lesson(path, fm, body)

    state = state_mod.load_state()
    state_mod.recount(state)
    state_mod.save_state(state)
    common.log_event(status, lesson_id, by, note or f"was {previous}")
    return {"id": lesson_id, "status": status, "previous": previous, "changed": True,
            "marked_at": marked_at, "review_due": fm["review_due"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Mark a lesson passed, review or skipped.  Run from the repo root.",
        epilog="Example:  python3 dojo/engine/mark.py 2026-10-06-1 passed --by chat")
    ap.add_argument("lesson", help="lesson id (2026-10-06-1) or file path")
    ap.add_argument("status", choices=["passed", "review", "skipped", "sent"],
                    help="`sent` re-opens a lesson (undo)")
    ap.add_argument("--by", default="job", choices=["job", "dashboard", "chat"], help="who marked it (logged)")
    ap.add_argument("--at", metavar="ISO_TS", help="mark time (default: now); the job passes the dashboard's marked_at")
    ap.add_argument("--note", default="", help="free-text note for the log")
    args = ap.parse_args(argv)
    print(common.dumps(mark(args.lesson, args.status, args.by, args.at, args.note)))
    return 0


if __name__ == "__main__":
    common.run_cli(main)
