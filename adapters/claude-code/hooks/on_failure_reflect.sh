#!/usr/bin/env bash
# Stop hook: if the trajectory shows a failure signal, run `hypha reflect`.
#
# "Failure signal" = recent messages contain rollback/revert/"doesn't work"/etc.,
# OR the user's last message explicitly says something failed. This runs in
# async background mode so the user can quit without waiting.

set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

# Recursion guard: if this hook is invoked from inside another hook's claude -p,
# bail out immediately.
if [ "${HYPHA_IN_HOOK:-0}" = "1" ]; then
  exit 0
fi
export HYPHA_IN_HOOK=1

INPUT=$(cat)
TRANSCRIPT=$(echo "$INPUT" | /usr/bin/env python3 -c "import sys, json; print(json.load(sys.stdin).get('transcript_path', ''))" 2>/dev/null || echo "")
SESSION_ID=$(echo "$INPUT" | /usr/bin/env python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', 'unknown'))" 2>/dev/null || echo "unknown")
CWD=$(echo "$INPUT" | /usr/bin/env python3 -c "import sys, json; print(json.load(sys.stdin).get('cwd', ''))" 2>/dev/null || echo "")

[ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ] && exit 0

# Cheap grep check for failure signals in the last ~40 messages of the JSONL.
TAIL=$(tail -40 "$TRANSCRIPT" 2>/dev/null)
if ! echo "$TAIL" | grep -qiE "rollback|revert|didn.?t work|still broken|that.?s wrong|not right|bug again"; then
  exit 0
fi

PROJECT=$(basename "${CWD:-$PWD}" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
LOGDIR="$HOME/.hypha/logs"
mkdir -p "$LOGDIR"

hypha \
  --project "$PROJECT" \
  reflect \
  --trajectory "$TRANSCRIPT" \
  --session-id "$SESSION_ID" \
  --signal "stop-hook-detected-failure" \
  --llm "claude -p --bare --setting-sources '' --output-format json" \
  >> "$LOGDIR/reflect-$SESSION_ID.log" 2>&1 || true

exit 0
