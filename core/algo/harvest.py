"""Harvest — on success, extract a reusable skill into an inbox for human review.

Algorithm: Voyager's skill library, simplified. Extraction produces a candidate
skill; a second LLM call (critic) judges generality; only approved drafts land
in ``~/.hypha/skills/`` directly. Everything else goes to the inbox.

Inspired by Gemini CLI's ``/memory inbox`` (2026-04-23): users have mental models
for a review step, and silent auto-ingestion erodes trust.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.schema.skill import Skill


@dataclass
class HarvestContext:
    hypha_root: Path
    project: str
    session_id: str
    trajectory: list[dict[str, Any]]
    diff: str = ""


def _load_prompt() -> str:
    here = Path(__file__).resolve().parent.parent / "prompts" / "harvest.md"
    return here.read_text(encoding="utf-8")


def prepare(ctx: HarvestContext) -> dict:
    return {
        "prompt": _load_prompt(),
        "trajectory": ctx.trajectory[-30:],
        "diff": ctx.diff[:4000],
        "session_id": ctx.session_id,
        "expected_output_schema": {
            "name": "snake_case, <=40 chars; empty string if nothing reusable",
            "description": "one sentence describing when to invoke",
            "body_md": "full SKILL.md body: steps, code blocks, gotchas",
        },
    }


def apply(ctx: HarvestContext, response: dict) -> Skill | None:
    name = (response.get("name") or "").strip()
    if not name:
        return None

    skill = Skill(
        name=name,
        description=response.get("description", ""),
        body=response.get("body_md", ""),
        source_session=ctx.session_id,
        status="inbox",
    )
    inbox = ctx.hypha_root / "skills" / ".inbox"
    skill.write_to(inbox)
    return skill


def list_inbox(hypha_root: Path) -> list[Path]:
    inbox = hypha_root / "skills" / ".inbox"
    if not inbox.exists():
        return []
    return sorted(p for p in inbox.iterdir() if p.is_dir())


def approve(hypha_root: Path, skill_name: str) -> Path:
    src = hypha_root / "skills" / ".inbox" / skill_name
    dst = hypha_root / "skills" / skill_name
    if not src.exists():
        raise FileNotFoundError(f"Skill not in inbox: {skill_name}")
    src.rename(dst)
    return dst


def reject(hypha_root: Path, skill_name: str) -> None:
    src = hypha_root / "skills" / ".inbox" / skill_name
    rejected = hypha_root / "skills" / ".rejected"
    rejected.mkdir(parents=True, exist_ok=True)
    if src.exists():
        src.rename(rejected / skill_name)
