# Enforcement

Load when setting up the checker, interpreting its output, or deciding whether a finding is wrong.

## Why enforcement exists

A rule in `CLAUDE.md` is a suggestion competing with a strong default, and the default [wins often enough](https://github.com/anthropics/claude-code/issues/65961) that users end up stacking a project rule, memory entries, and hooks just to get clean code. That stack is what this repo packages — once, properly.

The checker is not a substitute for the rules. It is the backstop for when the default reasserts itself, which it does silently and which you will not notice from the inside.

## The checker

`scripts/slopcheck.py` — no dependencies, Python 3.10+.

```bash
python3 scripts/slopcheck.py src/auth.ts          # specific files
python3 scripts/slopcheck.py src/                 # a directory
python3 scripts/slopcheck.py --diff               # changed vs HEAD
python3 scripts/slopcheck.py --diff main          # changed vs a base branch
python3 scripts/slopcheck.py --diff --json        # machine-readable
python3 scripts/slopcheck.py src/ -v              # include low severity
python3 scripts/slopcheck.py src/ -q              # one-line summary
```

Exit codes: `0` clean · `1` findings at or above `--fail-on` (default `high`) · `2` bad usage.

**`--diff` is the one to use during work.** It checks what you changed, which is what the rules govern — the skill does not de-slop files you were not asked to touch.

## The hook

Wire it as a `PostToolUse` hook and every `Write`/`Edit` gets checked, with findings fed back to you as feedback you can act on before the user sees the file. This is the difference between a rule you intend to follow and a rule that holds.

Enforcement is **opt-in**. The hook is registered when the plugin installs but exits silently until a flag file exists:

```bash
sh hooks/enable.sh          # turn enforcement on
sh hooks/enable.sh --project # this project only
sh hooks/disable.sh         # off
```

On a high-severity finding the hook exits non-zero and prints a summary to stderr. That surfaces in your context as: this file you just wrote has slop in it, fix it now. Medium and low findings print without failing.

## Reading a finding

```
src/upload.ts:42  [high] redundant-comment
    Comment restates the code beneath it.
    > // Initialize the retry counter
    fix: Delete it. Comment the why, or say nothing.
```

Act on it immediately, in the same turn, on the file you just wrote. Do not defer to a cleanup pass, and do not tell the user about the finding — just fix it. The user asked for clean code, not a report about the process that produced it.

## When a finding is wrong

It happens. The redundancy heuristic compares comment vocabulary against the adjacent code and cannot know that a word carries domain meaning.

Suppress inline, **with a reason**:

```python
except (OSError, TimeoutError):
    continue  # slopcheck: ok — probe is best-effort, other sources still run
```

```ts
// slopcheck: ignore redundant-comment
// Idempotent: safe to call twice, unlike the v1 endpoint.
```

`slopcheck: ok` suppresses everything on that line or the line below. `slopcheck: ignore <rule>` suppresses one rule. Both are honoured on the offending line or the line above it.

**A suppression without a reason is worse than the finding.** It is how a linter stops meaning anything. If you cannot write the reason in a few words, the finding was probably right.

## CI

```yaml
- name: slopcheck
  run: python3 scripts/slopcheck.py --diff origin/${{ github.base_ref }}
```

Fails on high severity in changed files only, so existing code does not block anyone. Add `--fail-on medium` when a team wants to hold a tighter line, but do it deliberately — a gate that fires constantly gets bypassed, and a bypassed gate is worse than none.

## What it cannot see

The checker is deterministic, which means it only catches deterministic patterns. It cannot see unnecessary abstraction, duplicated sources of truth, scope creep, reimplemented stdlib, test theatre, confident guessing, or false completion — the judgement half of `slop-catalogue.md`.

So a clean checker run is necessary, not sufficient. It means you did not leave obvious noise behind. It does not mean the design is right.

## Self-check

The checker passes its own rules:

```bash
python3 scripts/slopcheck.py scripts/slopcheck.py   # clean
```

That is deliberate. A tool that lectures about comment discipline while carrying section dividers and three-line explanations has no standing, and every rule in it should be doubted.
