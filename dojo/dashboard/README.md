# Dojo dashboard (`dojo.html`)

`dojo.html` is the source of the published **IT Iaido Dojo** artifact: the live view of the
learning system where the reader marks lessons. The repo is the source of truth (SPEC §1); the
artifact's database is a cache that the scheduled job fills and the page reads and marks.

The file is page content only (no doctype/html/head/body); the Artifact tool wraps it at publish.

## Publish

Publish `dojo/dashboard/dojo.html` with exactly this capabilities declaration:

```json
{
  "db": {},
  "user": {},
  "mcp": { "servers": [ { "server": "Claude Code Remote", "tools": ["fire_trigger"] } ] }
}
```

- `db`: default access rules. Everyone admitted reads. Contributors (`interact`) and above
  write. The owner always writes. No custom rules are needed.
- `user`: only `can("data.write")` is used, to hide the mark buttons from people who can only
  read. No names or emails are read or stored.
- `mcp`: one connector tool, used by the "Request 2 more" button. A page that declares a
  connector cannot be shared publicly. That is fine for a private dashboard.

After the first publish, store the URL in `state.json` (`state.py set dashboard_url <url>`).
Republish to the same URL and omit `capabilities`, so the stored declaration carries forward.

## What the page reads

It opens one live subscription (`onSnapshot`) per source and re-renders from that state:

| Source | Query | Used for |
|---|---|---|
| `lessons` | whole collection | Today (status `sent`), History, open-lesson count |
| `tracks` | whole collection | Tracks section |
| `meta/state` | one document | day, streak, last delivery, `trigger_id`, `repo_url` |
| `requests` | `where("handled", "==", false)` | blocks a second request while one is in flight (30 min window) |

## What the page writes

Only these two writes, one at a time per document:

1. **A mark**: `lessons/{id}.update({status, marked_at})`
   - `status` is one of `passed`, `review`, `skipped`.
   - `marked_at` is an ISO-8601 UTC timestamp (`2026-10-06T18:30:12.345Z`).
   - **Undo** (only during the same visit) is another mark with `status: "sent"` and a new
     `marked_at`.
   - The page never writes `review_due`, `filed_to` or any other field.
2. **A request for two more**: `requests/{iso-ts}.set({type: "more", created_at: iso-ts, handled: false})`.
   The document id is that same ISO timestamp.
   - Then the page calls `Claude Code Remote` → `fire_trigger` with
     `{trigger_id: meta/state.trigger_id, text: "on-demand: 2 more lessons requested from the Dojo at <iso-ts>"}`.
   - The button works only when no lesson has status `sent` and `meta/state.trigger_id` is set.
   - If this view cannot call connectors, the request document is still written. The page then
     tells the reader to say `next 2` in the IT Iaido project chat.

## How the job must write documents

All writes go through `ArtifactData` against the artifact URL. Use `batch` for several
documents. Never put the data into the page source.

### `lessons/{id}`: one document per lesson, id = lesson id (`2026-10-06-1`)

