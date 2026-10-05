#!/usr/bin/env python3
"""Pick today's lessons (SPEC §6).

  pick.py core [--commit]      next core rung as JSON (smooth weighted round-robin + prerequisites)
  pick.py fresh                target domain for the fresh slot as JSON
  pick.py --dry-run 16         table of the next 16 core picks; never mutates state

`core` only prints unless --commit is given (new_lesson.py commits for you after writing the file).
Run from the repo root.  Deterministic: no randomness anywhere.

Prerequisite rule (SPEC §6.2): a prerequisite rung is satisfied when its lesson is `passed` or
`skipped`, or was sent two or more (Kyiv) days ago.  If every candidate track is blocked, the
highest-credit track is taken anyway and the pick carries `primer_needed: true`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from typing import Any

import common
import state as state_mod
from common import DojoError

PREREQ_GRACE_DAYS = 2


# --------------------------------------------------------------------------- lesson index

def sent_date(fm: dict) -> dt.date | None:
    """Kyiv date the lesson was sent (sent_at, falling back to the `date` field)."""
    try:
        if fm.get("sent_at"):
            return common.kyiv_date_of(fm["sent_at"])
        if fm.get("date"):
            return common.parse_date(fm["date"])
    except ValueError:
        pass
    return None


def build_sent_index(lessons: list[dict]) -> dict[str, list[dict]]:
    """rung id -> [{'status', 'sent_date'}] built from the lesson files' front matter."""
    index: dict[str, list[dict]] = {}
    for x in lessons:
        fm = x["fm"]
        if fm.get("rung"):
            index.setdefault(str(fm["rung"]), []).append(
                {"status": fm.get("status", "sent"), "sent_date": sent_date(fm)})
    return index


def prereq_ok(rung_id: str, index: dict[str, list[dict]], today: dt.date) -> bool:
    for e in index.get(str(rung_id), []):
        if e["status"] in ("passed", "skipped"):
            return True
        d = e["sent_date"]
        if d is not None and (today - d).days >= PREREQ_GRACE_DAYS:
            return True
    return False


# --------------------------------------------------------------------------- core picker

class Exhausted(DojoError):
    """Every track has been fully sent."""


def _weight(track: dict) -> float:
    return track.get("weight", 1)


def pick_next(tracks: dict[str, dict], state: dict, index: dict[str, list[dict]],
              today: dt.date) -> tuple[dict, dict[str, float], dict[str, int]]:
    """One smooth-weighted-round-robin step.  Pure: returns (pick, new_credits, new_next_rung)."""
    credits = dict(state.get("credits", {}))
    next_rung = dict(state.get("next_rung", {}))
    order = list(tracks)
    active = [k for k in order
              if _weight(tracks[k]) > 0 and next_rung.get(k, 0) < len(tracks[k]["rungs"])]
    if not active:
        raise Exhausted("every track is complete (or has weight 0): nothing left to pick")

    total = sum(_weight(tracks[k]) for k in active)
    for k in active:                                   # 1. credits += weight
        credits[k] = credits.get(k, 0) + _weight(tracks[k])

    ranked = sorted(active, key=lambda k: (-credits[k], -_weight(tracks[k]), order.index(k)))
    chosen, primer = None, False
    for k in ranked:                                   # 2. best credit with satisfied prerequisites
        rung = tracks[k]["rungs"][next_rung.get(k, 0)]
        if all(prereq_ok(p, index, today) for p in (rung.get("prereqs") or [])):
            chosen = k
            break
    if chosen is None:                                 # 4. everything blocked: take the best anyway
        chosen, primer = ranked[0], True

    credits[chosen] -= total                           # 3. pay for the pick
    idx = next_rung.get(chosen, 0)
    next_rung[chosen] = idx + 1

    track = tracks[chosen]
    rung = track["rungs"][idx]
    lookup = {r.get("id"): r for t in tracks.values() for r in t["rungs"]}
    prereqs = [{"id": p, "title": (lookup.get(p) or {}).get("title", p),
                "satisfied": prereq_ok(p, index, today)} for p in (rung.get("prereqs") or [])]
    pick = {
        "track": chosen,
        "track_name": track.get("name", chosen),
        "rung": rung,
        "rung_index": idx,
        "total_rungs": len(track["rungs"]),
        "primer_needed": primer,
        "level": rung.get("level", "B"),
        "files_to": rung.get("files_to") or track.get("files_to"),
        "weight": _weight(track),
        "prereqs": prereqs,
    }
    return pick, credits, next_rung


