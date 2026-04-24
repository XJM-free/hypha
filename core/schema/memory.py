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

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


TOPICS = ("preferences", "decisions", "corrections", "patterns", "facts")


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

    def next_id(self, topic: str) -> str:
        existing = [e.id for e in self.entries if e.topic == topic]
        n = len(existing)
        return f"{topic[:4]}-{n + 1:05d}"