| Field | Type | Notes |
|---|---|---|
| `id` | string | same as the document id |
| `date` | `YYYY-MM-DD` | Kyiv delivery date; used for sorting and the date column |
| `slot` | `core` \| `fresh` | |
| `track` | string | track key; `fresh` for fresh lessons (History's track filter uses it) |
| `track_name` | string | display name; for fresh lessons, the name of the closest track |
| `domain`, `rung` | string / null | stored, not shown |
| `level` | `B` \| `I` \| `A` | shown as a 1–3 notch pill |
| `title`, `summary` | string | plain text, set with `textContent` |
| `est_min` | number | |
| `status` | `sent` \| `passed` \| `review` \| `skipped` | an unknown value is treated as `sent` |
| `sent_at`, `marked_at` | ISO string / null | |
| `md` | string | full lesson Markdown, front matter stripped (see below) |
| `filed_to` | string / null | repo path; shown as a link `<repo_url>/blob/HEAD/<filed_to>` for passed lessons |
| `review_due` | `YYYY-MM-DD` / null | the job sets it (mark.py: +7 days); History shows it for `review` |
| `sources` | `[{title, url}]` | stored, not shown (the Markdown has its own Sources section) |
| `day` | number | |

The page orders lessons by `date` (newest first), then `sent_at` (newest first), then by the
number at the end of the id. So lesson 1 shows above lesson 2 within one delivery.

**`md` rendering rules.** The page renders `md` with marked 12 and then sanitizes it.
- The first `# Title` line is dropped, because the card already shows the title.
- A blockquote at the very top (the `> Track · Level · ~20 min …` meta line) is shown as a
  muted meta line.
- Every other blockquote is styled as an evidence quote.
- ` ```mermaid ` fences become diagrams, using mermaid 10.9.1 loaded on demand from cdnjs. Keep
  the diagrams fenced in `md`. Do not swap them for the email's PNGs, because relative image
  paths do not resolve in the artifact.
- `<details>`/`<summary>` are kept.
- These are removed: HTML comments, `<script>`, `<style>`, iframes, forms, inline SVG,
  `style`/`id`/`on*` attributes and non-http(s) links.
- A document must stay under 256 KiB. Lessons are far below that.

**Mirroring marks without losing them.** Before the job rewrites any `lessons/{id}` document
from the repo, it must:
1. Read the `lessons` collection.
2. Treat every document whose `marked_at` is newer than `meta/state.last_run_at` as a new
   dashboard mark, and apply it to the repo first:
   `mark.py <id> <status> --by dashboard --at <marked_at>`.
3. Then write the repo's view back.

A dashboard mark with `status: "sent"` is an **undo**. It reopens the lesson. `mark.py` does not
accept `sent` yet, so the job must reset the front matter itself: `status: sent`,
`marked_at: null`, `review_due: null`. If the lesson was never mirrored, nothing changes. If it
was already filed, the filed copy stays and the job should log a `reopened` note.

### `tracks/{key}`: one per curriculum track

`{key, name, weight, total, done, next_title, next_level, files_to}`
- `total` is the number of rungs. `done` is the rungs passed or skipped.
- `weight` is per 16 core lessons and is shown as `5/16`.
- When the ladder is finished, set `next_title: null`. The page then shows "Ladder complete".
- A ladder of up to 48 rungs is drawn one segment per rung. A longer ladder is drawn as a
  plain bar.

### `meta/state`: one document

`{day, lessons_sent, lessons_passed, open:[ids], last_run_at, last_run_summary, trigger_id, reminder_trigger_id, repo_url, streak}`
- `day` and `streak` are integers. The streak is drawn as tally marks in groups of five, up to
  30, with the exact number beside it.
- `last_run_summary` is one plain sentence, shown under the header.
- `trigger_id` must be set, or "Request 2 more" stays disabled.
- `repo_url` must be `https://…`. It is used for the footer link and the "Filed to" links.

### `requests/{iso-ts}`

When the job delivers the lessons for a request, it updates that document to
`{handled: true}` (adding `handled_at` is fine). The page treats an unhandled request younger
than 30 minutes as in flight. An older one no longer blocks the button. At each daily run, the
job should also mark stale unhandled requests as handled.

## Empty database

On first load with no documents, the page shows a designed empty state: "The first lessons
arrive at 09:00 Kyiv", and what Today, Tracks and History will show. Nothing needs seeding by
hand. The first job run fills it.

## Per-viewer conveniences

`localStorage` key `it-iaido-dojo:prefs` = `{status, track, help}`. It holds the History filters
and whether "How it works" is open. Every access is wrapped in try/catch, and the page works
without it.

## Libraries

- `https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js`: loaded at page load.
- `https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js`: loaded lazily, the
  first time an opened lesson contains a diagram. If a global `mermaid` with `run()` already
  exists, it is reused. The diagram colours come from the page's theme tokens.
- Google Fonts: Shippori Mincho B1 (display), Red Hat Text (UI), Red Hat Mono (code). Each has
  a system fallback.
