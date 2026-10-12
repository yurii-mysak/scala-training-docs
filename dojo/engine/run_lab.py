#!/usr/bin/env python3
"""Run the Scala and Rust programs of a lesson and print their real output (SPEC §4 Language rule).

A runnable program is a fenced ```scala or ```rust block whose FIRST line is a marker comment:

    // file: Lab.scala               Scala 3 script, standard library only, with an @main
    // file: main.rs                 Rust binary (becomes src/main.rs of a fresh cargo project)
    // deps: ndarray@0.16, rand@0.8  optional second line for Rust: crates for `cargo add`
    // run: local                    optional: needs something the cloud cannot reach (a model
                                     download, a database, an API key); it is skipped here and
                                     the lesson must say "Run locally" and label its output

Fragments without a `// file:` marker are illustrations and are not run.

Usage:  python3 dojo/engine/run_lab.py <lesson-id|path> [--json] [--timeout 600]
Exit 0 when every runnable program ran successfully, 1 when one failed, 2 on usage errors.
Scala comes from dojo/engine/toolchain.sh (run it first); Rust uses cargo from PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

FENCE = re.compile(r"(?ms)^```(scala|rust)[ \t]*\n(.*?)^```[ \t]*$")
SCALA_VERSION = os.environ.get("SCALA_VERSION", "3.3.4")


def scala_bin() -> str:
    home = Path(os.environ.get("DOJO_TOOLS", Path.home() / ".local/dojo-tools")) / f"scala3-{SCALA_VERSION}" / "bin" / "scala"
    if home.exists():
        return str(home)
    found = shutil.which("scala")
    if not found:
        raise common.DojoError("scala not installed: run dojo/engine/toolchain.sh first")
    return found


def programs(body: str) -> list[dict]:
    out = []
    for i, m in enumerate(FENCE.finditer(body), 1):
        lang, code = m.group(1), m.group(2)
        lines = code.splitlines()
        if not lines:
            continue
        fm = re.match(r"^\s*//\s*file:\s*(\S+)", lines[0])
        if not fm:
            continue
        deps, local = [], False
        for line in lines[1:4]:
            d = re.match(r"^\s*//\s*deps:\s*(.+)$", line)
            if d:
                deps = [x.strip() for x in d.group(1).split(",") if x.strip()]
            if re.match(r"^\s*//\s*run:\s*local\b", line):
                local = True
        out.append({"n": i, "lang": lang, "file": fm.group(1), "code": code, "deps": deps, "local": local})
    return out


def run_scala(p: dict, timeout: int) -> dict:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / Path(p["file"]).name
        f.write_text(p["code"])
        r = subprocess.run([scala_bin(), str(f)], cwd=d, capture_output=True, text=True, timeout=timeout)
    return {"ok": r.returncode == 0, "stdout": r.stdout, "stderr": _clean(r.stderr)}


def run_rust(p: dict, timeout: int) -> dict:
    cargo = shutil.which("cargo")
    if not cargo:
        raise common.DojoError("cargo not found on PATH")
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d) / "lab"
        subprocess.run([cargo, "new", "-q", "--vcs", "none", str(proj)], check=True, capture_output=True, text=True)
        for dep in p["deps"]:
            args = [cargo, "add", "-q"]
            name, _, feats = dep.partition("+")          # crate@ver+feat1+feat2
            args.append(name)
            if feats:
                args += ["--features", feats.replace("+", ",")]
            r = subprocess.run(args, cwd=proj, capture_output=True, text=True, timeout=timeout)
            if r.returncode:
                return {"ok": False, "stdout": "", "stderr": f"cargo add {dep} failed:\n{_clean(r.stderr)}"}
        (proj / "src" / "main.rs").write_text(p["code"])
        r = subprocess.run([cargo, "run", "-q", "--release"], cwd=proj, capture_output=True, text=True, timeout=timeout)
    return {"ok": r.returncode == 0, "stdout": r.stdout, "stderr": _clean(r.stderr)}


def _clean(err: str) -> str:
    return "\n".join(l for l in err.splitlines() if not l.startswith("Picked up JAVA_TOOL_OPTIONS")).strip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lesson", help="lesson id (2026-10-14-1) or path to the .md file")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args(argv)
    path = common.find_lesson_path(a.lesson)
    _, body = common.parse_front_matter(path.read_text(encoding="utf-8"))
    results, failed = [], False
    for p in programs(body):
        if p["local"]:
            res = {"ok": True, "skipped": "run: local", "stdout": "", "stderr": ""}
        else:
            try:
                res = run_scala(p, a.timeout) if p["lang"] == "scala" else run_rust(p, a.timeout)
            except subprocess.TimeoutExpired:
                res = {"ok": False, "stdout": "", "stderr": f"timed out after {a.timeout}s"}
        failed |= not res["ok"]
        results.append({"block": p["n"], "lang": p["lang"], "file": p["file"], "deps": p["deps"], **res})
    if a.json:
        print(json.dumps({"lesson": str(path), "programs": results}, indent=2, ensure_ascii=False))
    else:
        if not results:
            print("no runnable programs (no ```scala/```rust block starting with '// file:')")
        for r in results:
            head = f"--- block {r['block']} · {r['lang']} · {r['file']}" + (f" · deps {', '.join(r['deps'])}" if r["deps"] else "")
            print(head + (" · SKIPPED (run: local)" if r.get("skipped") else (" · OK" if r["ok"] else " · FAILED")))
            if r["stdout"]:
                print(r["stdout"].rstrip())
            if not r["ok"] and r["stderr"]:
                print("stderr:\n" + r["stderr"][-3000:])
    return 1 if failed else 0


if __name__ == "__main__":
    common.run_cli(main)
