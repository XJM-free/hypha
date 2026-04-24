"""Read-only queries over a Hypha data directory.

Powers ``hypha stats``, ``hypha search``, and ``hypha show``. None of these
commands need an LLM — they're pure local filesystem reads.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.schema.memory import MemoryEntry, Playbook, TOPICS


@dataclass
class ProjectStats:
    name: str
    entries_by_topic: dict[str, int]
    total_active: int
    total_superseded: int

    @property
    def total(self) -> int:
        return self.total_active + self.total_superseded


def project_stats(memory_root: Path) -> list[ProjectStats]:
    if not memory_root.exists():
        return []
    out: list[ProjectStats] = []
    for project_dir in sorted(memory_root.iterdir()):
        if not project_dir.is_dir():
            continue
        pb = Playbook.load(project_dir)
        by_topic = {t: 0 for t in TOPICS}
        active = superseded = 0
        for e in pb.entries:
            by_topic[e.topic] = by_topic.get(e.topic, 0) + 1
            if e.superseded_by:
                superseded += 1
            else:
                active += 1
        out.append(ProjectStats(
            name=project_dir.name,
            entries_by_topic=by_topic,
            total_active=active,
            total_superseded=superseded,
        ))
    return out


def count_dir(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob(pattern))


@dataclass
class SearchHit:
    project: str
    entry: MemoryEntry
    score: int  # crude relevance — count of query-term matches


def search(memory_root: Path, query: str, limit: int = 20) -> list[SearchHit]:
    if not memory_root.exists():
        return []
    terms = [t.lower() for t in query.split() if t.strip()]
    if not terms:
        return []

    hits: list[SearchHit] = []
    for project_dir in memory_root.iterdir():
        if not project_dir.is_dir():
            continue
        pb = Playbook.load(project_dir)
        for e in pb.entries:
            hay = f"{e.text} {e.source}".lower()
            score = sum(hay.count(t) for t in terms)
            if score > 0:
                hits.append(SearchHit(project=project_dir.name, entry=e, score=score))

    hits.sort(key=lambda h: (-h.score, h.project, h.entry.id))
    return hits[:limit]


def find_entry(memory_root: Path, entry_id: str) -> tuple[str, MemoryEntry] | None:
    for project_dir in memory_root.iterdir():
        if not project_dir.is_dir():
            continue
        pb = Playbook.load(project_dir)
        for e in pb.entries:
            if e.id == entry_id:
                return project_dir.name, e
    return None
