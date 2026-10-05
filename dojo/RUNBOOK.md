# IT Iaido — RUNBOOK for the scheduled job

You are the IT Iaido course job: a fresh Claude session started by a scheduled task (or fired on
demand). You have no memory of earlier runs; everything you need is in this repository and in the
dashboard database. Follow this runbook top to bottom. Read `dojo/SPEC.md` once first (the contract),
and `dojo/engine/README.md` (the scripts).

Constants
- Reader: Yuriy, yura.mysak@gmail.com, time zone Europe/Kyiv. Backend engineer (Scala/Akka, JVM,
  distributed systems), QA Lead background, now Product Owner, advanced Claude Code user; new to
  ML maths but strong at programming. Address him directly, as a knowledgeable colleague.
- Repo: https://github.com/yurii-mysak/scala-training-docs (branch `main`), knowledge base +
  this course under `dojo/`.
- Dashboard (artifact): https://claude.ai/artifact/Eedt4UPNqrameHt3dahkHp — its database is read
  and written with the `ArtifactData` tool using this URL.
- Delivery: push notifications only (`PushNotification`), by the reader's choice — no email. The
  lessons are read on the Dojo, so the database write in step 9 IS the delivery.
- Hard rules: two lessons per daily run, each 15–30 minutes; slot 1 from the curriculum, slot 2
  researched today; basics before advanced; the Evidence rule (SPEC §4) on every claim; only
  `passed` lessons are filed into the knowledge base; never send the same day's pair twice.

## 0. Setup (every run)

1. Load tools: `ToolSearch` with `select:ArtifactData,PushNotification`.
2. Attach and clone the repo: `add_repo` owner `yurii-mysak`, repo `scala-training-docs`,
   access `push`; then `git clone --depth 50 https://github.com/yurii-mysak/scala-training-docs /home/claude/scala-training-docs`
   (generous timeout; if the folder already exists and `git -C … rev-parse HEAD` works, reuse it
   and `git pull --ff-only`). `cd /home/claude/scala-training-docs`. Set
   `git config user.name "IT Iaido job"` and `git config user.email "yura.mysak@gmail.com"`.
3. Dependencies: `python3 -c "import yaml, markdown"`; if missing,
   `pip install --break-system-packages pyyaml markdown`. `which mmdc || npm i -g @mermaid-js/mermaid-cli`.
4. Decide the MODE:
   - **on-demand** if an extra user message in this run contains `on-demand` (the Dojo's
     "Request 2 more" button or Claude in the project fired you).
   - **daily** otherwise.
   Today = `python3 -c "import sys; sys.path.insert(0,'dojo/engine'); import common; print(common.kyiv_today())"`.
5. Idempotency: list `dojo/lessons/<today>-1-*.md`. In **daily** mode, if it exists, today's pair
   was already sent: do steps 1–2 only (sync marks, file passed), commit, push, and finish with a
   one-line report. In **on-demand** mode the next slot numbers are 3 and 4 (or 5 and 6 …):
   `N = (number of today's lesson files) + 1`.

## 1. Sync marks from the dashboard

1. `ArtifactData` → `list` collection `lessons` (`query.limit` 1000) for the dashboard URL. Keep
   every document's `version` (you need it for writes later).
2. For each document whose `marked_at` is set and differs from the local lesson's `marked_at`
   (front matter of `dojo/lessons/<id>-*.md`), or whose `status` differs from the local one:
   `python3 dojo/engine/mark.py <id> <status> --by dashboard --at <marked_at>`
   (`status` may be `passed`, `review`, `skipped` or `sent` — `sent` is an undo).
3. `ArtifactData` → `query` collection `requests` where `handled == false`. Remember their ids and
   versions; in on-demand mode you will set `handled: true` at the end (also when you refuse).

## 2. File passed lessons into the knowledge base

`python3 dojo/engine/file_passed.py --all-passed-unfiled` — it copies each newly passed lesson
into its `files_to` section (creating `24-ai-ml-foundations/`, `25-software-architecture/` or
`26-rust/` with a README on first use), appends the README row and the root README link, and sets
`filed_to`. Read its JSON output and mention filed titles in the final report.

## 3. On-demand gate

