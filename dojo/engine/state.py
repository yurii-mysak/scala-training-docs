#!/usr/bin/env python3
"""Picker/progress state: dojo/progress/state.json (SPEC §5).

Library use:  load_state(tracks) -> dict, save_state(state), ensure_tracks(), recount().
CLI:          python3 dojo/engine/state.py show|init|set|touch|log ...   (run from the repo root)

Unknown keys in state.json are always preserved.
"""
from __future__ import annotations

import argparse
import json
import sys

import common
from common import DojoError

SCHEMA = 1


def default_state() -> dict:
    return {
        "schema": SCHEMA,
        "day": 0,
        "credits": {},
        "next_rung": {},
        "lessons_sent": 0,
        "lessons_passed": 0,
        "open": [],
        "last_run_at": None,
        "last_fresh_domains": [],
        "trigger_id": None,
        "reminder_trigger_id": None,
        "dashboard_url": None,
    }


def ensure_tracks(state: dict, tracks: dict[str, dict]) -> dict:
    """Make sure every curriculum track has a credit and a next_rung entry."""
    credits = state.setdefault("credits", {})
    next_rung = state.setdefault("next_rung", {})
    for key in tracks:
        credits.setdefault(key, 0)
        next_rung.setdefault(key, 0)
    return state


def load_state(tracks: dict[str, dict] | None = None) -> dict:
    """Read state.json (or defaults when absent) and top up missing keys.  Does not write."""
    raw = common.load_json(common.state_path(), default=None)
    state = default_state()
    if raw is not None:
        if not isinstance(raw, dict):
            raise DojoError("dojo/progress/state.json must be a JSON object")
        state.update(raw)  # unknown keys survive
    if tracks is None:
        tracks = common.load_curriculum()
    return ensure_tracks(state, tracks)


def save_state(state: dict) -> None:
    common.save_json(common.state_path(), state)


def recount(state: dict, lessons: list[dict] | None = None) -> dict:
    """Derive lessons_sent / lessons_passed / open from the lesson files (the source of truth)."""
    if lessons is None:
        lessons = common.load_all_lessons()
    state["lessons_sent"] = len(lessons)
    state["lessons_passed"] = sum(1 for x in lessons if x["fm"].get("status") == "passed")
    state["open"] = [x["fm"]["id"] for x in lessons if x["fm"].get("status", "sent") == "sent"]
    return state


# --------------------------------------------------------------------------- CLI

def _coerce(value: str):
    """'null' / numbers / JSON literals become typed values, anything else stays a string."""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Inspect and edit dojo/progress/state.json and the event log.",
        epilog="Examples:\n"
               "  state.py show\n"
               "  state.py init\n"
               "  state.py set dashboard_url https://claude.ai/artifact/...\n"
               "  state.py touch                      # last_run_at = now\n"
               "  state.py log reminded --by job --note 'open: 2026-10-06-1'",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show", help="print the current state as JSON (does not write)")
    sub.add_parser("init", help="create state.json if missing / add new curriculum tracks, then recount")
    p_set = sub.add_parser("set", help="set a top-level key (value parsed as JSON, else string)")
    p_set.add_argument("key")
    p_set.add_argument("value")
    sub.add_parser("touch", help="set last_run_at to now")
    p_log = sub.add_parser("log", help="append an event to progress/log.jsonl")
    p_log.add_argument("event", help="sent|passed|review|skipped|filed|requested|reminded")
    p_log.add_argument("--lesson", default=None)
    p_log.add_argument("--by", default="job", choices=["job", "dashboard", "chat"])
    p_log.add_argument("--note", default="")
    args = ap.parse_args(argv)

    if args.cmd == "show":
        print(common.dumps(load_state()))
        return 0
    if args.cmd == "log":
        print(common.dumps(common.log_event(args.event, args.lesson, args.by, args.note)))
        return 0

    state = load_state()
    if args.cmd == "init":
        recount(state)
    elif args.cmd == "set":
        state[args.key] = _coerce(args.value)
    elif args.cmd == "touch":
        state["last_run_at"] = common.now_iso()
    save_state(state)
    print(common.dumps(state))
    return 0


if __name__ == "__main__":
    common.run_cli(main)
