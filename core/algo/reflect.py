"""Reflect — on failure, locate the first bad step and write a structured lesson.

Algorithm: Agent-R's verifier prompt (locate ``first_bad_step_index``) + Reflexion's
verbal self-reflection (natural-language ``reflection`` + ``reusable_lesson``).

Input is a trajectory (a list of {role, content} messages) plus the failure
signal (exit code, stderr, user correction). Output is a ``Reflection`` that
gets appended to ``~/.hypha/reflections/<project>/<timestamp>.jsonl``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.schema.reflection import Reflection


@dataclass
class ReflectContext:
    hypha_root: Path
    project: str
    session_id: str
    trajectory: list[dict[str, Any]]
    failure_signal: str = ""


def _load_prompt() -> str:
    here = Path(__file__).resolve().parent.parent / "prompts" / "reflect.md"
    return here.read_text(encoding="utf-8")


def prepare(ctx: ReflectContext) -> dict:
    tail = ctx.trajectory[-40:]  # last 40 turns; older context rarely helps
    return {
        "prompt": _load_prompt(),
        "trajectory": tail,
        "failure_signal": ctx.failure_signal,
        "session_id": ctx.session_id,
        "expected_output_schema": {
            "first_bad_step_index": "int (0-based into trajectory)",
            "root_cause": "one sentence",
            "reflection": "3-5 sentences on why it failed and what to try next",
            "reusable_lesson": "optional one-liner rule-of-thumb; empty string if none",
        },
    }


def apply(ctx: ReflectContext, response: dict) -> Reflection:
    reflection = Reflection.from_json({**response, "session_id": ctx.session_id})

    out_dir = ctx.hypha_root / "reflections" / ctx.project
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{reflection.timestamp.replace(':', '-')}.jsonl"
    out_file.write_text(reflection.to_jsonl() + "\n", encoding="utf-8")

    # Reusable lessons also go into a global file for cross-project consumption.
    if reflection.reusable_lesson:
        lessons = ctx.hypha_root / "memory" / "global_lessons.md"
        lessons.parent.mkdir(parents=True, exist_ok=True)
        with lessons.open("a", encoding="utf-8") as f:
            f.write(f"- [{reflection.timestamp[:10]}] {reflection.reusable_lesson} "
                    f"(source: {ctx.project}/{ctx.session_id})\n")

    return reflection
