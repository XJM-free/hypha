# Hypha × Claude Code

Wires Claude Code's native [hook system](https://docs.claude.com/en/docs/claude-code/hooks)
to Hypha's four abilities.

## What gets installed

Five shell scripts under `hooks/`:

| Hook | Event | What it does |
|---|---|---|
| `session_inject.sh` | `SessionStart` | Greps `~/.hypha/memory/<project>/*.md` for entries relevant to `cwd` and emits them as additional context |
| `on_failure_reflect.sh` | `Stop` | If recent trajectory contains a failure signal, runs `hypha reflect` |
| `skill_harvester.sh` | `Stop` | If recent trajectory contains a success signal, runs `hypha harvest` into the inbox |
| `memory_consolidate.sh` | `Stop` | Gated by 24h + ≥5 new sessions; runs `hypha consolidate` in background |
| `benchmark_guard.sh` | `PostToolUse` (matcher: `Write\|Edit`) | If the edit touched `~/.claude/` or `~/.hypha/skills/**`, runs `hypha guard` and rolls back on regression |

All hooks invoke `claude -p --bare --setting-sources ''` to prevent hook
recursion — `--bare` explicitly disables hook, skill, plugin, and MCP
auto-discovery in the nested call. See
[CLI reference: bare mode](https://docs.claude.com/en/docs/claude-code/cli-reference).

## Install

```bash
# 1. Install Hypha core
pip install -e /path/to/hypha

# 2. Initialize data directory
hypha init

# 3. Copy hooks and merge settings
cp -r adapters/claude-code/hooks ~/.claude/hypha-hooks
# Then merge adapters/claude-code/settings.example.json into your
# ~/.claude/settings.json (or settings.local.json for personal overrides)
```

## Verified hook fields only

This adapter deliberately uses only fields confirmed in the April 2026 Claude
Code docs:

- ✅ `type: "command"` with `command`, `timeout`, `async`
- ✅ `SessionStart`, `Stop`, `PostToolUse`
- ✅ `matcher` with OR syntax (`"Write|Edit"`) and tool-permission syntax
- ✅ Exit code 2 = block (`PreToolUse` / `UserPromptSubmit` only)
- ❌ We do **not** use `type: "agent"` or `type: "prompt"` inline — they were
  under-documented as of 2026-04. Shell `type: "command"` is the safe path.

## Recursion safety

Every hook that invokes `claude -p` uses:

```bash
claude -p --bare --setting-sources '' --output-format json ...
```

`--bare` skips auto-discovery of hooks, skills, plugins, MCP servers, and
CLAUDE.md. `--setting-sources ''` further ensures no settings files are read.
Without both, a Stop hook that runs `claude -p` would itself trigger Stop hooks
in the nested process and recurse.

## Troubleshooting

- Hooks not firing? Check `~/.claude/hooks/*.log` and run `/status` in Claude
  Code to see which hooks are registered.
- `hypha` command not found inside the hook? Hooks inherit a minimal env; use
  an absolute path or `PATH=$PATH:$HOME/.local/bin hypha ...`.
- Recursion suspected? Set `HYPHA_IN_HOOK=1` as an env guard in the hook
  script and exit early if already set.
