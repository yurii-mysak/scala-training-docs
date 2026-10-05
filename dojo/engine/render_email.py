#!/usr/bin/env python3
"""Render lessons as one email (SPEC §9).

  render_email.py 2026-10-06-1 2026-10-06-2 [--out dojo/out/email.json] [--render-diagrams]

Writes dojo/out/email.json = {subject, html, text, attachments:[{filename, cid, path, mimeType, inline}], meta}
for the Gmail connector.  Mermaid blocks become <img src="cid:<id>-<k>"> when
dojo/lessons/assets/<id>-<k>.png exists (run mermaid.py first, or pass --render-diagrams); otherwise
the diagram source stays in a <pre>.  All CSS is inline; layout is table based, 680px max width.
HTML comments (scaffold hints) are removed from the output.  Run from the repo root.
"""
from __future__ import annotations

import argparse
import html as html_lib
import re
import struct
import sys
from pathlib import Path

import markdown

import common
import state as state_mod
from common import DojoError

MD_EXTENSIONS = ["fenced_code", "tables", "sane_lists", "attr_list", "md_in_html"]  # toc deliberately off
FOOTER_SENTENCE = ("Mark them on the Dojo, or tell Claude in the IT Iaido project: "
                   "'passed both' / 'review 1' / 'skip 2'.")
IMG_MAX_W = 616

_FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
_MONO = "SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

# Inline styles per tag (email clients drop <style> blocks often, so everything is inline).
STYLES = {
    "h1": f"margin:24px 0 10px;font-size:22px;line-height:1.3;color:#102a43;font-family:{_FONT};",
    "h2": f"margin:28px 0 10px;padding-bottom:5px;font-size:19px;line-height:1.3;color:#102a43;"
          f"border-bottom:1px solid #d9e2ec;font-family:{_FONT};",
    "h3": f"margin:22px 0 8px;font-size:16px;line-height:1.35;color:#243b53;font-family:{_FONT};",
    "h4": f"margin:18px 0 6px;font-size:15px;line-height:1.35;color:#243b53;font-family:{_FONT};",
    "p": "margin:0 0 14px;",
    "ul": "margin:0 0 14px;padding-left:24px;",
    "ol": "margin:0 0 14px;padding-left:26px;",
    "li": "margin:0 0 8px;",
    "blockquote": "margin:0 0 16px;padding:10px 16px;border-left:4px solid #5c7cfa;background:#f1f4ff;color:#334e68;",
    "a": "color:#1c7ed6;text-decoration:underline;",
    "table": "border-collapse:collapse;margin:0 0 16px;width:100%;font-size:14px;",
    "th": "border:1px solid #d9e2ec;background:#f0f4f8;padding:6px 9px;text-align:left;vertical-align:top;",
    "td": "border:1px solid #d9e2ec;padding:6px 9px;vertical-align:top;",
    "hr": "border:0;border-top:1px solid #d9e2ec;margin:22px 0;",
    "img": "max-width:100%;height:auto;border:0;display:block;margin:10px auto;",
    "details": "margin:8px 0;padding:8px 12px;background:#f8fafc;border:1px solid #e4e7eb;border-radius:6px;",
    "summary": "font-weight:600;color:#486581;",
    "code": f"font-family:{_MONO};font-size:90%;background:#f0f4f8;padding:1px 5px;border-radius:4px;color:#102a43;",
}
PRE_STYLES = {
    "pre": f"margin:0 0 16px;padding:12px 14px;background:#f6f8fa;border:1px solid #d9e2ec;border-radius:6px;"
           f"font-family:{_MONO};font-size:13px;line-height:1.5;white-space:pre-wrap;word-wrap:break-word;"
           f"overflow-x:auto;color:#1f2933;",
    "code": f"font-family:{_MONO};font-size:13px;background:none;padding:0;border:0;color:#1f2933;",
}

_OPEN_TAG = re.compile(r"<(h[1-6]|p|ul|ol|li|blockquote|a|table|th|td|hr|img|details|summary|pre|code)"
                       r"(\s[^<>]*?)?(\s*/)?>", re.I)
