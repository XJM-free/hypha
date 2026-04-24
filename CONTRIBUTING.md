# Contributing to Hypha

Thanks for thinking about contributing. Hypha is intentionally small — read this first.

## Ground rules

1. **Read [AGENTS.md](AGENTS.md) first.** It encodes the non-obvious design decisions.
2. **No LLM-driven DELETE on memory.** This is not negotiable. See
   [ADR-001](docs/adr/001-no-llm-delete.md) (coming soon) for the full argument.
3. **Core stays language-agnostic.** If your change requires `subprocess.run("claude", ...)`
   inside `core/`, it belongs in an adapter.
4. **Prompts live in `core/prompts/*.md`.** They must be diffable.
5. **Idempotent commands.** Every `hypha <cmd>` must be safe to run twice.

## How to add a new adapter

1. Open an issue first with the agent's lifecycle documentation.
2. Create `adapters/<agent>/README.md` explaining the events and how they map to
   `hypha <cmd>` calls.
3. Adapter code must be &lt;200 LoC. If it's larger, you're probably duplicating
   logic that belongs in `core/`.
4. Add an example under `examples/<agent>/`.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## Commit style

- Short subject (&lt;70 chars), imperative mood.
- Body explains the **why**, not the what. Code already shows the what.
- Reference issues with `#N`.

## Pull requests

- Keep them small. One abstraction change per PR.
- Update `README.md` / `README.zh-CN.md` **together** if user-facing.
- CI must pass.

## Reporting issues

Useful issue reports include:

- The agent and version you're using (`claude --version`, `codex --version`, etc.)
- The exact `hypha` command you ran
- What you expected vs what happened
- `~/.hypha/*.log` tail if relevant

## Code of conduct

Be kind. Assume good faith. If someone is being a jerk, email me directly.
