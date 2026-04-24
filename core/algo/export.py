"""Render a Hypha playbook into formats other agents can consume.

Currently supported formats:
    agents-md   — a Markdown block suitable for AGENTS.md (https://agents.md).
                  Idempotent via HYPHA:BEGIN / HYPHA:END sentinels.

The goal is interoperability: even without a dedicated adapter, any agent that
reads AGENTS.md (Codex, Cursor, Aider, Copilot, Jules, Devin, ...) can benefit
from a shared Hypha playbook.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.schema.memory import Playbook, TOPICS


SENTINEL_BEGIN = "<!-- HYPHA:BEGIN - do not edit by hand, run `hypha export agents-md --merge` -->"
SENTINEL_END = "<!-- HYPHA:END -->"

TOPIC_HEADINGS = {
    "preferences": "Preferences",
    "decisions": "Decisions",
    "corrections": "Common corrections (learn from past mistakes)",
    "patterns": "Recurring patterns",
    "facts": "Reference facts",
}


@dataclass
class ExportContext:
    hypha_root: Path
    project: str
    per_topic_limit: int = 30


def render_agents_md(ctx: ExportContext) -> str:
    memory_dir = ctx.hypha_root / "memory" / ctx.project
    pb = Playbook.load(memory_dir)

    lines = [
        SENTINEL_BEGIN,
        "",
        "## Context from Hypha",
        "",
        "Prior sessions learned the following about this project. "
        "Treat these as project conventions.",
        "",
    ]
    for topic in TOPICS:
        entries = [e for e in pb.entries if e.topic == topic and not e.superseded_by]
        if not entries:
            continue
        heading = TOPIC_HEADINGS.get(topic, topic.title())
        lines.append(f"### {heading}")
        lines.append("")
        for e in entries[: ctx.per_topic_limit]:
            lines.append(f"- {e.text}")
        if len(entries) > ctx.per_topic_limit:
            lines.append(f"- _(+{len(entries) - ctx.per_topic_limit} more; "
                        "see ~/.hypha/memory/ or run `hypha search <query>`)_")
        lines.append("")
    lines.append(SENTINEL_END)
    return "\n".join(lines) + "\n"


def merge_into(agents_md_path: Path, new_block: str) -> str:
    """Idempotently update (or append) the Hypha block in an existing AGENTS.md.

    Returns the new full file contents. Does not write to disk — the caller
    decides whether to save it, so a dry-run is trivial.
    """
    if not agents_md_path.exists():
        header = "# AGENTS.md\n\n"
        return header + new_block

    existing = agents_md_path.read_text(encoding="utf-8")
    start = existing.find(SENTINEL_BEGIN)
    end = existing.find(SENTINEL_END)

    if start == -1 or end == -1 or end < start:
        # No prior block — append with a separator.
        sep = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
        return existing + sep + new_block

    before = existing[:start]
    after = existing[end + len(SENTINEL_END):].lstrip("\n")
    return before + new_block + ("\n" + after if after else "")
