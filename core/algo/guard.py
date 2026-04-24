"""Guard — fitness-gated self-modification.

Before applying any change to the playbook, skills, or hooks themselves, run a
tiny benchmark and compare against the baseline. Regression beyond
``noise_leeway`` triggers a rollback — exactly DGM's ``keep_better`` strategy,
minus the Docker sandbox (we rely on git instead).

The benchmark format is intentionally simple so users can maintain their own:
    bench/tiny.jsonl:  one JSON object per line, each:
        {"prompt": "...", "expected_substring": "..."}
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_NOISE_LEEWAY = 0.1


@dataclass
class GuardResult:
    passed: int
    total: int
    score: float
    baseline: float
    noise_leeway: float
    regressed: bool

    @property
    def delta(self) -> float:
        return self.score - self.baseline


@dataclass
class GuardContext:
    hypha_root: Path
    bench_file: Path
    baseline_file: Path


def load_bench(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_baseline(path: Path) -> float:
    if not path.exists():
        return 0.0
    try:
        return float(path.read_text().strip())
    except ValueError:
        return 0.0


def evaluate(ctx: GuardContext, run_one: callable) -> GuardResult:
    """Run the bench. ``run_one`` is an adapter-provided callable:
        run_one(prompt: str) -> str    # the LLM's full response
    """
    cases = load_bench(ctx.bench_file)
    passed = 0
    for case in cases:
        try:
            out = run_one(case["prompt"])
        except Exception:
            out = ""
        if case["expected_substring"] in out:
            passed += 1

    total = len(cases) or 1
    score = passed / total
    baseline = load_baseline(ctx.baseline_file)
    regressed = score < (baseline - DEFAULT_NOISE_LEEWAY)

    return GuardResult(
        passed=passed,
        total=total,
        score=score,
        baseline=baseline,
        noise_leeway=DEFAULT_NOISE_LEEWAY,
        regressed=regressed,
    )


def update_baseline(ctx: GuardContext, result: GuardResult) -> None:
    ctx.baseline_file.write_text(f"{result.score:.4f}\n", encoding="utf-8")
