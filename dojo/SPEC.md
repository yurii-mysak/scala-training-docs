# IT Iaido — system contract (SPEC)

This file is the contract between every part of the daily-learning system: the curriculum
files, the engine scripts, the dashboard, and the scheduled job (RUNBOOK.md). Change it
deliberately; everything else follows it.

## 1. Purpose and hard requirements

- Two lessons a day, each 15–30 minutes of reading plus a small example or lab.
- Slot 1 (`core`) comes from the curated curriculum in `dojo/curriculum/`.
  Slot 2 (`fresh`) is researched the same morning from the feeds in `dojo/feeds.yaml`.
- Every track is an ordered ladder from basics (B) to advanced (A). A rung is never skipped;
  prerequisites are respected across tracks.
- Priorities (weight per cycle of 18 core lessons): ai-ml 5 · fp-scala 3 · ddia 3 ·
  claude-academy 2 · architecture 2 · networking 2 · rust 1. AI/ML (with Claude Academy) is the
  top priority; Rust is a trickle.
- Presentation also ramps: early rungs = one idea, one diagram, one tiny example; later rungs =
  worked examples, labs, code, trade-off discussion.
- Only lessons marked `passed` are filed into the knowledge base (the numbered sections of this
  repo), categorised into the right section with README rows added.
- Everything is trackable: every lesson ever sent is a file under `dojo/lessons/`, every
  status change is a line in `dojo/progress/log.jsonl`, and the dashboard shows the same.
- On demand: two more lessons can be requested, but only when no sent lesson is still open.
- Delivery by 09:00 Europe/Kyiv daily: a push notification to the Claude app (phone + Mac) that
  names the two lessons; the lessons themselves are read on the Dojo dashboard (and live in the
  repo). No email. The task is scheduled at 08:52 because on-the-hour runs queue behind
  everyone else's. Reminder 20:00 Europe/Kyiv, push only, only if lessons are still open.
- One repo. This repository is the single source of truth. The dashboard database is a cache.

## 2. Repository layout

```
dojo/
  SPEC.md                 this contract
  RUNBOOK.md              what the scheduled job does, step by step (its prompt points here)
  curriculum/
    ai-ml.yaml  claude-academy.yaml  fp-scala.yaml  ddia.yaml  architecture.yaml  networking.yaml  rust.yaml
  feeds.yaml              fresh-slot sources, domain mix, research protocol parameters
  progress/
    state.json            picker state (credits, next rung per track, counters)
    log.jsonl             append-only event log (one JSON object per line)
  lessons/
    YYYY-MM-DD-N-<slug>.md          every lesson ever sent (N = 1,2 daily; 3,4 on demand)
    assets/YYYY-MM-DD-N-<k>.png     rendered diagrams (k = 1..)
  engine/
    pick.py  render_email.py  file_passed.py  state.py  mermaid.py  common.py
    templates/lesson.md  templates/email.html
    tests/
  dashboard/
    dojo.html             source of the published Dojo artifact
```

Knowledge-base sections used for filing (existing + three new):
`24-ai-ml-foundations/`, `25-software-architecture/`, `26-rust/` are created by the engine on
first filing, with a README.md in the same format as the other sections.

## 3. Curriculum YAML schema (`dojo/curriculum/<track>.yaml`)

```yaml
track: ai-ml                    # key = file stem; any number of tracks
name: AI / ML foundations       # display name
weight: 5                       # core lessons per cycle (cycle = sum of weights)
files_to: 24-ai-ml-foundations  # default KB section for passed lessons of this track
description: one or two sentences on what the ladder covers and the order logic
primary_sources:                # the books/courses the ladder is built from
  - title: ...
    url: ...
rungs:                          # ORDERED. Index 0 is the first lesson of the track.
  - id: ai-ml-01                # <track>-NN, two digits, sequential
    title: What machine learning actually optimises
    level: B                    # B | I | A ; non-decreasing along the ladder
    est_min: 20                 # 15..30
    prereqs: []                 # rung ids, this track or another (e.g. fp-scala-03)
    summary: >-                 # 2–4 sentences: what the lesson teaches and why now
      ...
    key_points:                 # 3–6 bullets the lesson must cover
      - ...
    diagram: >-                 # what the one diagram shows (the writer draws it in Mermaid)
      ...
    example: >-                 # the worked example or 5–10 min lab
      ...
    presentation: minimal       # minimal | standard | deep (how rich the lesson should be)
    sources:                    # the writer must use and cite these; may add more
      - title: ...
        url: ...
        locator: ch. 3, "Hash Indexes"   # chapter / section / lecture / timestamp when known
        kind: book | course | video | docs | blog | paper | news
    files_to: 24-ai-ml-foundations   # optional override of the track default
```

