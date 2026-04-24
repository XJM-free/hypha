#!/usr/bin/env bash
# SessionStart hook: inject relevant memory into the session context.
#
# Reads Claude Code's SessionStart hook input (JSON via stdin) and emits
# additionalContext containing memory entries relevant to the current cwd.
#
# Fails open: any error in memory lookup results in zero injected context,
# never a failed session start.

set -u

HYPHA_ROOT="${HYPHA_ROOT:-$HOME/.hypha}"
INPUT=$(cat)
CWD=$(echo "$INPUT" | /usr/bin/env python3 -c "import sys, json; print(json.load(sys.stdin).get('cwd', ''))" 2>/dev/null || echo "")
PROJECT=$(basename "${CWD:-$PWD}" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
MEMORY_DIR="$HYPHA_ROOT/memory/$PROJECT"

if [ ! -d "$MEMORY_DIR" ]; then
  # First time in this project; nothing to inject.
  exit 0
fi

# Pull top entries from each topic, capped to keep context cost bounded.
CONTEXT=""
for topic in preferences decisions corrections patterns facts; do
  F="$MEMORY_DIR/$topic.md"
  [ ! -f "$F" ] && continue
  HEAD=$(head -20 "$F")
  if [ -n "$HEAD" ]; then
    CONTEXT+=$'\n\n## '"$topic"$'\n'"$HEAD"
  fi
done

# Also surface the global lessons file if present.
GLOBAL="$HYPHA_ROOT/memory/global_lessons.md"
if [ -f "$GLOBAL" ]; then
  CONTEXT+=$'\n\n## cross-project lessons\n'"$(head -15 "$GLOBAL")"
fi

if [ -z "$CONTEXT" ]; then
  exit 0
fi

/usr/bin/env python3 -c "
import json, sys
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': '''# Hypha-injected memory for this project$CONTEXT'''
    }
}))
"
