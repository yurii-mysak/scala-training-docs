#!/usr/bin/env python3
"""Render a lesson's ```mermaid blocks to PNG with the Mermaid CLI (mmdc).

  mermaid.py dojo/lessons/2026-10-06-1-some-slug.md

For block k (1-based) writes dojo/lessons/assets/<lesson-id>-<k>.png (plus <id>-<k>.mmd holding the
source it was rendered from) and prints a JSON list of {k, cid, png, mermaid_source[, error]}.

* Idempotent: a PNG whose .mmd sidecar matches the current source is reused, not re-rendered
  (use --force to re-render).
* Tolerant: if mmdc or Chromium is missing or a diagram fails, that entry has `png: null` and an
  `error` string; the exit code stays 0 so the email can still go out (render_email.py leaves a
  <pre> for diagrams without a PNG).

mmdc is found via $MMDC, PATH, or ~/.npm-global/bin.  Chromium via $DOJO_CHROMIUM,
$PUPPETEER_EXECUTABLE_PATH, /opt/pw-browsers/chromium, or PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import common

MMDC_TIMEOUT_S = 120


def find_mmdc() -> str | None:
    cands = [os.environ.get("MMDC"), shutil.which("mmdc"),
             str(Path.home() / ".npm-global/bin/mmdc"), "/home/claude/.npm-global/bin/mmdc"]
    for c in cands:
        if c and Path(c).exists():
            return c
    return None


def find_chromium() -> str | None:
    cands = [os.environ.get("DOJO_CHROMIUM"), os.environ.get("PUPPETEER_EXECUTABLE_PATH"),
             "/opt/pw-browsers/chromium", shutil.which("chromium"), shutil.which("chromium-browser"),
             shutil.which("google-chrome")]
    for c in cands:
        if c and Path(c).exists():
            return c
    return None


def _puppeteer_config(tmp: Path) -> Path:
    cfg: dict = {"args": ["--no-sandbox", "--disable-gpu"]}
    chromium = find_chromium()
    if chromium:
        cfg["executablePath"] = chromium
    p = tmp / "puppeteer.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


def lesson_id_of(path: Path, fm: dict) -> str:
    if fm.get("id"):
        return str(fm["id"])
    m = common.LESSON_FILE_RE.match(path.name)
    return f"{m.group(1)}-{m.group(2)}" if m else path.stem


def render_lesson(path: Path, force: bool = False) -> list[dict]:
    fm, body = common.load_lesson(path)
    lid = lesson_id_of(path, fm)
    blocks = common.find_mermaid_blocks(common.strip_html_comments(body))
    if not blocks:
        return []
    assets = common.assets_dir()
    assets.mkdir(parents=True, exist_ok=True)
    mmdc = find_mmdc()
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="dojo-mmd-") as td:
        tmp = Path(td)
        cfg = _puppeteer_config(tmp)
        for b in blocks:
            k, src = b["k"], b["source"]
            png = assets / f"{lid}-{k}.png"
            sidecar = assets / f"{lid}-{k}.mmd"
            entry = {"k": k, "cid": f"{lid}-{k}", "png": None, "mermaid_source": src}
            if (not force and png.exists() and png.stat().st_size > 0 and sidecar.exists()
                    and sidecar.read_text(encoding="utf-8") == src + "\n"):
                entry["png"] = common.rel(png)
                results.append(entry)
                continue
            if not mmdc:
                entry["error"] = "mmdc not found (set $MMDC or install @mermaid-js/mermaid-cli)"
                results.append(entry)
                continue
            mmd, out = tmp / f"{k}.mmd", tmp / f"{k}.png"
            mmd.write_text(src + "\n", encoding="utf-8")
            try:
                proc = subprocess.run(
                    [mmdc, "-i", str(mmd), "-o", str(out), "-p", str(cfg), "-b", "white", "-s", "2", "-q"],
                    capture_output=True, text=True, timeout=MMDC_TIMEOUT_S)
                if proc.returncode != 0 or not out.exists() or out.stat().st_size == 0:
                    err = (proc.stderr or proc.stdout or f"mmdc exit {proc.returncode}").strip()
                    entry["error"] = err[-800:]
                else:
                    shutil.copyfile(out, png)
                    sidecar.write_text(src + "\n", encoding="utf-8")
                    entry["png"] = common.rel(png)
            except subprocess.TimeoutExpired:
                entry["error"] = f"mmdc timed out after {MMDC_TIMEOUT_S}s"
            except OSError as e:
                entry["error"] = f"could not run mmdc: {e}"
            results.append(entry)
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Render every ```mermaid block of a lesson to dojo/lessons/assets/<id>-<k>.png.",
        epilog="Prints a JSON list of {k, cid, png, mermaid_source[, error]}.  Run from the repo root.")
    ap.add_argument("lesson", help="lesson file path or id")
    ap.add_argument("--force", action="store_true", help="re-render even when the PNG is up to date")
    args = ap.parse_args(argv)
    path = common.find_lesson_path(args.lesson)
    results = render_lesson(path, force=args.force)
    for r in results:
        if r.get("error"):
            print(f"warning: diagram {r['k']} of {path.name} not rendered: {r['error'].splitlines()[-1]}",
                  file=sys.stderr)
    print(common.dumps(results))
    return 0


if __name__ == "__main__":
    common.run_cli(main)