_PRE_SPLIT = re.compile(r"(<pre\b.*?</pre>)", re.S | re.I)


# --------------------------------------------------------------------------- HTML helpers

def _style_with(styles: dict[str, str]):
    def repl(m: re.Match) -> str:
        tag = m.group(1).lower()
        attrs, selfclose = m.group(2) or "", m.group(3) or ""
        base = styles.get(tag)
        if not base:
            return m.group(0)
        sm = re.search(r'\sstyle="([^"]*)"', attrs)
        extra = ""
        if sm:  # keep e.g. text-align from the tables extension; it wins by coming last
            extra = sm.group(1)
            attrs = attrs[:sm.start()] + attrs[sm.end():]
        return f'<{tag}{attrs} style="{base}{extra}"{selfclose}>'
    return repl


def inline_styles(html: str) -> str:
    """Add inline CSS to every styled tag; <pre> blocks get code-block styling."""
    parts = _PRE_SPLIT.split(html)
    normal, pre = _style_with(STYLES), _style_with(PRE_STYLES)
    for i, part in enumerate(parts):
        parts[i] = _OPEN_TAG.sub(pre if i % 2 else normal, part)
    return "".join(parts)


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        return struct.unpack(">II", head[16:24])
    except OSError:
        return None


def split_header(md: str, fm: dict) -> tuple[str, str, str]:
    """(title, meta line, rest of body) - the H1 and the '> ...' meta line become the card header."""
    lines = md.lstrip("\n").splitlines()
    title = str(fm.get("title") or "")
    i = 0
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        i = 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    meta = ""
    if i < len(lines) and lines[i].startswith(">"):
        j = i
        meta_lines = []
        while j < len(lines) and lines[j].startswith(">"):
            meta_lines.append(lines[j].lstrip("> ").strip())
            j += 1
        meta, i = " ".join(meta_lines), j
    return title, meta, "\n".join(lines[i:]).strip("\n") + "\n"


IMG_MODE = {"mode": "raw", "raw_base": None}  # set from the CLI; see --img-mode


def raw_base_for(state: dict) -> str:
    """raw.githubusercontent.com base for lesson assets, derived from repo_url (public repo)."""
    repo = (state.get("repo_url") or common.DEFAULT_REPO_URL).rstrip("/").removesuffix(".git")
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", repo)
    if not m:
        return ""
    return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/main/dojo/lessons/assets/"


def md_to_html(md: str, lesson_id: str, attachments: list[dict]) -> str:
    """Markdown -> email-safe HTML; mermaid blocks with a PNG become images.

    --img-mode raw (default): <img src="https://raw.githubusercontent.com/.../assets/<id>-<k>.png">
      (the job pushes the PNGs to the public repo before sending; Gmail proxies remote images).
    --img-mode cid: inline attachments, <img src="cid:<id>-<k>.png"> (filename doubles as Content-ID).
    --img-mode dojo: no image at all; a short box links to the Dojo, which renders the Mermaid itself
      (used when the push failed, since base64 attachments cannot pass reliably through a tool call).
    """
    source = md

    def repl(block: dict) -> str:
        cid = f"{lesson_id}-{block['k']}"
        png = common.assets_dir() / f"{cid}.png"
        if not png.exists():
            return source[block["start"]:block["end"]]  # keep the fence -> <pre>
        size = png_size(png)
        width = f' width="{min(size[0] // 2, IMG_MAX_W)}"' if size else ""
        if IMG_MODE["mode"] == "cid":
            attachments.append({"filename": f"{cid}.png", "cid": f"{cid}.png", "path": str(png.resolve()),
                                "mimeType": "image/png", "inline": True})
            return f'\n\n<img src="cid:{cid}.png" alt="diagram"{width}>\n\n'
        if IMG_MODE["mode"] == "dojo":
            # No hosted image: point at the Dojo, which renders the Mermaid source itself.
            dash = state_mod.load_state().get("dashboard_url") or ""
            return (f'\n\n<p style="margin:12px 0;padding:10px 14px;border:1px dashed #B1B7C9;border-radius:4px;'
                    f'color:#434960;font-size:14px">Diagram {block["k"]}: open this lesson on the '
                    f'<a href="{dash}">Dojo</a> to see it rendered.</p>\n\n')
        base = IMG_MODE["raw_base"] or raw_base_for(state_mod.load_state())
        return f'\n\n<img src="{base}{cid}.png" alt="diagram"{width} style="max-width:100%">\n\n'

    md = common.replace_mermaid_blocks(md, repl)
    # A <details> that starts a line is a raw HTML block; markdown="1" makes md_in_html render its content.
    md = re.sub(r'(?m)^<details(?![^>]*\bmarkdown=)([^>]*)>', r'<details markdown="1"\1>', md)
    html = markdown.markdown(md, extensions=MD_EXTENSIONS, output_format="html")
    return inline_styles(html)


