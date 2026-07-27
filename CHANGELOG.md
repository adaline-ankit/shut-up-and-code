# Changelog

## 0.1.0

First release.

- Seven comment rules: default zero, one line under 80 characters, why never what, a ban list, match the file's density, docstrings for contracts only, delete silently.
- Restraint rules: deliver at the size of the request, rule of three before any abstraction, a do-not-add list, scope discipline, and a ranked solution order that starts with deleting code.
- Reuse and single-source-of-truth: search by value before adding any named thing.
- Error handling: catch only what you handle, preserve cause chains, validate at boundaries, and avoid fallbacks that turn failures into plausible values.
- Verification: confirm imports against the manifest, keep verified/inferred/unknown distinguishable, no false completion claims.
- `scripts/slopcheck.py` — dependency-free checker across ~40 file types. Detects redundant comments via token-overlap analysis, comment blocks, redundant docstrings, step narration, changelog comments, section dividers, filler, commented-out code, bare TODOs, debug logging, entry/exit logging, swallowed errors, defensive guards, and redundant booleans. Exempts JSDoc tags, Google/NumPy docstring sections, module docstrings, and license headers. Inline `slopcheck: ok — reason` suppression.
- Opt-in `PostToolUse` hook that feeds high-severity findings back to the agent for same-turn correction. Off until `hooks/enable.sh` is run.
- Packaging for Claude Code, Codex, Cursor, Gemini CLI, and a self-contained `AGENTS.md`.
- Eval suite with rubric and fixtures.
