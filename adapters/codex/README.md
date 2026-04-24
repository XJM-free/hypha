# Hypha × OpenAI Codex

Status: **P1 (stub)** — interface documented, implementation pending.

## How Codex's lifecycle maps to Hypha

Codex reads project conventions from `AGENTS.md` and per-user config from
`~/.codex/config.toml`. It doesn't have an in-process hook system like Claude
Code; integration is done via:

1. **`AGENTS.md` injection** — Hypha can render top memory entries into a
   project's `AGENTS.md` at session start (idempotent — only rewrites the
   `<!-- HYPHA:BEGIN -->` / `<!-- HYPHA:END -->` delimited block).
2. **Pre/post-exec wrappers** — Codex supports `pre_exec` and `post_exec`
   scripts in `config.toml`. We hook:
   - `pre_exec` → `hypha consolidate` (gated)
   - `post_exec` → `hypha reflect` on non-zero exit; `hypha harvest` on success
3. **Shared playbook** — Both Codex and Claude Code read the same
   `~/.hypha/memory/<project>/*.md` files. The playbook is the substrate,
   not any single agent's configuration.

## Planned install

```bash
hypha init
# Rendered to AGENTS.md (idempotent):
hypha export agents-md >> AGENTS.md

# Merge into ~/.codex/config.toml:
# [hooks]
# pre_exec  = "hypha consolidate --llm 'codex exec --dry-run'"
# post_exec = "hypha reflect-or-harvest --exit-code $?"
```

## Why not yet

Codex's hook semantics are still stabilizing in the 2026 Q2 Agents SDK. We're
waiting for:

- Stable `transcript_path` equivalent for Codex sessions
- Official confirmation that `post_exec` receives the exit code

Track [issue #TBD](https://github.com/XJM-free/hypha/issues) for the
implementation PR.

## Contribute

If you use Codex daily and want to land this adapter, see
[CONTRIBUTING.md](../../CONTRIBUTING.md) and open a draft PR. Target: <200 LoC,
no new dependencies in `core/`.
