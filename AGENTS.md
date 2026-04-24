# AGENTS.md

> Hypha itself follows the [AGENTS.md](https://agents.md) convention. This file is the
> single source of truth for any AI agent working on this repository.

## Project

**Hypha** — a shared, evolving playbook for AI coding agents. Monorepo with a neutral
`core/` and thin `adapters/` per agent (Claude Code, Codex, Cursor, OpenClaw).

## Golden rules

1. **Never let an LLM DELETE memory entries.** Procedural memory (grep checklists,
   review rules) must only be added, marked, or archived — never silently removed.
   Rationale: Mem0's A.U.D.N. model is tuned for personal facts, not for hand-crafted
   playbooks. See `docs/adr/001-no-llm-delete.md`.
2. **Core is language-agnostic.** Algorithms in `core/algo/` must not shell out to a
   specific agent CLI. Adapters own the "how to invoke an LLM" concern.
3. **Every hook must be idempotent.** A user may invoke `hypha consolidate` twice in
   a row; the second run must be a no-op if nothing has changed.
4. **No vector database in the default path.** Grep + descriptions are enough under
   ~200 skills. Add embeddings as an optional backend, never as a hard dependency.
5. **All prompts live in `core/prompts/*.md`** and are loaded at runtime. Do not
   inline prompts in `.py` files — they must be diffable and translatable.

## Directory map

```
core/         # language-agnostic algorithms + CLI
  schema/     # dataclasses for memory / reflection / skill entries
  algo/       # consolidate, reflect, harvest, guard
  prompts/    # markdown prompt templates
  cli.py      # `hypha <cmd>` entry point
adapters/     # one directory per supported agent
bench/        # tiny smoke tests + SWE-Skills-Bench integration notes
examples/     # end-to-end demos per adapter
```

## Testing

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## When adding a new adapter

1. Create `adapters/<agent>/README.md` describing the agent's lifecycle events.
2. Wire each event to a `hypha <cmd>` call. Adapter code should be a thin shell.
3. Add an end-to-end example under `examples/<agent>/`.
4. Do not modify `core/` to accommodate a single adapter — if `core/` can't express
   what you need, open an issue first.

## Style

- Python 3.10+ (`match` statements allowed).
- No comments that restate the code.
- Error messages must tell the user what to do next, not just what went wrong.