# --------------------------------------------------------------------------- plain text

def md_to_text(md: str) -> str:
    md = common.replace_mermaid_blocks(md, lambda b: "[diagram: see the HTML version or the Dojo]")
    md = re.sub(r"<details[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>",
                lambda m: f"{common.clean_inline_md(m.group(1))}: {common.clean_inline_md(m.group(2))}",
                md, flags=re.S | re.I)
    out, in_fence = [], False
    for line in md.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if in_fence:
            out.append("    " + line)
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"[\1]", line)
        line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", line)
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"^#{1,6}\s+", "", line)
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


# --------------------------------------------------------------------------- build

def lesson_day(fm: dict, state: dict, all_dates: list[str]) -> int:
    if isinstance(fm.get("day"), int):
        return fm["day"]
    d = str(fm.get("date"))
    return all_dates.index(d) + 1 if d in all_dates else int(state.get("day", 0))


def build_email(ids: list[str], render_diagrams: bool = False) -> dict:
    state = state_mod.load_state()
    lessons = []
    for ref in ids:
        path = common.find_lesson_path(ref)
        fm, body = common.load_lesson(path)
        if render_diagrams:
            import mermaid
            mermaid.render_lesson(path)
        lessons.append((path, fm, body))

    all_dates = sorted({str(x["fm"].get("date")) for x in common.load_all_lessons()})
    day = max(lesson_day(fm, state, all_dates) for _, fm, _ in lessons)
    date = common.parse_date(max(str(fm.get("date")) for _, fm, _ in lessons))
    total_min = sum(int(fm.get("est_min") or 0) for _, fm, _ in lessons)

    template = (common.templates_dir() / "email.html").read_text(encoding="utf-8")
    m = re.search(r"<!--card-->(.*?)<!--/card-->", template, re.S)
    if not m:
        raise DojoError("email.html template has no <!--card-->...<!--/card--> block")
    card_tpl = m.group(1)

    cards, text_parts, attachments, titles = [], [], [], []
    for i, (path, fm, body) in enumerate(lessons, start=1):
        lid = str(fm["id"])
        md = common.strip_html_comments(body)
        title, meta, rest = split_header(md, fm)
        if not meta:
            meta = f"{fm.get('track')} · {common.level_name(fm.get('level'))} · ~{fm.get('est_min')} min"
        titles.append(title or str(fm.get("title")))
        # The H1 and meta line form the card header; mermaid numbering (k) is unaffected because
        # the header never contains diagrams, so it matches what mermaid.py rendered.
        body_html = md_to_html(rest, lid, attachments)
        slot_label = "Core" if fm.get("slot") == "core" else "Fresh"
        cards.append(common.render_template(card_tpl, {
            "badge": f"{slot_label} · lesson {i} of {len(lessons)} · {fm.get('est_min')} min",
            "title": html_lib.escape(titles[-1]),
            "meta": html_lib.escape(meta),
            "body": body_html,
        }))
        text_parts.append(f"{'=' * 72}\n{i}. {titles[-1]}\n{meta}\n{'=' * 72}\n\n{md_to_text(rest)}")

    dash = state.get("dashboard_url")
    dash_html = (f'<div style="margin-bottom:6px;"><a href="{html_lib.escape(dash, quote=True)}" '
                 f'style="color:#1c7ed6;font-weight:600;">Open the Dojo dashboard</a></div>') if dash else ""
    subject = "IT Iaido · Day {} · {}".format(day, " · ".join(titles))
    count = f"{len(lessons)} lesson{'s' if len(lessons) != 1 else ''}"
    ctx = {
        "subject": html_lib.escape(subject),
        "preheader": html_lib.escape(f"{' · '.join(titles)} — {total_min} min"),
        "day": day, "date": common.human_date(date),
        "lesson_count": count, "total_minutes": total_min,
        "dashboard_link": dash_html,
        "footer_sentence": html_lib.escape(FOOTER_SENTENCE),
    }
    # Fill the page template with a placeholder for the cards, strip the template's own comments, and only
    # then splice the rendered cards in (so lesson text is never scanned for {{...}} or comments again).
    page_tpl = template[:m.start()] + "@@CARDS@@" + template[m.end():]
    page = common.render_template(page_tpl, ctx)
    page = re.sub(r"<!--.*?-->\s*", "", page, flags=re.S)
    # Optional review recap (RUNBOOK §4): dojo/out/recaps.md is rendered as a card before the lessons.
    recaps_path = common.out_dir() / "recaps.md"
    if recaps_path.exists() and recaps_path.read_text(encoding="utf-8").strip():
        recap_md = recaps_path.read_text(encoding="utf-8")
        recap_html = inline_styles(markdown.markdown(recap_md, extensions=MD_EXTENSIONS, output_format="html"))
        cards.insert(0, common.render_template(card_tpl, {
            "badge": "Review · a week later", "title": "Quick recap",
            "meta": "Lessons you marked “review again”", "body": recap_html}))
        text_parts.insert(0, "QUICK RECAP\n\n" + md_to_text(recap_md))
    page = page.replace("@@CARDS@@", "".join(cards))

    header_text = f"IT Iaido · Day {day} · {common.human_date(date)} · {count} · {total_min} min"
    footer_text = ((f"Dojo dashboard: {dash}\n" if dash else "") + FOOTER_SENTENCE)
    text = header_text + "\n\n" + "\n\n".join(text_parts) + "\n" + "-" * 72 + "\n" + footer_text + "\n"

    attachments.sort(key=lambda a: a["cid"])
    return {
        "subject": subject, "html": page, "text": text, "attachments": attachments,
        "meta": {"day": day, "date": date.isoformat(), "lessons": [str(fm["id"]) for _, fm, _ in lessons],
                 "total_minutes": total_min},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Render one or more lessons into dojo/out/email.json for the Gmail connector.",
        epilog="Example:  python3 dojo/engine/render_email.py 2026-10-06-1 2026-10-06-2\n"
               "Run mermaid.py on each lesson first so diagrams become inline images.")
    ap.add_argument("ids", nargs="+", metavar="LESSON_ID", help="lesson ids (or files), in the order to show")
    ap.add_argument("--out", help="output JSON path (default: dojo/out/email.json)")
    ap.add_argument("--render-diagrams", action="store_true", help="run mermaid.py logic first for each lesson")
    ap.add_argument("--img-mode", choices=["raw", "cid", "dojo"], default="raw",
                    help="raw = link PNGs from the public repo on GitHub (default); cid = inline attachments; "
                         "dojo = no images, link to the Dojo (fallback when the push failed)")
    args = ap.parse_args(argv)

    IMG_MODE["mode"] = args.img_mode
    IMG_MODE["raw_base"] = raw_base_for(state_mod.load_state())
    email = build_email(args.ids, render_diagrams=args.render_diagrams)
    out = Path(args.out) if args.out else common.out_dir() / "email.json"
    common.save_json(out, email)
    print(common.dumps({"out": common.rel(out), "subject": email["subject"],
                        "attachments": len(email["attachments"]), "total_minutes": email["meta"]["total_minutes"]}))
    return 0


if __name__ == "__main__":
    common.run_cli(main)
