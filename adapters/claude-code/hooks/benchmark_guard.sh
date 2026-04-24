#!/usr/bin/env bash
# PostToolUse hook (matcher: Write|Edit): if the edit touched Hypha's own
# config or skill library, run the tiny benchmark and roll back on regression.
#
# This is DGM's "keep_better" strategy minus the Docker sandbox — we rely on
# git to snapshot and restore. Exits 2 on regression, which signals Claude Code
# to surface a block warning.

set -u

if [ "${HYPHA_IN_HOOK:-0}" = "1" ]; then exit 0; fi
export HYPHA_IN_HOOK=1

HYPHA_ROOT="${HYPHA_ROOT:-$HOME/.hypha}"
INPUT=$(cat)
FILE=$(echo "$INPUT" | /usr/bin/env python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null || echo "")

# Only guard changes to Hypha's own evolving surface; application-code edits are
# the user's responsibility, not ours.
case "$FILE" in
  "$HOME/.claude/settings"*|"$HOME/.claude/CLAUDE.md"|"$HOME/.claude/hypha-hooks"*|"$HYPHA_ROOT"/skills/*|"$HYPHA_ROOT"/memory/*)
    ;;
  *)
    exit 0
    ;;
esac

BENCH="$HYPHA_ROOT/bench/tiny.jsonl"
BASELINE="$HYPHA_ROOT/bench/baseline_score"
if [ ! -f "$BENCH" ]; then
  # No bench configured; fail open.
  exit 0
fi

LOGDIR="$HYPHA_ROOT/logs"
mkdir -p "$LOGDIR"

RESULT=$(hypha guard \
  --bench "$BENCH" \
  --baseline "$BASELINE" \
  --llm "claude -p --bare --setting-sources '' --output-format json" \
  2>&1 | tee -a "$LOGDIR/guard.log")
RC=$?

if [ "$RC" -eq 2 ]; then
  echo "Hypha guard: benchmark regressed after editing $FILE" >&2
  echo "$RESULT" >&2
  echo "Run \`git diff\` and consider reverting." >&2
  exit 2
fi

exit 0
