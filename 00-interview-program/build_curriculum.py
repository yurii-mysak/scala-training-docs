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


LEGACY = [
    ("06-databases-and-distributed-data", "Required", "~6 h",
     "Your strongest existing asset. CAP, linearizability vs serializability, partitioning and rebalancing, "
     "distributed transactions, DynamoDB, Cassandra LSM, event sourcing. Feeds the design rounds directly — "
     "DynamoDB is what Lyft uses for agent state."),
    ("07-messaging-and-streaming", "Required", "~5 h",
     "Kafka fundamentals and advanced, delivery QoS/DLQ/HA, backpressure, high-throughput low-latency systems. "
     "Directly reusable in every design round."),
    ("08-algorithms-and-data-structures", "Required", "~4 h",
     "Foundation for the CoderPad screen. Re-read Sorting/Searching, Trees and Graphs, Traversal, "
     "Recursion and DP, binary heap, hashset/hashmap."),
    ("10-networking", "Recommended", "~2 h",
     "HTTP/TLS, load balancing, reverse proxies. Feeds the Envoy and API-design parts of design rounds."),
    ("12-testing", "Recommended", "~1.5 h",
     "Testing strategy is explicitly probed in Lyft's design round. Skim for vocabulary."),
    ("11-security", "Recommended", "~1.5 h",
     "One Staff report included a cloud-security domain round. A skim, not a deep dive, "
     "unless the recruiter names security."),
    ("03-akka-ecosystem", "Recommended", "~3 h",
     "Do not present as Akka knowledge. Re-read cluster, streams and backpressure as transferable "
     "distributed-systems concepts: actor-per-conversation maps onto agent session state, supervision onto escalation."),
    ("05-jvm-internals", "Optional", "~0 h",
     "Deep and excellent, but Lyft runs Python and Go. Relevant only if an interviewer asks about your background."),
    ("13-data-engineering", "Optional", "~0 h",
     "Lakehouse/Delta/Parquet. Relevant only to Lyft's data-platform org, which is not this team."),
    ("01-scala-language", "Optional", "~0 h",
     "Skip for this loop. Retain for LotusFlare and for the fallback plan."),
    ("02-functional-programming", "Optional", "~0 h", "Skip for this loop."),
    ("04-concurrency-and-async", "Optional", "~0.5 h",
     "Concepts transfer, syntax does not. Skim only the Cats Effect concurrency file for vocabulary."),
    ("16-adtech", "Optional", "~0 h", "Not relevant to Lyft. Skip."),
]


def render(rows) -> str:
    L = []
    total = sum(minutes(r["time"]) for r in rows)
    required = sum(minutes(r["time"]) for r in rows if r["priority"] == "Required")
    L.append("# Curriculum — every item, tagged\n")
    L.append("> **Priority:** Required")
    L.append("> **Est. time:** 15 min to read")
    L.append("> **Track:** Both")
    L.append("> **HelloInterview:** none\n")
    L.append("Part 1 is generated from the front-matter of every file in this repo. Regenerate with")
    L.append("`python3 00-interview-program/build_curriculum.py`. Part 2 is hand-maintained inside that script.\n")
    L.append("**Priority means:** *Required* — you cannot pass this loop without it. *Recommended* — materially")
    L.append("raises the odds. *Optional* — nice to have, or only relevant if the role turns out to include Web.\n")
    L.append(f"**New material:** {len(rows)} documents. Required only \u2248 {required // 60} h {required % 60} m. "
             f"Everything \u2248 {total // 60} h {total % 60} m.")
    L.append("Existing repo material adds roughly 24 h more if you work all of it; see part 2.\n")
    L.append("---\n")
    L.append("## Part 1 — new material written for this loop\n")
    for sec in sorted(SECTION_NAMES):
        items = [r for r in rows if r["section"] == sec]
        if not items:
            continue
        items.sort(key=lambda r: (ORDER.get(r["priority"], 3), r["path"]))
        st = sum(minutes(r["time"]) for r in items)
        L.append(f"### {SECTION_NAMES[sec]}")
        L.append(f"*{len(items)} documents \u00b7 \u2248{st // 60} h {st % 60} m*\n")
        L.append("| \u2713 | Priority | Time | Track | Document |")
        L.append("|---|---|---|---|---|")
        for r in items:
            name = r["path"].split("/", 1)[1]
            L.append(f"| [ ] | **{r['priority']}** | {r['time']} | {r['track']} | [{r['title']}](../{r['path']}) |")
        L.append("")
    L.append("---\n")
    L.append("## Part 2 — existing repo material, re-tagged for this loop\n")
    L.append("The 186 documents already in this repo were written for Scala interviews. Most still earn their")
    L.append("place; some do not. Section-level guidance rather than per-file, because the judgement is the same")
    L.append("across each section.\n")
    L.append("| \u2713 | Priority | Time | Section | Why |")
    L.append("|---|---|---|---|---|")
    for s, p, t, why in LEGACY:
        L.append(f"| [ ] | **{p}** | {t} | [{s}](../{s}/) | {why} |")
    L.append("")
    L.append("---\n")
    L.append("## Interview questions\n")
    L.append("This file is an index, not a topic. See [interview-playbook.md](interview-playbook.md) for how")
    L.append("each round runs and [evidence.md](evidence.md) for the reported question bank.")
    return "\n".join(L) + "\n"


def main() -> int:
    rows = collect(".")
    if not rows:
        print("no front-matter found; run from the repo root", file=sys.stderr)
        return 1
    out = os.path.join("00-interview-program", "curriculum.md")
    open(out, "w", encoding="utf-8").write(render(rows))
    total = sum(minutes(r["time"]) for r in rows)
    required = sum(minutes(r["time"]) for r in rows if r["priority"] == "Required")
    print(f"wrote {out}")
    print(f"{len(rows)} tagged documents")
    print(f"required: {required // 60}h {required % 60}m")
    print(f"total:    {total // 60}h {total % 60}m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
