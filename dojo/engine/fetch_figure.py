#!/usr/bin/env python3
"""Download an openly licensed figure for a lesson and print the Markdown to embed it (SPEC §4 Visual rule).

Only use figures whose licence allows reuse with attribution (CC BY, CC BY-SA, CC0/public domain,
MIT/Apache docs). Anything else is REPLICATED instead (redrawn as Mermaid or a chart) and
captioned "Adapted from …".  From the cloud only GitHub-hosted files are reachable
(raw.githubusercontent.com, github.com): many course sites and docs are published from GitHub
repos (e.g. cs231n.github.io -> github.com/cs231n/cs231n.github.io), so fetch the raw file there.

Usage:
  python3 dojo/engine/fetch_figure.py <url> <lesson-id> --k 1 --credit "Stanford CS231n, Andrej Karpathy" \
      --license "MIT" --page https://cs231n.github.io/neural-networks-1/ --caption "A 2-layer network"
Writes dojo/lessons/assets/<id>-fig-<k>.<ext> and a .json provenance sidecar; prints the Markdown.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

OK_LICENSES = ("cc by", "cc-by", "cc0", "public domain", "mit", "apache", "bsd", "cc by-sa", "cc-by-sa")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("lesson")
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--credit", required=True, help="author / organisation")
    ap.add_argument("--license", required=True, help="e.g. 'CC BY 4.0', 'MIT'")
    ap.add_argument("--page", required=True, help="the page the figure appears on (for the reader to check)")
    ap.add_argument("--caption", required=True)
    a = ap.parse_args(argv)
    if not any(x in a.license.lower() for x in OK_LICENSES):
        raise common.DojoError(f"licence {a.license!r} does not allow reuse: replicate the figure instead")
    ext = Path(a.url.split("?")[0]).suffix.lower() or ".png"
    if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
        raise common.DojoError(f"not an image URL ({ext})")
    out = common.assets_dir() / f"{a.lesson}-fig-{a.k}{'.png' if ext == '.svg' else ext}"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(ext + ".download")
    r = subprocess.run(["curl", "-sSfL", "--max-time", "60", "-o", str(tmp), a.url], capture_output=True, text=True)
    if r.returncode:
        raise common.DojoError(f"download failed ({r.stderr.strip()[:200]}): replicate the figure instead")
    if ext == ".svg":
        r = subprocess.run(["npx", "-y", "@resvg/resvg-js-cli", str(tmp), str(out)], capture_output=True, text=True)
        tmp.unlink(missing_ok=True)
        if r.returncode:
            raise common.DojoError("could not rasterise SVG: replicate the figure instead")
    else:
        tmp.rename(out)
    meta = {"url": a.url, "page": a.page, "credit": a.credit, "license": a.license, "caption": a.caption}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(f"![{a.caption}](assets/{out.name})\n\n*Figure {a.k}: {a.caption}. Source: {a.credit}, "
          f"[{a.page}]({a.page}) ({a.license}).*")
    return 0


if __name__ == "__main__":
    common.run_cli(main)
