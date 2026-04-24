"""Skill schema — compatible with Anthropic's Agent Skills open standard.

A Skill is a folder containing at minimum:
    <skill_name>/SKILL.md     # frontmatter + body
    <skill_name>/.desc        # one-line trigger description (for grep retrieval)

The frontmatter keys we use are a subset of Anthropic's spec so skills harvested
by Hypha can be dropped into ``~/.claude/skills/`` unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    name: str
    description: str
    body: str
    source_session: str = ""
    status: str = "inbox"  # inbox | approved | rejected | superseded

    def render(self) -> str:
        """Render SKILL.md with frontmatter."""
        return (
            f"---\n"
            f"name: {self.name}\n"
            f'description: "{self.description}"\n'
            f"source_session: {self.source_session}\n"
            f"status: {self.status}\n"
            f"---\n\n"
            f"{self.body}\n"
        )

    def write_to(self, root: Path) -> Path:
        """Write SKILL.md and .desc to root/<name>/ ."""
        folder = root / self.name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "SKILL.md").write_text(self.render(), encoding="utf-8")
        (folder / ".desc").write_text(self.description + "\n", encoding="utf-8")
        return folder
