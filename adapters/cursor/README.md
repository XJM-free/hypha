# Hypha × Cursor

Status: **P1 (stub)** — interface documented, implementation pending.

## How Cursor's lifecycle maps to Hypha

Cursor configures agents via `.cursor/rules/*.mdc` files and user rules in
Cursor settings. It does not have shell hooks, but it reliably:

1. Reads `.cursor/rules/` at session start
2. Respects git hooks (`post-commit`, `pre-push`)
3. Runs in a workspace with full filesystem access

Integration plan:

1. **`.cursor/rules/hypha.mdc`** — auto-generated rule file that pulls the top
   entries from `~/.hypha/memory/<project>/*.md` at session start. Rewritten
   idempotently via `hypha export cursor-rules`.
2. **Git `post-commit` hook** — `hypha harvest` + `hypha consolidate` (gated)
   run in the background after each commit. This is a reasonable proxy for
   "session end" since Cursor sessions don't have a clean exit signal.
3. **Git `pre-push` hook** — `hypha guard` runs before push if the working
   tree touched `.cursor/rules/` or `~/.hypha/skills/**`.

## Planned install

```bash
hypha init
hypha export cursor-rules > .cursor/rules/hypha.mdc

# .git/hooks/post-commit (idempotent):
cat >> .git/hooks/post-commit <<'EOF'
command -v hypha >/dev/null && hypha harvest --git-commit HEAD &
EOF
chmod +x .git/hooks/post-commit
```

## Why not yet

Needs real-world validation for:

- Whether `.cursor/rules/` is re-read mid-session (affects injection cadence)
- Whether Cursor's "Chat" vs "Agent" modes both honor the rule file

## Contribute

PRs welcome. See [CONTRIBUTING.md](../../CONTRIBUTING.md).
