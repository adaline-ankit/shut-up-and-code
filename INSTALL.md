# Install

## Claude Code

```bash
claude plugin marketplace add adaline-ankit/shut-up-and-code
```

Invoke with `/shut-up-and-code`. Stays active for the session; "stop suac" or "normal mode" turns it off.

Enforcement backstop — recommended, since the rules alone are documented to decay:

```bash
sh hooks/enable.sh
```

Local development instead of the marketplace:

```bash
git clone https://github.com/adaline-ankit/shut-up-and-code
claude plugin marketplace add ./shut-up-and-code
```

## Codex

```bash
git clone https://github.com/adaline-ankit/shut-up-and-code ~/.codex/skills/shut-up-and-code
```

Invoke with `$shut-up-and-code`. Or drop [`AGENTS.md`](AGENTS.md) in your project root — it is a complete self-contained version.

## Cursor

```bash
git clone https://github.com/adaline-ankit/shut-up-and-code /tmp/suac
mkdir -p .cursor/skills
cp -r /tmp/suac/.cursor/skills/shut-up-and-code .cursor/skills/
```

The `.cursor/` copy is generated from `skills/shut-up-and-code/` — edit the source, not the copy, then run `sh scripts/sync-cursor.sh`.

## Gemini CLI

```bash
gemini extensions install https://github.com/adaline-ankit/shut-up-and-code
```

Slash command only:

```bash
curl -o ~/.gemini/commands/shut-up-and-code.toml \
  https://raw.githubusercontent.com/adaline-ankit/shut-up-and-code/main/skills/shut-up-and-code/agents/gemini.toml
```

## Any other agent

[`AGENTS.md`](AGENTS.md) is self-contained. Paste it into a system prompt, a custom GPT, a project instruction field, or a `.rules` file.

## The checker on its own

No plugin needed — it is one dependency-free file.

```bash
curl -O https://raw.githubusercontent.com/adaline-ankit/shut-up-and-code/main/scripts/slopcheck.py
python3 slopcheck.py --diff
```

### As a git pre-commit hook

```bash
printf '#!/bin/sh\npython3 scripts/slopcheck.py --diff --cached -q\n' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### In CI

```yaml
- name: slopcheck
  run: python3 scripts/slopcheck.py --diff origin/${{ github.base_ref }}
```

Checks changed files only, so existing code never blocks a PR.

## Enforcement scopes

| Command | Effect |
|---|---|
| `sh hooks/enable.sh` | On globally (`~/.claude/suac-enforce`) |
| `sh hooks/enable.sh --project` | On for this project (`.suac-enforce`) |
| `SUAC_ENFORCE=1` | On for one shell session |
| `sh hooks/disable.sh` | Off, both scopes |

The hook is registered when the plugin installs but does nothing until one of these is set.

## Verifying it loaded

Ask for something small and see what comes back:

```
Add a 30 second timeout to the fetch call in src/api.ts.
```

Working: one changed line, no comment, or a single comment saying *why* 30 seconds. Not working: a `/** Sets the timeout */` block and a `// Step 1:` above it.

Then check the checker itself runs:

```bash
python3 scripts/slopcheck.py scripts/slopcheck.py
```

Should print `slopcheck: clean`.
