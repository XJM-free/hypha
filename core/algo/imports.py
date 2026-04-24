"""Import existing memory directories from other tools into Hypha.

Currently supported sources:
    claude-code-memory  — Anthropic Claude Code's project memory directories
                          (``~/.claude/projects/<project>/memory/*.md``)

The import is **non-destructive**: source files stay where they are. Each file
becomes one ``MemoryEntry`` whose ``source`` field points to the original path,
so Hypha can surface the description in MEMORY.md while letting you open the
full document on demand.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from core.schema.memory import MemoryEntry, Playbook


# Claude Code's memory frontmatter uses a ``type`` field; we map each value to
# one of Hypha's five topics. Unknown types land in ``facts``.
TYPE_TO_TOPIC = {
    "feedback": "corrections",
    "project": "decisions",
    "reference": "facts",
    "user": "preferences",
}


@dataclass
class ImportContext:
    hypha_root: Path
    project: str
    source_dir: Path
    include_globs: tuple[str, ...] = ("*.md",)
    exclude_names: tuple[str, ...] = ("MEMORY.md",)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse ``--- ... ---`` frontmatter at the top of a Markdown document.

    Kept dependency-free on purpose: we only support ``key: value`` lines with
    string values, which is all Claude Code's memory files use. Returns
    ``(frontmatter_dict, body_without_frontmatter)``.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    fm: dict[str, str] = {}
    end = -1
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")

    if end == -1:
        return {}, text
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return fm, body


def run(ctx: ImportContext) -> dict:
    """Import every matching file under ``source_dir`` into the playbook.

    Returns a stats dict suitable for printing.
    """
    if not ctx.source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {ctx.source_dir}")

    files: list[Path] = []
    for pattern in ctx.include_globs:
        files.extend(ctx.source_dir.glob(pattern))
    files = sorted(f for f in files if f.name not in ctx.exclude_names)

    memory_dir = ctx.hypha_root / "memory" / ctx.project
    memory_dir.mkdir(parents=True, exist_ok=True)

    playbook = Playbook(root=memory_dir)
    stats = {"scanned": len(files), "imported": 0, "skipped_no_frontmatter": 0}

    for f in files:
        text = f.read_text(encoding="utf-8")
        fm, _body = parse_frontmatter(text)
        if not fm:
            stats["skipped_no_frontmatter"] += 1
            continue

        topic = TYPE_TO_TOPIC.get(fm.get("type", "").lower(), "facts")
        created = date.fromtimestamp(f.stat().st_mtime) if hasattr(date, "fromtimestamp") \
            else datetime.fromtimestamp(f.stat().st_mtime).date()

        entry = MemoryEntry(
            id=playbook.next_id(topic),
            topic=topic,
            text=fm.get("description", fm.get("name", f.stem)),
            created=created,
            source=str(f.resolve()),
            confidence="high",
        )
        playbook.entries.append(entry)
        stats["imported"] += 1

    _write_imported(memory_dir, playbook)
    return stats


def _write_imported(memory_dir: Path, playbook: Playbook) -> None:
    from core.schema.memory import TOPICS

    for topic in TOPICS:
        entries = [e for e in playbook.entries if e.topic == topic]
        if not entries:
            continue
        lines = [f"# {topic}\n"]
        lines.extend(e.render() for e in entries)
        (memory_dir / f"{topic}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    index = ["# Memory index", ""]
    for topic in TOPICS:
        f = memory_dir / f"{topic}.md"
        if f.exists():
            count = sum(1 for _ in f.read_text(encoding="utf-8").splitlines() if _.startswith("- "))
            index.append(f"- [{topic}]({topic}.md) — {count} entries")
    (memory_dir / "MEMORY.md").write_text("\n".join(index) + "\n", encoding="utf-8")