Rules: 15 ≤ est_min ≤ 30. Level never goes down along the ladder. Every rung has ≥ 1 source
with a real URL. `presentation` starts `minimal` for the first B rungs and grows.

## 4. Lesson file (`dojo/lessons/YYYY-MM-DD-N-<slug>.md`)

YAML front matter then fixed sections, in this order:

```yaml
---
id: 2026-10-06-1
date: 2026-10-06
slot: core                       # core | fresh
track: ai-ml                     # for fresh: fresh
domain: ai-ml                    # for fresh lessons: the closest track key
rung: ai-ml-01                   # fresh lessons: null
level: B
title: What machine learning actually optimises
est_min: 20
files_to: 24-ai-ml-foundations
status: sent                     # sent | passed | review | skipped
sent_at: 2026-10-06T06:00:00Z
marked_at: null
filed_to: null                   # path in KB once filed
review_due: null                 # date, set when status = review
sources:
  - title: ...
    url: ...
---
# <title>

> Track · Level · ~20 min · rung 1 of 31 · needs: —

## Why this matters
## The idea
(600–1200 words. Exactly one or two ```mermaid blocks. Subheadings allowed.)
## Worked example
(or "## Lab" — 5–10 minutes, concrete, copy-pasteable)
## Self-check
1. Q … <details><summary>Answer</summary>…</details>
2. …
3. …
## Sources
- [Title](url) — Author/Org, date — what it contributed (accessed YYYY-MM-DD)
- Book title, edition — ch. N "Chapter name", §"Section" — what it contributed
## Next on this track
One sentence naming the next rung.
```

Fresh lessons add a `## Primer` section right after "Why this matters" when the item sits
above the reader's current level in that domain.

### Lab rule (hard requirement, every lesson with code or numbers)

The reader must be able to follow the lab from input to verdict without reverse-engineering it:
1. **The question first** — one sentence saying what the lab will decide or show.
2. **Steps** — `### Step 1 …`, `### Step 2 …` headings; the code prints intermediate values
   (per-row predictions, per-step state), not only the final aggregates.
3. **`### Reading the output`** — required whenever the lab shows output: what each column or
   number means and which direction is better; the output reproduced (tables preferred); the
   arithmetic traced for at least one case, digits shown; a bold **Verdict** after each block.
4. **Cause → consequence** — a short numbered chain: cause, mechanism, consequence, what it
   means in practice for the reader's work.
5. The writer runs the code and pastes the real output; numbers in the text must match it.
`engine/check_lesson.py` rejects a lab that shows output without a `Reading the output`
section or without a **Verdict**.

### Evidence rule (hard requirement, every lesson)

The reader must be able to check every claim he decides to follow up on. Anything that is not
from his own books or the links he supplied needs a source, a verbatim quote and a citation:

- A claim taken from a book or course the reader owns or a page the reader can open is cited
  inline in the text: `(Kleppmann, DDIA ch. 3, "Hash Indexes")`, `(RFC 9000 §7.2)`,
  `(3Blue1Brown, "But what is a neural network?", 4:10)`. Chapter, section or timestamp,
  not just the title.
- A claim that is NOT from one of those (a blog post, a paper, a release note, a talk, news)
  must be backed by a **verbatim quote** of 1–3 sentences from the source, in a blockquote,
  with the citation right under it: `> "…" — Author or organisation, *Title*, date, URL`.
  The writer fetches the page and copies the quote; it never paraphrases a quote as if it
  were verbatim and never invents one.
- The `## Sources` list carries every URL used, each with one line on what it contributed and
  the date accessed. Links are verified (fetched) before the lesson is sent; a link that fails
  is replaced or the claim is dropped.
- Fresh-slot lessons are built from sources, so they always contain at least two quoted
  passages; if the writer cannot quote the primary source (paywall, PDF the fetcher cannot
  read), it says so and quotes a secondary source instead.
- Numbers, benchmarks and dates always carry their citation in the same sentence.
- Core lessons whose sources are web pages or courses (every track except DDIA and FP in
  Scala) carry at least one such quoted passage; book-based lessons cite chapter and section
  inline. `engine/check_lesson.py` enforces these rules; a lesson with an unverifiable claim
  does not ship — the claim is rewritten or dropped.

## 5. Progress state and log

