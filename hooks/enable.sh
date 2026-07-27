#!/usr/bin/env sh
# Turn slopcheck enforcement on. Default is global; --project scopes it here.
set -eu

if [ "${1:-}" = "--project" ]; then
  touch .suac-enforce
  echo "slopcheck enforcement ON for this project (.suac-enforce)"
  echo "Add .suac-enforce to .gitignore if you don't want to commit it."
else
  mkdir -p "$HOME/.claude"
  touch "$HOME/.claude/suac-enforce"
  echo "slopcheck enforcement ON globally (~/.claude/suac-enforce)"
fi

echo "Files written by Write/Edit are now checked; high-severity findings are reported back."
echo "Off: sh hooks/disable.sh"
