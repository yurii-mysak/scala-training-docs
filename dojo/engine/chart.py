#!/usr/bin/env python3
"""Render a lesson chart from a JSON spec (SPEC §4 Visual rule).

The numbers come from the lab's real output; the spec is data, kept next to the PNG so the
chart is reproducible:  dojo/lessons/assets/<lesson-id>-chart-<k>.json  ->  ...-chart-<k>.png

Spec:
{
  "type": "line" | "bar" | "scatter" | "hbar" | "heatmap",
  "title": "Training loss falls, validation loss turns up",
  "x_label": "epoch", "y_label": "MSE",
  "series": [                                  # line / bar / scatter / hbar
    {"name": "train", "x": [1, 2, 3], "y": [9.1, 4.2, 2.0], "style": "line|dashed|points"},
    {"name": "validation", "x": [1, 2, 3], "y": [9.3, 5.0, 6.1]}
  ],
  "categories": ["A", "B"],                    # bar / hbar: x labels (series give y only)
  "matrix": [[1, 2], [3, 4]], "row_labels": [...], "col_labels": [...],   # heatmap
  "annotate": [{"x": 3, "y": 6.1, "text": "overfitting starts"}],
  "hline": {"y": 0.5, "label": "threshold"},
  "log_y": false
}

Usage: python3 dojo/engine/chart.py <spec.json> [-o out.png]   (default: same name, .png)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

# One calm palette, readable on the Dojo's light and dark cards (the PNG has its own white ground).
INK, MUTED, GRID = "#1F2430", "#5F657B", "#E3E6EE"
PALETTE = ["#2F4B8A", "#C2571A", "#2E7D4F", "#8A3F8F", "#B08900", "#4F6D7A"]


def render(spec: dict, out: Path) -> Path:
    kind = spec.get("type", "line")
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=150)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    series = spec.get("series") or []
    if kind in ("line", "scatter"):
        for i, s in enumerate(series):
            c = s.get("color") or PALETTE[i % len(PALETTE)]
            style = s.get("style") or ("points" if kind == "scatter" else "line")
            if style == "points":
                ax.scatter(s["x"], s["y"], s=28, color=c, label=s.get("name"), zorder=3)
            else:
                ax.plot(s["x"], s["y"], color=c, linewidth=2, linestyle="--" if style == "dashed" else "-",
                        marker="o" if len(s["x"]) <= 25 else None, markersize=3.5, label=s.get("name"), zorder=3)
    elif kind in ("bar", "hbar"):
        cats = spec.get("categories") or [str(x) for x in (series[0].get("x") if series else [])]
        n = max(len(series), 1)
        width = 0.8 / n
        idx = range(len(cats))
        for i, s in enumerate(series):
            pos = [j + (i - (n - 1) / 2) * width for j in idx]
            c = s.get("color") or PALETTE[i % len(PALETTE)]
            bars = (ax.barh if kind == "hbar" else ax.bar)(pos, s["y"], width * 0.92, color=c, label=s.get("name"), zorder=3)
            if spec.get("value_labels", True):
                ax.bar_label(bars, fmt=spec.get("value_fmt", "%g"), fontsize=8, color=INK, padding=2)
        (ax.set_yticks if kind == "hbar" else ax.set_xticks)(list(idx))
        (ax.set_yticklabels if kind == "hbar" else ax.set_xticklabels)(cats)
        ax.grid(axis="y" if kind == "hbar" else "x", visible=False)
    elif kind == "heatmap":
        m = spec["matrix"]
        im = ax.imshow(m, cmap=spec.get("cmap", "Blues"), aspect="auto")
        ax.grid(False)
        ax.set_xticks(range(len(m[0])))
        ax.set_yticks(range(len(m)))
        if spec.get("col_labels"):
            ax.set_xticklabels(spec["col_labels"])
        if spec.get("row_labels"):
            ax.set_yticklabels(spec["row_labels"])
        vmax = max(max(r) for r in m) or 1
        for r, row in enumerate(m):
            for c, v in enumerate(row):
                ax.text(c, r, spec.get("value_fmt", "{:g}").format(v), ha="center", va="center", fontsize=9,
                        color="white" if v > vmax * 0.6 else INK)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    else:
        raise common.DojoError(f"unknown chart type {kind!r}")

    if spec.get("hline"):
        h = spec["hline"]
        ax.axhline(h["y"], color=MUTED, linestyle=":", linewidth=1.2, zorder=2)
        if h.get("label"):
            ax.annotate(h["label"], xy=(1, h["y"]), xycoords=("axes fraction", "data"), ha="right", va="bottom",
                        fontsize=8, color=MUTED)
    for a in spec.get("annotate") or []:
        ax.annotate(a["text"], xy=(a["x"], a["y"]), xytext=(a.get("dx", 20), a.get("dy", 20)), textcoords="offset points",
                    fontsize=9, color=INK, arrowprops={"arrowstyle": "->", "color": MUTED, "linewidth": 1})
    if spec.get("log_y"):
        ax.set_yscale("log")
    ax.set_title(spec.get("title", ""), fontsize=11, color=INK, loc="left", pad=10, fontweight="bold")
    ax.set_xlabel(spec.get("x_label", ""), fontsize=9, color=MUTED)
    ax.set_ylabel(spec.get("y_label", ""), fontsize=9, color=MUTED)
    if any(s.get("name") for s in series) and kind != "heatmap":
        ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("-o", "--out")
    a = ap.parse_args(argv)
    spec_path = Path(a.spec)
    spec = json.loads(spec_path.read_text())
    out = render(spec, Path(a.out) if a.out else spec_path.with_suffix(".png"))
    print(out)
    return 0


if __name__ == "__main__":
    common.run_cli(main)
