#!/usr/bin/env python3
"""Regenerate curriculum.md from the front-matter of every markdown file in the repo.

Run from the repo root:  python3 00-interview-program/build_curriculum.py
Standard library only. Front-matter format expected directly under the H1:

    > **Priority:** Required | Recommended | Optional
    > **Est. time:** 45 min
    > **Track:** Server | Server + Web | Both
    > **HelloInterview:** <lesson path or "none">
"""
import os
import re
import sys

SKIP_DIRS = {".git", "__pycache__", ".claude", "node_modules"}
ORDER = {"Required": 0, "Recommended": 1, "Optional": 2}

SECTION_NAMES = {
    "09-coding-challenges": "09 — Coding challenges (Lyft-evidence set)",
    "14-cloud-and-infrastructure": "14 — Cloud, containers & Kubernetes",
    "15-system-design": "15 — System design",
    "17-lyft-laptop-round": "17 — The Lyft laptop round",
    "18-io-harness": "18 — I/O harness (runnable project)",
    "19-observability-and-oncall": "19 — Observability & on-call",
    "20-llm-agent-systems": "20 — LLM & agent systems",
    "21-python-for-interviews": "21 — Python for interviews",
    "22-behavioral-and-staff-scope": "22 — Behavioural & Staff scope",
    "23-web-and-frontend": "23 — Web & frontend (conditional track)",
}


def field(text: str, label: str) -> str:
    m = re.search(r"\*\*" + label + r":\*\*\s*([^\n]+)", text)
    return m.group(1).strip() if m else ""


def minutes(value: str) -> int:
    m = re.search(r"(\d+)", value or "")
    return int(m.group(1)) if m else 0


def collect(root: str = "."):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            if not name.endswith(".md"):
                continue
            path = os.path.relpath(os.path.join(dirpath, name), root)
            try:
                head = open(os.path.join(root, path), encoding="utf-8").read(2500)
            except OSError:
                continue
            priority = field(head, "Priority")
            if not priority:
                continue
            h1 = re.search(r"^#\s+(.+)$", head, re.M)
            out.append({
                "path": path.replace(os.sep, "/"),
                "section": path.replace(os.sep, "/").split("/")[0],
                "title": h1.group(1).strip() if h1 else name,
                "priority": priority.split("|")[0].strip(),
                "time": field(head, "Est. time"),
                "track": field(head, "Track"),
            })
    return out


def main() -> int:
    rows = collect(".")
    if not rows:
        print("no front-matter found; run from the repo root", file=sys.stderr)
        return 1
    total = sum(minutes(r["time"]) for r in rows)
    required = sum(minutes(r["time"]) for r in rows if r["priority"] == "Required")
    print(f"{len(rows)} tagged documents")
    print(f"required: {required // 60}h {required % 60}m")
    print(f"total:    {total // 60}h {total % 60}m")
    print("\nNote: curriculum.md part 2 (legacy sections) is hand-maintained;")
    print("this script reports part 1 only. Edit curriculum.md directly for part 2.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
