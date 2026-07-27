#!/usr/bin/env sh
# Turn slopcheck enforcement off, both scopes.
set -eu

rm -f "$HOME/.claude/suac-enforce" .suac-enforce
echo "slopcheck enforcement OFF. The skill's rules still apply; the backstop is gone."