def simulate(tracks: dict[str, dict], state: dict, index: dict[str, list[dict]],
             today: dt.date, n: int) -> list[dict]:
    """The next n core picks, one per day starting today, without touching real state.

    Each simulated pick counts as sent on its day, so cross-track prerequisites behave as they
    would for a reader who marks nothing.
    """
    st = {"credits": dict(state.get("credits", {})), "next_rung": dict(state.get("next_rung", {}))}
    idx = {k: list(v) for k, v in index.items()}
    picks = []
    for i in range(n):
        day = today + dt.timedelta(days=i)
        try:
            pick, st["credits"], st["next_rung"] = pick_next(tracks, st, idx, day)
        except Exhausted:
            break
        idx.setdefault(str(pick["rung"]["id"]), []).append({"status": "sent", "sent_date": day})
        pick["date"] = day.isoformat()
        picks.append(pick)
    return picks


def pick_core(commit: bool = False, today: dt.date | None = None) -> dict:
    tracks = common.require_curriculum()
    state = state_mod.load_state(tracks)
    index = build_sent_index(common.load_all_lessons())
    pick, credits, nxt = pick_next(tracks, state, index, today or common.kyiv_today())
    if commit:
        state["credits"], state["next_rung"] = credits, nxt
        state_mod.save_state(state)
    return pick


# --------------------------------------------------------------------------- fresh slot

_SHARE_KEYS = ("domain_shares", "domain_mix", "shares", "domains", "mix")


def _find_share_block(feeds: Any) -> Any:
    if not isinstance(feeds, dict):
        return None
    for k in _SHARE_KEYS:
        if k in feeds:
            return feeds[k]
    for v in feeds.values():          # one level of nesting, e.g. `fresh: {domain_mix: ...}`
        if isinstance(v, dict):
            for k in _SHARE_KEYS:
                if k in v:
                    return v[k]
    return None


def load_shares(tracks: dict[str, dict]) -> dict[str, float]:
    """Domain shares for the fresh slot, normalised to sum 1.

    Read from dojo/feeds.yaml `domain_shares` (a mapping domain -> share, or a list of {domain, share};
    `domain_mix` / `shares` are accepted as aliases).  When feeds.yaml is missing or has no such block,
    every curriculum track gets an equal share.
    """
    raw = None
    if common.feeds_path().exists():
        raw = _find_share_block(common.load_yaml(common.feeds_path()))
    shares: dict[str, float] = {}

    def add(domain: Any, value: Any) -> None:
        if isinstance(value, dict):
            value = value.get("share", value.get("weight", value.get("pct")))
        if domain is not None and isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
            shares[str(domain)] = float(value)

    if isinstance(raw, dict):
        for d, v in raw.items():
            add(d, v)
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                add(item.get("domain") or item.get("key") or item.get("track"),
                    item.get("share", item.get("weight", item.get("pct"))))
    if not shares:
        for k in tracks:
            add(k, 1)
    total = sum(shares.values())
    return {d: v / total for d, v in shares.items()} if total else {}


def reader_level(domain: str, tracks: dict[str, dict], lessons: list[dict]) -> str:
    """Level of the furthest passed rung of the track matching `domain` (B when none)."""
    track = tracks.get(domain)
    if not track:
        return "B"
    pos = {r.get("id"): i for i, r in enumerate(track["rungs"])}
    best, level = -1, "B"
    for x in lessons:
        fm = x["fm"]
        if fm.get("status") == "passed" and fm.get("rung") in pos and pos[fm["rung"]] > best:
            best = pos[fm["rung"]]
            level = track["rungs"][best].get("level", fm.get("level", "B"))
    return level


