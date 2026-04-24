"""Consolidate — merge loose notes into a tidy, non-destructive playbook.

Algorithm: ACE grow-and-refine + dream-skill's 4-phase (ORIENT / GATHER /
CONSOLIDATE / PRUNE-INDEX). Unlike Mem0's A.U.D.N., we never DELETE — we mark
entries as ``superseded_by`` and let them age out.

Two-step interface:
    prepare(ctx) -> {"prompt": str, "context_files": [...], "stats": {...}}
    apply(ctx, llm_response: dict) -> {"added": N, "superseded": N, "evicted": N}

The LLM response schema is documented in ``core/prompts/consolidate.md``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from core.schema import MemoryEntry, Playbook
from core.schema.memory import TOPICS


MIN_HOURS_BETWEEN_RUNS = 24
MIN_NEW_SESSIONS = 5
EVICT_SCORE_THRESHOLD = -3


@dataclass
class ConsolidateContext:
    hypha_root: Path
    project: str
    dry_run: bool = False

    @property
    def memory_dir(self) -> Path:
        return self.hypha_root / "memory" / self.project

    @property
    def last_dream_file(self) -> Path:
        return self.memory_dir / ".last-dream"


def _load_prompt() -> str:
    here = Path(__file__).resolve().parent.parent / "prompts" / "consolidate.md"
    return here.read_text(encoding="utf-8")


def prepare(ctx: ConsolidateContext) -> dict:
    """Phase 1+2: read current playbook + recent sessions, return prompt payload."""
    ctx.memory_dir.mkdir(parents=True, exist_ok=True)

    topic_files = {t: (ctx.memory_dir / f"{t}.md") for t in TOPICS}
    current = {
        t: p.read_text(encoding="utf-8") if p.exists() else ""
        for t, p in topic_files.items()
    }

    return {
        "prompt": _load_prompt(),
        "current_playbook": current,
        "project": ctx.project,
        "instructions": (
            "Read the current playbook and recent session transcripts. "
            "Propose ADD operations for new insights, and SUPERSEDE operations "
            "for entries that are now contradicted. NEVER propose DELETE."
        ),
    }


def apply(ctx: ConsolidateContext, response: dict) -> dict:
    """Phase 3+4: apply the LLM's proposed operations and regenerate MEMORY.md index."""
    stats = {"added": 0, "superseded": 0, "evicted": 0}

    if ctx.dry_run:
        stats["dry_run"] = True
        stats["would_apply"] = response.get("operations", [])
        return stats

    playbook = _load_playbook(ctx)
    for op in response.get("operations", []):
        match op.get("type"):
            case "ADD":
                topic = op["topic"]
                entry = MemoryEntry(
                    id=playbook.next_id(topic),
                    topic=topic,
                    text=op["text"],
                    created=_parse_date(op.get("date")),
                    source=op.get("source", ""),
                )
                playbook.entries.append(entry)
                stats["added"] += 1
            case "SUPERSEDE":
                for e in playbook.entries:
                    if e.id == op["target_id"]:
                        e.superseded_by = op.get("new_id", "")
                        stats["superseded"] += 1

    # ACE's grow-and-refine eviction: any entry with helpful-harmful <= -3 ages out
    for e in playbook.entries:
        if (e.helpful - e.harmful) <= EVICT_SCORE_THRESHOLD:
            e.superseded_by = e.superseded_by or "evicted-by-score"
            stats["evicted"] += 1

    _write_playbook(ctx, playbook)
    return stats


def _load_playbook(ctx: ConsolidateContext) -> Playbook:
    # TODO(parse): read back entries from the topic .md files
    # For MVP, start from empty and accumulate via ADD.
    return Playbook(root=ctx.memory_dir, entries=[])


def _write_playbook(ctx: ConsolidateContext, playbook: Playbook) -> None:
    ctx.memory_dir.mkdir(parents=True, exist_ok=True)
    for topic in TOPICS:
        entries = [e for e in playbook.entries if e.topic == topic]
        if not entries:
            continue
        lines = [f"# {topic}\n"]
        lines.extend(e.render() for e in entries)
        (ctx.memory_dir / f"{topic}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Index (MEMORY.md) is safe to fully rewrite — it's an index, not a source of truth.
    index = ["# Memory index", ""]
    for topic in TOPICS:
        f = ctx.memory_dir / f"{topic}.md"
        if f.exists():
            count = sum(1 for _ in f.read_text(encoding="utf-8").splitlines() if _.startswith("- "))
            index.append(f"- [{topic}]({topic}.md) — {count} entries")
    (ctx.memory_dir / "MEMORY.md").write_text("\n".join(index) + "\n", encoding="utf-8")


def _parse_date(s: str | None) -> "date":
    from datetime import date, datetime
    if not s:
        return date.today()
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        return date.today()
