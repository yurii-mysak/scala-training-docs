"""Shared test fixtures: a minimal fixture repo in a temp dir plus helpers to write lessons.

The engine finds its repo root through $DOJO_REPO (falling back to the script's own location), so each
test points that variable at its own temp copy.  $DOJO_NOW pins "now" for reproducible timestamps.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import common  # noqa: E402  (needs the sys.path line above)

NOW = "2026-10-06T06:00:00Z"


def tiny_png(w: int = 200, h: int = 100) -> bytes:
    """A valid white PNG of the given size (so email tests do not need mmdc)."""
    import struct
    import zlib

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + b"\xff\xff\xff" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


# --------------------------------------------------------------------------- fixture curriculum


def make_rung(track: str, n: int, level: str = "B", prereqs: list[str] | None = None,
              title: str | None = None, **extra) -> dict:
    r = {
        "id": f"{track}-{n:02d}",
        "title": title or f"{track} lesson {n}",
        "level": level,
        "est_min": 20,
        "prereqs": prereqs or [],
        "summary": f"Summary of {track} rung {n}. It teaches one idea.",
        "key_points": [f"{track} point {n}.1", f"{track} point {n}.2", f"{track} point {n}.3"],
        "diagram": f"A diagram of {track} {n}.",
        "example": f"A tiny example for {track} {n}.",
        "presentation": "minimal",
        "sources": [{"title": f"Source for {track} {n}", "url": f"https://example.com/{track}/{n}",
                     "locator": "ch. 1", "kind": "book"}],
    }
    r.update(extra)
    return r


def make_track(key: str, weight: int, files_to: str, rungs: list[dict], name: str | None = None) -> dict:
    return {"track": key, "name": name or key, "weight": weight, "files_to": files_to,
            "description": f"The {key} ladder.", "primary_sources": [{"title": "Book", "url": "https://example.com"}],
            "rungs": rungs}


def default_tracks() -> list[dict]:
    """Two tracks, three rungs each, one cross-track prerequisite (ai-ml-02 needs networking-01)."""
    return [
        make_track("ai-ml", 2, "24-ai-ml-foundations", [
            make_rung("ai-ml", 1, "B", title="What machine learning actually optimises"),
            make_rung("ai-ml", 2, "I", ["networking-01"], title="Gradient descent by hand"),
            make_rung("ai-ml", 3, "A", title="Attention from scratch"),
        ], name="AI / ML foundations"),
        make_track("networking", 1, "10-networking", [
            make_rung("networking", 1, "B", title="Network models"),
            make_rung("networking", 2, "I", title="DNS resolution"),
            make_rung("networking", 3, "A", ["networking-02"], title="TLS 1.3 handshake"),
        ], name="Networking"),
    ]


def six_tracks() -> list[dict]:
    """Weights 5/3/3/2/2/1 (SPEC §1), six rungs each, no prerequisites."""
    spec = [("ai-ml", 5), ("fp-scala", 3), ("ddia", 3), ("architecture", 2), ("networking", 2), ("rust", 1)]
    return [make_track(k, w, f"{i + 1:02d}-{k}", [make_rung(k, n, "BBIIAA"[n - 1]) for n in range(1, 7)])
            for i, (k, w) in enumerate(spec)]


# --------------------------------------------------------------------------- fixture READMEs

NETWORKING_README = """\
# Networking

Network models, protocols, addressing, DNS, routing, and transport security.

## Beginner

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 1 | Network models | [Networking-Network-Models.md](Networking-Network-Models.md) | OSI 7 layers, TCP/IP 4 layers, encapsulation |
| 2 | IP addressing | [Networking-IP-Addressing.md](Networking-IP-Addressing.md) | IPv4, CIDR notation, subnetting |

## Intermediate

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 3 | DNS & DHCP | [Networking-DNS-DHCP.md](Networking-DNS-DHCP.md) | DNS resolution, record types, DHCP lease process |

## Advanced

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 4 | HTTPS & TLS | [Networking-HTTPS-TLS.md](Networking-HTTPS-TLS.md) | TLS handshake, certificates, cipher suites, mTLS |

## Key Interview Questions by Level

**Beginner**: What are the OSI layers?

**Intermediate**: How does DNS resolution work?

**Advanced**: Explain the TLS 1.3 handshake.
"""

ROOT_README = """\
# Scala & Backend Engineering — Training & Interview Guide

**Levels**: B = Beginner | I = Intermediate | A = Advanced

---

## Infrastructure & Operations

### [10 — Networking](10-networking/)
| Level | Topics |
|-------|--------|
| B | [Network Models](10-networking/Networking-Network-Models.md), [IP Addressing](10-networking/Networking-IP-Addressing.md) |
| I | [DNS & DHCP](10-networking/Networking-DNS-DHCP.md) |

---

## Domain-Specific

