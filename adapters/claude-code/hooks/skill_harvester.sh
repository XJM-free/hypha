#!/usr/bin/env bash
# Stop hook: if the trajectory shows a success signal, harvest a skill draft
# into the inbox (NOT directly into the active skill library — mimics Gemini
# CLI's /memory inbox pattern; user approves explicitly).

set -u

if [ "${HYPHA_IN_HOOK:-0}" = "1" ]; then exit 0; fi
export HYPHA_IN_HOOK=1

INPUT=$(cat)
TRANSCRIPT=$(echo "$INPUT" | /usr/bin/env python3 -c "import sys, json; print(json.load(sys.stdin).get('transcript_path', ''))" 2>/dev/null || echo "")
SESSION_ID=$(echo "$INPUT" | /usr/bin/env python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', 'unknown'))" 2>/dev/null || echo "unknown")
CWD=$(echo "$INPUT" | /usr/bin/env python3 -c "import sys, json; print(json.load(sys.stdin).get('cwd', ''))" 2>/dev/null || echo "")

[ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ] && exit 0

TAIL=$(tail -40 "$TRANSCRIPT" 2>/dev/null)
# Success signals: explicit user approval or a tests-pass / shipped / LGTM event.
if ! echo "$TAIL" | grep -qiE "lgtm|ship it|looks good|nice|works now|fixed|all tests pass"; then
  exit 0
fi

PROJECT=$(basename "${CWD:-$PWD}" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
LOGDIR="$HOME/.hypha/logs"
mkdir -p "$LOGDIR"

# Try to capture a diff for context. Fall back silently if not in a git repo.
DIFF=""
if [ -n "$CWD" ] && cd "$CWD" 2>/dev/null; then
  DIFF=$(git diff --stat HEAD~1 2>/dev/null | head -40 || true)
fi

hypha \
  --project "$PROJECT" \
  harvest \
  --trajectory "$TRANSCRIPT" \
  --session-id "$SESSION_ID" \
  --diff "$DIFF" \
  --llm "claude -p --bare --setting-sources '' --output-format json" \
  >> "$LOGDIR/harvest-$SESSION_ID.log" 2>&1 || true

exit 0
