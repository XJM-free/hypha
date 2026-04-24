"""Reflection schema — combines Agent-R's trajectory verifier and Reflexion's verbal reflection.

A Reflection is what we write after a failed session. It answers:
1. Where did it go wrong? (Agent-R's ``first_bad_step_index``)
2. Why? (``root_cause``)
3. What to do next time? (``reflection``)
4. Can this be generalized into a rule? (``reusable_lesson``; may be empty)
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass
class Reflection:
    first_bad_step_index: int
    root_cause: str
    reflection: str
    reusable_lesson: str = ""
    session_id: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, data: dict) -> "Reflection":
        return cls(
            first_bad_step_index=int(data["first_bad_step_index"]),
            root_cause=data["root_cause"],
            reflection=data["reflection"],
            reusable_lesson=data.get("reusable_lesson", ""),
            session_id=data.get("session_id", ""),
            timestamp=data.get("timestamp", ""),
        )
