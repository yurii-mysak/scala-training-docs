# IT Iaido engine

Deterministic helpers behind the daily job (contract: `../SPEC.md`). Python 3 + PyYAML + `markdown`;
every script runs from the repo root as `python3 dojo/engine/<script>.py ...`, takes `--help`, and prints
JSON (or a path) to stdout. Failures print one `error: ...` line and exit 2.

| Script | Does |
|---|---|
| `common.py` | paths, YAML/JSON, front matter, Kyiv time, event log, curriculum loading |
| `state.py` | `progress/state.json` (`show`, `init`, `set K V`, `touch`, `log EVENT`); keeps unknown keys |
| `pick.py` | `core [--commit]`, `fresh`, `--dry-run N`; smooth weighted round-robin + prerequisites (SPEC §6) |
| `new_lesson.py` | `core` / `fresh`: writes the lesson scaffold, commits picker state, logs `sent` |
| `mermaid.py` | renders each ```` ```mermaid ```` block to `lessons/assets/<id>-<k>.png`; never fails the run |
| `render_email.py` | optional: lessons -> `dojo/out/email.json` for an explicit "resend by email" request; the daily run delivers by push + Dojo (SPEC §9) |
| `mark.py` | `<id> passed\|review\|skipped\|sent`: front matter, state, log; idempotent |
| `file_passed.py` | files passed lessons into the KB: section README row, root README link (SPEC §8) |
| `sync_db.py` | `export <id>…\|--all`, `tracks`, `meta`, `all` -> `dojo/out/db/<collection>/<id>.json` |

## Commands the daily job runs, in order (`D` = today's Kyiv date, `D-1` = lesson id `<D>-1`)

```
# 1. mirror dashboard marks made since state.last_run_at, then file what passed
python3 dojo/engine/mark.py <id> passed|review|skipped --by dashboard --at <marked_at>   # per new mark
python3 dojo/engine/file_passed.py --all-passed-unfiled
# 2. slot 1 (core) and slot 2 (fresh)
python3 dojo/engine/new_lesson.py core --date D --n 1 --new-day      # prints the file to write
python3 dojo/engine/pick.py fresh                                    # target domain + reader level
python3 dojo/engine/new_lesson.py fresh --date D --n 2 --title "..." --domain X --level B|I|A --est-min 20 [--primer]
#    ... fill both scaffolds (delete every <!-- hint -->; follow the Evidence rule) ...
# 3. diagrams, email, dashboard cache
python3 dojo/engine/mermaid.py D-1 && python3 dojo/engine/mermaid.py D-2
python3 dojo/engine/sync_db.py all                                   # upload dojo/out/db/** to the dashboard DB = delivery
#    ... then one PushNotification naming both lessons ...
python3 dojo/engine/state.py touch                                   # last_run_at = now; then commit + push
```

On-demand lessons use slots 3 and 4 (`--n 3`, `--n 4`, `--on-demand`, no `--new-day`); `--on-demand`
exits 2 while any sent lesson is still open. The 20:00 reminder does no repo work: it reads the
dashboard database (`lessons` with status `sent`) and sends a push + a short email (RUNBOOK §R).
Eyeball the cadence any time with `python3 dojo/engine/pick.py --dry-run 16`.

## Behaviour worth knowing

- Repo root = two levels above these scripts; `$DOJO_REPO` overrides it, `$DOJO_NOW` pins "now" (tests).
- `new_lesson.py` is idempotent per id (date + N); `--new-day` bumps `day` once per date.
- A prerequisite counts as met when its lesson is passed/skipped or was sent 2+ Kyiv days ago.
- `open` in state = lessons still `sent`; `review` and `skipped` are marks, not open.
- `sync_db.py tracks`: `done` = rungs whose lesson is `passed`; `next_*` = next unsent rung.
- Email `<details>` blocks are kept; Gmail shows the answers expanded (no toggle support).

Tests: `python3 -m unittest discover -s dojo/engine/tests -t .` (fixture repo in a temp dir; the real
repo is never touched; the Mermaid tests run the real `mmdc` and skip only when it is missing).
