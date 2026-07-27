<div align="center">

# shut-up-and-code

**Your coding agent writes decent code and then explains it to you like you've never seen a `for` loop.**

*This is the skill that makes it stop.*

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-0F766E)](#install)
[![Codex](https://img.shields.io/badge/Codex-skill-0F766E)](#install)
[![Cursor](https://img.shields.io/badge/Cursor-skill-0F766E)](#install)
[![Gemini CLI](https://img.shields.io/badge/Gemini_CLI-extension-0F766E)](#install)

</div>

---

## The problem

```diff
- // ============================================================
- // User service
- // ============================================================
-
- /**
-  * Fetches a user by their ID.
-  *
-  * This function takes a user ID and returns the user object
-  * from the database, or null if not found.
-  */
  export async function getUser(id: string) {
-   // Initialize the result variable
-   let result = null;
-
-   // Step 1: Query the database
-   console.log("getUser called with", id);
-
-   try {
-     // Query the users table for the user
-     result = await db.query(USERS_QUERY, [id]);
-   } catch (e) {
-     // Log the error
-     console.error(e);
-   }
-
-   // NEW: added null safety as requested
-   if (result && result.rows && result.rows.length > 0) {
-     // Return the first row
-     return result.rows[0];
-   }
-
-   return null;
+   const result = await db.query(USERS_QUERY, [id]);
+   return result.rows[0] ?? null;
  }
```

Twenty-eight lines became three. Nothing was lost — every deleted comment restated the line beneath it, the `try/catch` swallowed the error and returned a silent `null`, and the triple existence check guarded against a shape the driver never returns.

Nobody asked for any of it. It arrived anyway.

## Why a skill, and not just a CLAUDE.md rule

Because that doesn't work, and it's [tracked as a bug](https://github.com/anthropics/claude-code/issues/65961):

> A clear, mandatory rule in `CLAUDE.md` does not reliably suppress it. Reinforcing the rule via the memory system does not stop it either. […] Users shouldn't have to stack a CLAUDE.md rule + memory entries + enforcement hooks just to get clean code.

That stack — rules, plus a checker, plus a hook that closes the loop — is what this repo is. Packaged once, so you don't have to build it.

## Install

```bash
claude plugin marketplace add adaline-ankit/shut-up-and-code
```

Then `/shut-up-and-code`. It stays on for the session; "stop suac" turns it off.

Want the enforcement backstop too (recommended):

```bash
sh hooks/enable.sh
```

Other agents in [INSTALL.md](INSTALL.md) — Codex, Cursor, Gemini CLI, or paste [`AGENTS.md`](AGENTS.md) anywhere.

## The comment rules

The part you actually came for.

| # | Rule |
|---|---|
| 1 | **Default is zero.** A comment must carry information the code cannot |
| 2 | **One line, under 80 chars.** Two if a real constraint won't compress. Never three |
| 3 | **Why, never what.** The code says what. Only you know why |
| 4 | **Ban list** — no narration, no changelog comments, no dividers, no filler, no commented-out code, no emoji, no unowned TODOs |
| 5 | **Match the file.** Read it, count its comments, match its density. House style always wins |
| 6 | **Docstrings are for contracts** — units, ranges, errors, invariants. Not for rephrasing the name |
| 7 | **Delete silently.** No `// (no comment needed here)` |

What a comment that earns its line looks like:

```ts
// Gateway kills idle sockets at 35s; stay under it.
const timeout = 30_000;

// Half-even, not half-up, to match the finance ledger.
const total = round(sum, "half-even");

// Sorted by ID so pagination cursors stay stable.
for (const u of users) { ... }
```

Each one is a fact you cannot get by reading the code. Each one is a single line. That's the whole standard.

## It's not only the comments

Comments are the loudest symptom. The same reflex produces the rest, and the skill covers all of it:

| Pattern | What it does instead |
|---|---|
| **Over-engineering** | Delivers a one-line change *as* a one-line change — not a checklist ([#72106](https://github.com/anthropics/claude-code/issues/72106)) |
| **Invented abstractions** | Rule of three. One call site → inline. Two → duplicate. Three → extract |
| **Duplicated constants** | Searches before adding — by *value*, not just by name ([#37137](https://github.com/anthropics/claude-code/issues/37137)) |
| **Swallowed errors** | Handle, wrap with context, or rethrow. Never `catch { log(e) }` |
| **Defensive padding** | Validate at the boundary, then trust the types |
| **Debug leftovers** | No `console.log`, no `print`, no `debugger` |
| **Scope creep** | No renames, reformats, or "while I was in here" fixes |
| **Confident guessing** | Verifies against the repo and lockfile. ~1 in 5 LLM-suggested packages don't exist |
| **False completion** | "Tests pass" only after running them |

## The checker

`scripts/slopcheck.py` — dependency-free, Python 3.10+, works across ~40 file types.

```bash
python3 scripts/slopcheck.py --diff        # what you just changed
python3 scripts/slopcheck.py src/          # a directory
python3 scripts/slopcheck.py --diff main   # vs a base branch, for CI
```

```
slopcheck: 13 finding(s) — section-divider 2 · redundant-comment 2 · comment-block 1 ·
step-narration 1 · debug-logging 1 · swallowed-error 1 · changelog-comment 1 ·
commented-out-code 1 · filler-comment 1 · defensive-guard 1 · bare-todo 1

src/upload.ts:12  [high] redundant-comment
    Comment restates the code beneath it.
    > // Initialize the result variable
    fix: Delete it. Comment the why, or say nothing.
```

**How the redundancy rule works:** it tokenizes the comment and the code beneath it, splitting `camelCase` and `snake_case`, drops stopwords and mechanical verbs (`initialize`, `loop`, `return`), then checks whether the comment introduced any vocabulary the code didn't already have. If it didn't, the comment is restating the line. That's why `// Initialize the result variable` gets caught and `// Gateway kills idle sockets at 35s` doesn't.

It's deliberately tuned for **precision over recall**. A linter that cries wolf gets disabled, and a disabled linter is worth nothing — so legitimate JSDoc `@param` blocks, Google-style `Args:` docstrings, module docstrings, and license headers are all exempt. Taste lives in the skill; only the mechanical patterns live in the regex.

When it's wrong, suppress it *with a reason*:

```python
except (OSError, TimeoutError):
    continue  # slopcheck: ok — probe is best-effort, other sources still run
```

A suppression without a reason is worse than the finding — that's how linters stop meaning anything.

### It passes its own rules

```bash
$ python3 scripts/slopcheck.py scripts/slopcheck.py
slopcheck: clean
```

Not a coincidence. Running it against itself during development found four real defects — including a false positive where it flagged its own regex patterns as debug logging, because it was matching inside string literals. Its own section dividers and three-line explanations got deleted for the same reason yours will.

A tool that lectures about comment discipline while carrying `# ═══ helpers ═══` has no standing.

## The hook is the part that makes it stick

Instructions decay. A hook doesn't.

```bash
sh hooks/enable.sh            # global
sh hooks/enable.sh --project  # this repo only
sh hooks/disable.sh           # off
```

Enforcement is **opt-in and off by default** — the hook installs with the plugin but no-ops until you flip the flag, so nothing changes under you.

Once on, every `Write`/`Edit` gets checked. High-severity findings come back to the agent as feedback in the same turn, so it fixes the file before you ever see it. You don't get a report; you get clean code.

## What's inside

| File | Carries |
|---|---|
| [`SKILL.md`](skills/shut-up-and-code/SKILL.md) | The 7 comment rules, restraint, the pre-finish checklist |
| [`comments.md`](skills/shut-up-and-code/references/comments.md) | What earns a comment, length discipline, per-language conventions |
| [`slop-catalogue.md`](skills/shut-up-and-code/references/slop-catalogue.md) | Every detected pattern plus the judgement-only ones, by severity |
| [`restraint.md`](skills/shut-up-and-code/references/restraint.md) | Rule of three, the do-not-add list, scope discipline |
| [`reuse-and-ssot.md`](skills/shut-up-and-code/references/reuse-and-ssot.md) | Search before you write, and what to do with duplicates |
| [`error-handling.md`](skills/shut-up-and-code/references/error-handling.md) | Catch only what you handle, fallbacks that lie, retries |
| [`verification.md`](skills/shut-up-and-code/references/verification.md) | Hallucinated imports, verified vs inferred vs unknown |
| [`enforcement.md`](skills/shut-up-and-code/references/enforcement.md) | Hook setup, reading findings, CI, suppression etiquette |

## Good things to ask it

```
/shut-up-and-code
Implement the retry logic in src/upload.ts.

Clean the slop out of this diff.
Review my comments — cut anything that restates the code.
Is this abstraction earning its keep?
I have the same timeout in three files. Find them.
This catch block swallows the error. Fix it properly.
```

## Caveats

- **The checker is mechanical.** It catches redundant comments, dead debug logging, and swallowed errors. It cannot see a bad abstraction, duplicated truth, or a confident guess — that's the judgement half, and it lives in the skill.
- **A clean run is necessary, not sufficient.** It means you left no obvious noise. It says nothing about whether the design is right.
- **House style wins over everything here.** If your project mandates Javadoc on every method, the skill defers. That's rule 5, not an exception to it.
- **It won't de-slop your whole repo.** Rules apply to code it writes or edits. Reformatting untouched files is the scope creep it's built to prevent — run the checker manually when you want a wider sweep.

## Contributing

The highest-value PRs, in order: a false positive in `slopcheck.py` (include the snippet), a slop pattern that isn't detected yet, and comment conventions for a language `comments.md` handles badly.

## License

MIT. Fork it, tighten it, make it stricter.
