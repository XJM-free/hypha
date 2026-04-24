"""Memory entry schema — aligned with ACE's bullet format and dream-skill's topic files.

Design:
- Every entry has a stable id (``<topic>-NNNNN``) so future runs can reference
  it without relying on text matching.
- ``helpful`` / ``harmful`` counters come from ACE — they let us evict useless
  entries without an LLM judging their "truth".
- ``superseded_by`` is how we handle updates **without** deleting. The old entry
  stays readable; the new one links back.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


TOPICS = ("preferences", "decisions", "corrections", "patterns", "facts")

# Matches a rendered MemoryEntry:
#   - [YYYY-MM-DD] text here (id=pref-00001 helpful=3 harmful=0 source=...)
_ENTRY_RE = re.compile(r"^- \[(\d{4}-\d{2}-\d{2})\] (.+?) \(([^)]*)\)\s*$")
_TOPIC_PREFIX = {t: t[:4] for t in TOPICS}


@dataclass
class MemoryEntry:
    id: str
    topic: str
    text: str
    created: date
    source: str = ""
    helpful: int = 0
    harmful: int = 0
    superseded_by: str | None = None
    confidence: str = "medium"

    def render(self) -> str:
        """Render as a single Markdown bullet.

        Format (kept grep-friendly):
            - [2026-04-24] <text> (id=pref-00012 helpful=3 harmful=0 source=session-abc)
        """
        tail = f"id={self.id} helpful={self.helpful} harmful={self.harmful}"
        if self.source:
            tail += f" source={self.source}"
        if self.superseded_by:
            tail += f" superseded_by={self.superseded_by}"
        return f"- [{self.created.isoformat()}] {self.text} ({tail})"


@dataclass
class Playbook:
    """A collection of memory entries grouped by topic, backed by a directory of .md files."""

    root: Path
    entries: list[MemoryEntry] = field(default_factory=list)

    def by_topic(self, topic: str) -> list[MemoryEntry]:
        return [e for e in self.entries if e.topic == topic and not e.superseded_by]

    def by_source(self, source: str) -> MemoryEntry | None:
        for e in self.entries:
            if e.source == source:
                return e
        return None

    def next_id(self, topic: str) -> str:
        prefix = _TOPIC_PREFIX.get(topic, topic[:4])
        used = set()
        for e in self.entries:
            if e.id.startswith(f"{prefix}-"):
                try:
                    used.add(int(e.id.split("-", 1)[1]))
                except ValueError:
                    pass
        n = 1
        while n in used:
            n += 1
        return f"{prefix}-{n:05d}"

    @classmethod
    def load(cls, root: Path) -> "Playbook":
        """Parse topic .md files under ``root`` back into a Playbook.

        Format is the output of :meth:`MemoryEntry.render`. Lines that don't
        match are silently skipped — user-edited sections don't break loads.
        """
        pb = cls(root=root)
        for topic in TOPICS:
            f = root / f"{topic}.md"
            if not f.exists():
                continue
            for line in f.read_text(encoding="utf-8").splitlines():
                entry = _parse_entry_line(line, topic)
                if entry is not None:
                    pb.entries.append(entry)
        return pb


def _parse_entry_line(line: str, topic: str) -> MemoryEntry | None:
    m = _ENTRY_RE.match(line)
    if not m:
        return None
    date_str, text, tail = m.group(1), m.group(2), m.group(3)
    meta: dict[str, str] = {}
    for part in tail.split():
        if "=" in part:
            k, _, v = part.partition("=")
            meta[k] = v
    try:
        created = date.fromisoformat(date_str)
    except ValueError:
        return None
    return MemoryEntry(
        id=meta.get("id", f"{_TOPIC_PREFIX.get(topic, topic[:4])}-00000"),
        topic=topic,
        text=text,
        created=created,
        source=meta.get("source", ""),
        helpful=int(meta.get("helpful", 0)),
        harmful=int(meta.get("harmful", 0)),
        superseded_by=meta.get("superseded_by") or None,
        confidence=meta.get("confidence", "medium"),
    )
