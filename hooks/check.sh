#!/usr/bin/env sh
# PostToolUse hook: run slopcheck on the file Write/Edit just touched.
# Silent no-op unless enforcement is enabled (see hooks/enable.sh).
set -u

root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
checker="$root/scripts/slopcheck.py"

enabled=0
[ -f "$HOME/.claude/suac-enforce" ] && enabled=1
[ -f ".suac-enforce" ] && enabled=1
[ "${SUAC_ENFORCE:-}" = "1" ] && enabled=1
[ "$enabled" = "1" ] || exit 0

[ -f "$checker" ] || exit 0

python3 "$checker" --hook -q
status=$?

# PostToolUse: exit 2 surfaces stderr to the agent as actionable feedback.
[ "$status" = "1" ] && exit 2
exit 0