In **on-demand** mode, after step 1: `python3 dojo/engine/state.py show` → `open`. If any lesson
is still `sent`, do NOT generate lessons (`new_lesson.py … --on-demand` refuses with exit 2 as a
second guard; pass `--on-demand` on both scaffolds in this mode). Send one push:
"IT Iaido: two more unlock once <titles> are marked — open the Dojo", set the request
documents to `handled: true` (ArtifactData `update` with `if_version`), commit any filing from
step 2, push, and finish. Otherwise continue.

## 4. Review returns (daily mode only)

Lessons with `status: review` and `review_due <= today` (front matter) come back: run
`python3 dojo/engine/mark.py <id> sent --by job` for each, so the lesson is open again on the Dojo
(it keeps its original text; the reader re-reads it and marks it passed or review again), and name
them in the push notification of step 9 as `review: <title>`. No separate recap document.

## 5. Slot 1 — the core lesson

1. `python3 dojo/engine/pick.py core` → read the rung (title, level, summary, key_points, diagram,
   example, presentation, sources with locators, prereqs, `primer_needed`).
2. `python3 dojo/engine/new_lesson.py core --date <today> --n <N> --new-day` (omit `--new-day`
   in on-demand mode) → the scaffold path. The scaffold's front matter is final; only the body is
   written.
3. Note the next rung's title (`pick.py core` again shows it, without `--commit`) for the
   "Next on this track" line.

## 6. Slot 2 — the fresh lesson

1. `python3 dojo/engine/pick.py fresh` → `domain`, `reader_level`, `track_name`, `files_to`.
2. Follow `dojo/feeds.yaml` → `selection_protocol`, using the feeds tagged with that domain. Budget:
   at most 5 `WebFetch` calls to scan indexes and 2 to read the chosen item (plus 1 for a secondary
   source if the primary cannot be quoted). Never pick a URL that already appears in
   `dojo/lessons/` (`grep -rl <url> dojo/lessons`). Prefer an item that connects with today's core
   lesson or with the reader's current rung in that domain. Record: title, author/org, date, URL,
   level (B/I/A), 2–3 verbatim passages (copied exactly), the claim, the mechanism, the evidence,
   the trade-offs.
3. `python3 dojo/engine/new_lesson.py fresh --date <today> --n <N+1> --title "<title>" --domain <domain> --level <B|I|A> --est-min <15..30> [--primer]`
   (`--primer` when the item sits above `reader_level`).

## 7. Writing — two writer subagents, then the gate

Launch two `Agent` subagents in parallel (model `opus`), one per lesson. Give each: the reader
profile above; the scaffold path; the full rung dict (core) or the research notes with the verbatim
passages (fresh); the next-rung title (core); and these instructions verbatim:

> Write the lesson body into the scaffold file, keeping the front matter exactly as it is and
> replacing every `<!-- … -->` hint. Follow `dojo/SPEC.md` §4: sections in order — Why this matters
> (3 lines) · [Primer, fresh lessons above the reader's level] · The idea (600–1200 words, one or
> two ```mermaid diagrams: `flowchart LR|TD` or `sequenceDiagram`; quote any label containing
> parentheses, colons or slashes in double quotes; no HTML inside labels) · Worked example or Lab
> (5–10 minutes, copy-pasteable, concrete, following SPEC §4 "Lab rule": the question first,
> numbered steps, code that prints intermediate values, a `### Reading the output` section that
> explains every column, traces the arithmetic and ends each block with a bold **Verdict**, then a
> numbered cause → consequence chain; run the code and paste its real output) · Self-check (3 numbered questions, each answer in
> `<details><summary>Answer</summary>…</details>`) · Sources (every URL used, one line on what it
> contributed, `accessed <today>`) · Next on this track (one sentence; core lessons only).
> Evidence rule: cite books/courses inline with chapter, section or timestamp; back every claim from
> a blog, paper, release note or news item with a verbatim 1–3 sentence quote in a blockquote
> followed by `— Author or org, *Title*, date, URL`; fetch each source you quote with `WebFetch`
> and copy the words, never paraphrase as a quote, never invent one; numbers and dates carry their
> citation in the same sentence. Presentation level `<presentation>`: minimal = one idea, one
> diagram, one tiny example; standard = adds a worked example and one trade-off; deep = lab, code,
> trade-offs, failure modes. The lesson must be readable in `<est_min>` minutes. Write to the
> reader directly, plainly, no filler. When done, run
> `python3 dojo/engine/check_lesson.py <id>` and fix every error it reports before you finish.
> Do not run git. Report in ≤80 words: word count, diagrams, sources quoted.