def pick_fresh(today: dt.date | None = None) -> dict:
    tracks = common.load_curriculum()
    state = state_mod.load_state(tracks)
    shares = load_shares(tracks)
    if not shares:
        raise DojoError("no domain shares: add `domain_shares` to dojo/feeds.yaml or create curriculum files")
    recent = [str(d) for d in state.get("last_fresh_domains", [])][-common.RECENT_FRESH_WINDOW:]
    n = len(recent)

    def deficit(d: str) -> float:   # how far below its share the domain is, counting today's slot
        return shares[d] * (n + 1) - recent.count(d)

    domain = sorted(shares, key=lambda d: (-round(deficit(d), 9), -shares[d], common.track_sort_key(d)))[0]
    track = tracks.get(domain)
    return {
        "domain": domain,
        "reader_level": reader_level(domain, tracks, common.load_all_lessons()),
        "shares": {d: round(v, 4) for d, v in shares.items()},
        "recent": recent,
        "track_name": track.get("name", domain) if track else domain,
        "files_to": track.get("files_to") if track else None,
    }


# --------------------------------------------------------------------------- CLI

def _dry_run_table(picks: list[dict]) -> str:
    rows = [("#", "date", "track", "rung", "lvl", "title")]
    for i, p in enumerate(picks, start=1):
        title = p["rung"].get("title", "")
        if p["primer_needed"]:
            title += "  [primer needed]"
        rows.append((str(i), p["date"], p["track"], str(p["rung"].get("id")), p["level"], title))
    widths = [max(len(r[c]) for r in rows) for c in range(5)]
    lines = ["  ".join(r[c].ljust(widths[c]) for c in range(5)) + "  " + r[5] for r in rows]
    counts: dict[str, int] = {}
    for p in picks:
        counts[p["track"]] = counts.get(p["track"], 0) + 1
    lines.insert(1, "  ".join("-" * w for w in widths) + "  -----")
    lines.append("")
    lines.append("counts: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Pick the next core rung / fresh domain.  Run from the repo root.",
        epilog="Examples:\n"
               "  python3 dojo/engine/pick.py core                 # print today's core pick (no state change)\n"
               "  python3 dojo/engine/pick.py core --commit        # ...and advance credits/next_rung\n"
               "  python3 dojo/engine/pick.py fresh                # target domain + reader level for slot 2\n"
               "  python3 dojo/engine/pick.py --dry-run 16         # eyeball the next 16 core picks",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", nargs="?", choices=["core", "fresh"], help="which slot to pick for")
    ap.add_argument("--dry-run", type=int, metavar="N", help="print the next N core picks as a table; no mutation")
    ap.add_argument("--commit", action="store_true", help="(core) persist credits and next_rung after printing")
    ap.add_argument("--today", metavar="YYYY-MM-DD", help="override today's Kyiv date (prerequisite check)")
    ap.add_argument("--json", action="store_true", help="(--dry-run) emit JSON instead of a table")
    args = ap.parse_args(argv)

    today = common.parse_date(args.today) if args.today else common.kyiv_today()

    if args.dry_run is not None:
        if args.mode == "fresh":
            raise DojoError("--dry-run applies to core picks only")
        tracks = common.require_curriculum()
        state = state_mod.load_state(tracks)
        index = build_sent_index(common.load_all_lessons())
        picks = simulate(tracks, state, index, today, args.dry_run)
        if args.json:
            print(common.dumps(picks))
        else:
            print(_dry_run_table(picks))
        return 0

    if args.mode == "core":
        print(common.dumps(pick_core(commit=args.commit, today=today)))
        return 0
    if args.mode == "fresh":
        if args.commit:
            raise DojoError("fresh picks are committed by new_lesson.py fresh, not by pick.py")
        print(common.dumps(pick_fresh(today)))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    common.run_cli(main)
