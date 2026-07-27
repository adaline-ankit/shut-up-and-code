#!/usr/bin/env sh
# Regenerate the Cursor copy of the skill from the source of truth.
set -eu

root="$(cd "$(dirname "$0")/.." && pwd)"
src="$root/skills/shut-up-and-code"
dest="$root/.cursor/skills"

rm -rf "$dest/shut-up-and-code"
mkdir -p "$dest"
cp -R "$src" "$dest/shut-up-and-code"

echo "synced $src -> $dest/shut-up-and-code"