### [16 — AdTech](16-adtech/)
| Level | Topics |
|-------|--------|
| I | [OpenRTB Protocol](16-adtech/openrtb.md) |
| A | [High-Scale Bidding Engine](16-adtech/bidding.md) |
"""

# --------------------------------------------------------------------------- lesson bodies

LESSON_BODY = """\
# {title}

> {track} · {level_name} · ~20 min · rung 1 of 3 · needs: —

## Why this matters
Machine learning is optimisation, and this lesson shows what is optimised. It sits first on the ladder.

## The idea
A loss turns "wrong" into a number (Goodfellow, Deep Learning ch. 5, "Machine Learning Basics").

```mermaid
flowchart LR
  A[Data] --> B[Model] --> C[Loss]
```

> "The loss is the number we try to make small." — Some Author, *A Blog Post*, 2024-05-01, https://example.com/post

| Term | Meaning |
|------|---------|
| loss | error as one number |

## Worked example
```python
loss = (3 - 2) ** 2
print(loss)
```

## Self-check
1. What does a loss measure? <details><summary>Answer</summary>How wrong the model is.</details>
2. Why a single number? <details><summary>Answer</summary>So it can be minimised.</details>
3. Is lower better? <details><summary>Answer</summary>Yes, usually.</details>

## Sources
- [A Blog Post](https://example.com/post) — contributed the quote; accessed 2026-10-06

## Next on this track
Next on AI / ML foundations: **Gradient descent by hand** (rung 2 of 3, Intermediate).
"""


def lesson_body(title: str = "A lesson", track: str = "AI / ML foundations", level: str = "B") -> str:
    return LESSON_BODY.format(title=title, track=track, level_name=common.level_name(level))


# --------------------------------------------------------------------------- base class

class RepoTestCase(unittest.TestCase):
    """Creates a fixture repo in a temp dir and points the engine at it for the duration of a test."""

    tracks_factory = staticmethod(default_tracks)
    with_readmes = True

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="dojo-test-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.enterContext(mock.patch.dict(os.environ, {"DOJO_REPO": str(self.root), "DOJO_NOW": NOW}))
        (self.root / "dojo" / "curriculum").mkdir(parents=True)
        for t in self.tracks_factory():
            common.save_yaml(self.root / "dojo" / "curriculum" / f"{t['track']}.yaml", t)
        (self.root / "dojo" / "lessons").mkdir(parents=True)
        (self.root / "dojo" / "progress").mkdir(parents=True)
        if self.with_readmes:
            self.write("10-networking/README.md", NETWORKING_README)
            self.write("README.md", ROOT_README)

    # ---- file helpers
    def write(self, rel: str, text: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def exists(self, rel: str) -> bool:
        return (self.root / rel).exists()

    def log_events(self) -> list[dict]:
        p = self.root / "dojo" / "progress" / "log.jsonl"
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []

    def state(self) -> dict:
        return json.loads((self.root / "dojo" / "progress" / "state.json").read_text(encoding="utf-8"))

    def add_lesson(self, lesson_id: str, rung: str | None = None, *, status: str = "sent", slot: str = "core",
                   track: str | None = None, level: str = "B", title: str | None = None,
                   sent_at: str | None = None, marked_at: str | None = None, files_to: str | None = None,
                   body: str | None = None, **fm_extra) -> Path:
        """Write a lesson file directly (bypasses the picker) and return its path."""
        date = lesson_id.rsplit("-", 1)[0]
        track = track or (rung.rsplit("-", 1)[0] if rung else "fresh")
        title = title or f"Lesson {lesson_id}"
        if files_to is None:
            files_to = {"ai-ml": "24-ai-ml-foundations", "networking": "10-networking"}.get(
                track if track != "fresh" else fm_extra.get("domain", ""), "24-ai-ml-foundations")
        fm = {"id": lesson_id, "date": date, "slot": slot, "track": track, "domain": fm_extra.pop("domain", track),
              "rung": rung, "level": level, "title": title, "est_min": 20, "files_to": files_to,
              "status": status, "sent_at": sent_at or f"{date}T06:00:00Z", "marked_at": marked_at,
              "filed_to": None, "review_due": None,
              "sources": [{"title": "A Blog Post", "url": "https://example.com/post"}]}
        fm.update(fm_extra)
        slug = common.slugify(title)
        path = self.root / "dojo" / "lessons" / f"{lesson_id}-{slug}.md"
        common.save_lesson(path, fm, body if body is not None else lesson_body(title, level=level))
        return path

    def lesson_fm(self, lesson_id: str) -> dict:
        return common.load_lesson(common.find_lesson_path(lesson_id))[0]

    # ---- CLI helpers
    @staticmethod
    def run_main(main, argv: list[str]) -> tuple[int, str, str]:
        """Call a script's main(argv) in-process, returning (rc, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = main(argv)
        return rc or 0, out.getvalue(), err.getvalue()
