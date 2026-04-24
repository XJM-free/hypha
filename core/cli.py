"""Hypha CLI entry point.

    hypha init                          — set up ~/.hypha/ for a project
    hypha consolidate [--dry-run]       — merge loose notes into playbook
    hypha reflect --trajectory FILE     — write a reflection for a failed session
    hypha harvest --trajectory FILE     — extract a skill from a successful session
    hypha guard --bench FILE            — run the tiny benchmark; exit 2 if regressed
    hypha inbox                         — list skills awaiting review
    hypha inbox approve <name>          — move a skill from inbox to active
    hypha inbox reject <name>           — move a skill from inbox to .rejected

Every command that needs an LLM supports two modes:
  1. Two-step:   ``hypha <cmd> prepare`` outputs a JSON prompt to stdout; after
     you invoke your preferred LLM CLI and save the response, run
     ``hypha <cmd> apply < response.json``.
  2. One-step:   ``hypha <cmd> --llm "claude -p --bare --setting-sources ''"``
     pipes for you. Adapter shell scripts use this form.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


DEFAULT_HYPHA_ROOT = Path(os.environ.get("HYPHA_ROOT", Path.home() / ".hypha"))


def _project_name(cwd: Path | None = None) -> str:
    cwd = cwd or Path.cwd()
    return cwd.name.replace(" ", "-").lower() or "default"


def cmd_init(args: argparse.Namespace) -> int:
    root: Path = args.root
    project = args.project or _project_name()
    for sub in ("memory", "skills", "reflections", "bench"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    (root / "memory" / project).mkdir(parents=True, exist_ok=True)
    print(f"Initialized Hypha at {root} for project '{project}'.")
    return 0


def cmd_consolidate(args: argparse.Namespace) -> int:
    from core.algo.consolidate import ConsolidateContext, prepare, apply

    ctx = ConsolidateContext(
        hypha_root=args.root,
        project=args.project or _project_name(),
        dry_run=args.dry_run,
    )

    if args.mode == "prepare":
        print(json.dumps(prepare(ctx), indent=2, ensure_ascii=False, default=str))
        return 0

    if args.mode == "apply":
        data = json.load(sys.stdin)
        stats = apply(ctx, data)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return 0

    # default: run both, requires --llm
    if not args.llm:
        print("error: one-step mode requires --llm <command>", file=sys.stderr)
        return 2
    payload = prepare(ctx)
    response = _invoke_llm(args.llm, json.dumps(payload, ensure_ascii=False, default=str))
    stats = apply(ctx, response)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


def cmd_reflect(args: argparse.Namespace) -> int:
    from core.algo.reflect import ReflectContext, prepare, apply

    trajectory = _read_trajectory(args.trajectory)
    ctx = ReflectContext(
        hypha_root=args.root,
        project=args.project or _project_name(),
        session_id=args.session_id or "unknown",
        trajectory=trajectory,
        failure_signal=args.signal or "",
    )

    if args.mode == "prepare":
        print(json.dumps(prepare(ctx), indent=2, ensure_ascii=False))
        return 0
    if args.mode == "apply":
        data = json.load(sys.stdin)
        reflection = apply(ctx, data)
        print(reflection.to_jsonl())
        return 0
    if not args.llm:
        print("error: one-step mode requires --llm <command>", file=sys.stderr)
        return 2
    payload = prepare(ctx)
    response = _invoke_llm(args.llm, json.dumps(payload, ensure_ascii=False))
    reflection = apply(ctx, response)
    print(reflection.to_jsonl())
    return 0


def cmd_harvest(args: argparse.Namespace) -> int:
    from core.algo.harvest import HarvestContext, prepare, apply

    trajectory = _read_trajectory(args.trajectory)
    ctx = HarvestContext(
        hypha_root=args.root,
        project=args.project or _project_name(),
        session_id=args.session_id or "unknown",
        trajectory=trajectory,
        diff=args.diff or "",
    )

    if args.mode == "prepare":
        print(json.dumps(prepare(ctx), indent=2, ensure_ascii=False))
        return 0
    if args.mode == "apply":
        data = json.load(sys.stdin)
        skill = apply(ctx, data)
        print(f"inbox: {skill.name if skill else '(nothing harvested)'}")
        return 0
    if not args.llm:
        print("error: one-step mode requires --llm <command>", file=sys.stderr)
        return 2
    payload = prepare(ctx)
    response = _invoke_llm(args.llm, json.dumps(payload, ensure_ascii=False))
    skill = apply(ctx, response)
    print(f"inbox: {skill.name if skill else '(nothing harvested)'}")
    return 0


def cmd_guard(args: argparse.Namespace) -> int:
    from core.algo.guard import GuardContext, evaluate

    ctx = GuardContext(
        hypha_root=args.root,
        bench_file=args.bench,
        baseline_file=args.baseline,
    )

    if not args.llm:
        print("error: guard requires --llm <command>", file=sys.stderr)
        return 2

    def run_one(prompt: str) -> str:
        return _invoke_llm_text(args.llm, prompt)

    result = evaluate(ctx, run_one)
    print(json.dumps({
        "passed": result.passed,
        "total": result.total,
        "score": round(result.score, 4),
        "baseline": round(result.baseline, 4),
        "delta": round(result.delta, 4),
        "regressed": result.regressed,
    }, indent=2))
    return 2 if result.regressed else 0


def cmd_inbox(args: argparse.Namespace) -> int:
    from core.algo.harvest import list_inbox, approve, reject

    match args.action:
        case "approve":
            if not args.name:
                print("error: inbox approve <name>", file=sys.stderr)
                return 2
            dst = approve(args.root, args.name)
            print(f"approved: {dst}")
        case "reject":
            if not args.name:
                print("error: inbox reject <name>", file=sys.stderr)
                return 2
            reject(args.root, args.name)
            print(f"rejected: {args.name}")
        case _:
            items = list_inbox(args.root)
            if not items:
                print("(inbox empty)")
                return 0
            for p in items:
                desc_file = p / ".desc"
                desc = desc_file.read_text().strip() if desc_file.exists() else ""
                print(f"{p.name}\t{desc}")
    return 0


def _read_trajectory(path: Path | None) -> list[dict]:
    if not path:
        return []
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    # Accept either JSONL (one message per line) or a single JSON array.
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _invoke_llm(cmd: str, prompt: str) -> dict:
    text = _invoke_llm_text(cmd, prompt)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract a fenced JSON block.
        import re
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        raise


def _invoke_llm_text(cmd: str, prompt: str) -> str:
    import shlex
    import subprocess
    args = shlex.split(cmd)
    result = subprocess.run(
        args,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"LLM invocation failed ({result.returncode}): {result.stderr}")
    return result.stdout


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hypha",
        description="The mycelial network beneath your agents.",
    )
    p.add_argument("--root", type=Path, default=DEFAULT_HYPHA_ROOT,
                   help=f"Hypha data root (default: {DEFAULT_HYPHA_ROOT})")
    p.add_argument("--project", help="project name (defaults to basename of cwd)")

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="set up the Hypha data directory").set_defaults(func=cmd_init)

    pc = sub.add_parser("consolidate", help="merge notes into playbook")
    pc.add_argument("mode", nargs="?", default="run", choices=["run", "prepare", "apply"])
    pc.add_argument("--llm", help='LLM command, e.g. "claude -p --bare --setting-sources \'\'"')
    pc.add_argument("--dry-run", action="store_true")
    pc.set_defaults(func=cmd_consolidate)

    pr = sub.add_parser("reflect", help="write a reflection for a failed session")
    pr.add_argument("mode", nargs="?", default="run", choices=["run", "prepare", "apply"])
    pr.add_argument("--trajectory", type=Path, help="session trajectory file (JSONL or JSON array)")
    pr.add_argument("--session-id")
    pr.add_argument("--signal", help="short description of the failure")
    pr.add_argument("--llm")
    pr.set_defaults(func=cmd_reflect)

    ph = sub.add_parser("harvest", help="extract a skill from a successful session")
    ph.add_argument("mode", nargs="?", default="run", choices=["run", "prepare", "apply"])
    ph.add_argument("--trajectory", type=Path)
    ph.add_argument("--session-id")
    ph.add_argument("--diff", help="inline diff string or path")
    ph.add_argument("--llm")
    ph.set_defaults(func=cmd_harvest)

    pg = sub.add_parser("guard", help="run the tiny benchmark; exit 2 on regression")
    pg.add_argument("--bench", type=Path, default=Path("bench/tiny.jsonl"))
    pg.add_argument("--baseline", type=Path, default=Path("bench/baseline_score"))
    pg.add_argument("--llm", required=True)
    pg.set_defaults(func=cmd_guard)

    pi = sub.add_parser("inbox", help="review harvested skills")
    pi.add_argument("action", nargs="?", default="list", choices=["list", "approve", "reject"])
    pi.add_argument("name", nargs="?")
    pi.set_defaults(func=cmd_inbox)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