When both return: run `python3 dojo/engine/check_lesson.py <id>` yourself on both. If errors
remain, fix them directly (you may use `WebFetch` to recover a quote). Then
`python3 dojo/engine/mermaid.py <id>` for both; if a diagram fails to render, simplify its Mermaid
source until it renders (the error text names the line).

## 8. Publish: commit, push

1. `python3 dojo/engine/sync_db.py all` (produces `dojo/out/db/**`; nothing is uploaded yet).
2. `git add -A dojo 2[0-9]-* [0-9][0-9]-*/ README.md .gitignore` (lesson files, assets, progress,
   filed copies, READMEs), `git commit -m "dojo: day <day> — <title 1> · <title 2>"`, then
   `git fetch origin main && git rebase origin/main && git push origin main`. If the push is
   refused, retry once after `git pull --rebase`; if it still fails, continue (the Dojo gets the
   lessons anyway) and say so in the report.
3. No email: the reader asked for push notifications only. (`render_email.py` exists for an
   explicit "resend today by email" request from chat; never run it from the job.)

## 9. Dashboard database

Using the versions from step 1 (re-`list` if you wrote anything since):
1. For every file in `dojo/out/db/lessons/*.json`: `set` collection `lessons`, `doc_id` = id,
   `file_path` = that file, `if_version` when the document already exists. Use `batch` (≤50 writes).
2. For every `dojo/out/db/tracks/*.json`: `set` collection `tracks`, `doc_id` = track key, same
   rule. One `batch`.
3. `dojo/out/db/meta/state.json`: `update` (merge) collection `meta`, `doc_id` `state`,
   `if_version` of the existing document. It must keep `trigger_id`, `reminder_trigger_id`,
   `repo_url`, `dashboard_url` — they are in the file because they live in `progress/state.json`.
4. On-demand: `update` each request from step 1.3 with `{handled: true}` and its `if_version`.
5. Read back one lesson document (`get`) to confirm the write landed — this is the delivery.
6. `PushNotification` (status `proactive`, ≤ 200 characters):
   `IT Iaido · Day <day>: <title 1> (<m> min) · <title 2> (<m> min) — open the Dojo`.

## 10. Finish

1. `python3 dojo/engine/state.py touch` (sets `last_run_at`), `python3 dojo/engine/state.py log sent --note "day <day>: <ids>"`,
   then `python3 dojo/engine/sync_db.py meta` and `ArtifactData` → `update` `meta/state` from
   `dojo/out/db/meta/state.json` with its `if_version`, so the Dojo shows this delivery time.
2. `git add -A dojo && git commit -m "dojo: state after day <day>" && git push origin main`.
3. Final response, 3–6 lines: mode, the two titles with tracks/levels/minutes, marks synced,
   lessons filed, anything that failed (git push, database write, diagram) and what you did instead.

Failure policy: never send the pair twice; if the database write fails, retry it once, then send
the push with "Dojo write failed — lessons are in the repo" and the GitHub link; if the fresh
research finds nothing within 90 days, use a timeless classic from the same feeds and say so in
the lesson; if a writer subagent fails, write that lesson yourself to the same standard.

---

## R. The 20:00 reminder (separate scheduled task)

1. `ToolSearch` `select:ArtifactData,PushNotification`.
2. `ArtifactData` → `query` collection `lessons` where `status == "sent"` (dashboard URL above).
3. If none: finish silently with one line ("nothing open").
4. Otherwise one `PushNotification` (proactive, ≤ 200 characters):
   `IT Iaido: <n> lesson(s) still open — <titles, trimmed>. 15–30 min each — open the Dojo.`
   No email, by the reader's choice.
5. `ArtifactData` → `update` `meta/state` with `{last_reminder_at: <now iso>}` and the document's
   `if_version` (`get` it first). No repo work. Final response: one line.
