#!/usr/bin/env bash
# Stop hook: gated consolidation of memory files.
#
# Runs `hypha consolidate` only when:
#   - .last-dream is missing OR > 24h old
#   - AND at least 5 new session transcripts have been touched since
#
# Follows Anthropic Auto Dream's cadence. Runs async in the background so the
# user doesn't wait on it.

set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

if [ "${HYPHA_IN_HOOK:-0}" = "1" ]; then exit 0; fi
export HYPHA_IN_HOOK=1

HYPHA_ROOT="${HYPHA_ROOT:-$HOME/.hypha}"
INPUT=$(cat)
CWD=$(echo "$INPUT" | /usr/bin/env python3 -c "import sys, json; print(json.load(sys.stdin).get('cwd', ''))" 2>/dev/null || echo "")
PROJECT=$(basename "${CWD:-$PWD}" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
MEMDIR="$HYPHA_ROOT/memory/$PROJECT"
LAST="$MEMDIR/.last-dream"

# Gate 1: time since last consolidation
if [ -f "$LAST" ]; then
  NOW=$(date +%s)
  PREV=$(cat "$LAST" 2>/dev/null || echo 0)
  AGE=$((NOW - PREV))
  if [ "$AGE" -lt 86400 ]; then
    exit 0
  fi
fi

# Gate 2: number of new sessions (best-effort; skip gate if directory missing)
SESSIONS_DIR="$HOME/.claude/projects"
if [ -d "$SESSIONS_DIR" ]; then
  NEW_COUNT=$(find "$SESSIONS_DIR" -name "*.jsonl" -newer "$LAST" 2>/dev/null | wc -l)
  if [ "$NEW_COUNT" -lt 5 ]; then
    exit 0
  fi
fi

mkdir -p "$HYPHA_ROOT/logs"
nohup hypha \
  --project "$PROJECT" \
  consolidate \
  --llm "claude -p --bare --setting-sources '' --output-format json" \
  > "$HYPHA_ROOT/logs/consolidate-$(date +%Y%m%d-%H%M%S).log" 2>&1 &

# Update timestamp regardless of final outcome so we don't spam retries.
mkdir -p "$MEMDIR"
date +%s > "$LAST"

exit 0