`dojo/progress/state.json`
```json
{
  "schema": 1,
  "day": 12,                               // lesson day counter (increments per daily run)
  "credits": {"ai-ml": 0, "fp-scala": 0, ...},   // smooth weighted round-robin credits
  "next_rung": {"ai-ml": 4, "fp-scala": 2, ...}, // index into rungs[] of the next unsent rung
  "lessons_sent": 24, "lessons_passed": 20, "open": ["2026-10-17-1"],
  "last_run_at": "2026-10-17T06:01:00Z",
  "last_fresh_domains": ["ai-ml", "architecture", "networking"],  // last 8 fresh domains
  "trigger_id": "trig_...", "reminder_trigger_id": "trig_...",
  "dashboard_url": "https://claude.ai/artifact/..."
}
```

`dojo/progress/log.jsonl` — one object per line, append-only:
`{"ts": "...", "event": "sent|passed|review|skipped|filed|requested|reminded", "lesson": "2026-10-06-1", "by": "job|dashboard|chat", "note": "..."}`

## 6. Picker algorithm (`engine/pick.py`)

Smooth weighted round-robin (nginx style), deterministic:
1. For every track with remaining rungs: `credits[t] += weight[t]`.
2. Candidate = track with the highest credit whose next rung has all prerequisites satisfied
   (a prerequisite is satisfied when its lesson is `passed` or `skipped`, or was sent ≥ 2 days
   ago — the reader may be behind by a day without the ladder stalling).
3. `credits[candidate] -= sum(weights of tracks with remaining rungs)`; `next_rung[candidate] += 1`.
4. If every track is blocked by prerequisites, take the highest-credit track anyway and mark
   the lesson `primer_needed: true`.
`pick.py --dry-run` prints the next 16 picks so the cadence can be eyeballed.

Fresh slot: `pick.py fresh` returns the target domain for today — the domain furthest below
its share in `last_fresh_domains` (shares in feeds.yaml), plus the reader's current level in
that domain (level of the last passed rung of the matching track, or B).

## 7. Dashboard database (ArtifactData) — the cache the frontend uses

Collections and documents (the job writes; the dashboard reads all and writes status):

- `lessons/{id}` — `{id, date, slot, track, track_name, domain, rung, level, title, est_min,
  status, sent_at, marked_at, summary, md, filed_to, review_due, sources:[{title,url}],
  day}`. `md` is the full lesson Markdown (front matter stripped).
- `tracks/{track}` — `{key, name, weight, total, done, next_title, next_level, files_to}`.
- `meta/state` — `{day, lessons_sent, lessons_passed, open:[ids], last_run_at,
  last_run_summary, trigger_id, reminder_trigger_id, repo_url, streak}`.
- `requests/{iso-ts}` — `{type: "more", created_at, handled: false}` written by the dashboard
  when the user asks for two more; the job sets `handled: true`.

Status changes from the dashboard: set `lessons/{id}.status` and `marked_at` (ISO). The job
treats any lesson whose `marked_at` is newer than `state.last_run_at` as a new mark and
mirrors it into the repo (front matter, log, filing).

## 8. Filing a passed lesson (`engine/file_passed.py <lesson-id>`)

1. Target folder = `files_to` from the lesson front matter. Create the folder and a README.md
   (same shape as `10-networking/README.md`: title, one-line description, Beginner /
   Intermediate / Advanced tables with columns `# | Topic | File | Interview Focus`, and a
   "Key Interview Questions by Level" section) if missing.
2. Write `<files_to>/<slug>.md`: the lesson body with a short header block
   (`> Source: IT Iaido lesson 2026-10-06-1 · Track · Level · passed on <date>`), without the
   dojo front matter and without the "Next on this track" section.
3. Append a row to the right level table in the section README (`#` = next number).
4. In the root `README.md`, add the topic link to the section's `| B |`/`| I |`/`| A |` row;
   if the section block does not exist yet (24/25/26), add a block in the same format under
   the right heading group.
5. Set `filed_to` in the lesson front matter, log `filed`.

## 9. Delivery (push + Dojo; `engine/render_email.py` is optional)

The reader asked for push notifications only (no email). The job's delivery is:
1. the two lesson documents written to the Dojo database (`lessons/{id}` with full `md`), and
2. one `PushNotification` (≤ 200 characters): `IT Iaido · Day N: <title 1> (<m> min) · <title 2>
   (<m> min) — open the Dojo`.
`engine/render_email.py` still renders an HTML version (`out/email.json`) for an explicit
"resend today by email" request; it is not part of the daily run.

## 10. Chat commands (handled by Claude in the project, applied to DB + repo)

"passed both" · "passed 1" · "review 2" · "skip 1" · "next 2" (same as the dashboard button) ·
"pause until <date>" · "change weight <track> <n>" · "add track <name>" · "resend today".
