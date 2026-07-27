# shut-up-and-code

Portable, self-contained version for any agent that reads `AGENTS.md` (Codex, Cursor, Amp, and friends). Full skill with reference files: [`skills/shut-up-and-code/`](skills/shut-up-and-code/SKILL.md).

---

Write the code. Don't narrate it. The reader is an engineer who can read code and does not need a tour guide.

These rules apply to every file you write or edit for the rest of the session. They do not lapse when the language changes or the file "feels complex."

## Comments

1. **Default is zero.** A comment must carry information the code cannot. Before writing one, ask what a competent reader loses if you delete it. "Nothing" or "they'd read one more line" → delete it.
2. **One line, under 80 characters.** Two only when a real constraint cannot compress. Three or more above an implementation is a defect — that content belongs in a commit message, an ADR, or a docstring on a public API.
3. **Why, never what.** The code says what. Comment the non-obvious: a unit, a boundary, an external constraint, a rejected alternative, a bug being worked around, the source of a magic number. If you cannot state a why, there is no comment to write.
4. **Never write these:** comments restating the line below · step narration (`// Step 1:`, `// First we`) · changelog comments (`// NEW:`, `// Changed from v1`, `// as requested`) · section dividers (`// ==== Helpers ====`) · filler (`// Note that`, `// This function simply`) · commented-out code · placeholder confessions (`// in a real implementation`) · emoji · TODOs with no owner or issue · docstrings that rephrase the signature.
5. **Match the file.** Read it first, count its comments, match its density and voice. House style outranks every rule here.
6. **Docstrings are for contracts** — units, ranges, error behaviour, side effects, invariants. Not for rephrasing the name. `get_user(id)` does not need "Gets a user by id."
7. **Delete silently.** When you decide against a comment, just don't write it. No `// (no comment needed)`, no telling the user you refrained.

Good: `// Gateway kills idle sockets at 35s; stay under it.`
Bad: `// Set the timeout to 30 seconds`

## Restraint

**Deliver at the size of the request.** A one-line change is a one-line change — not a checklist, a phased plan, or a new module. Producing process instead of a diff is a real, documented failure that costs the user money and trust. A one-line fix also gets a one-line summary.

**Rule of three.** No abstraction until three real call sites exist. One → inline it. Two → duplicate it; two similar things are usually not the same thing and you cannot yet see the axis of variation. A wrong abstraction is far more expensive than duplication, because duplication is visible and trivially fixed.

**Do not add unless asked:** config options, feature flags, interfaces with one implementation, `BaseX` with one subclass, a `utils/` file for one function, wrappers that only forward arguments, plugin systems, caching before measurement, retries around calls that have never failed, or abstractions "for when we add other providers."

**Scope is exactly what was asked.** No renaming, reformatting, import reordering, dependency bumps, or "while I was in here" improvements. Mixed diffs are unreviewable. When you notice something worth fixing, name it in one line and move on. Hand-tuned config — credentials, live integrations, infrastructure — is a protected zone.

**Solve in this order, stopping as soon as it works:** delete something → change a line → add lines in the existing structure → add a function → add a file → add a dependency → add an abstraction layer.

Restraint is about implementation size, never scope. Deliver the whole request; if part was blocked, say which part.

## Reuse before you write

Search before adding any constant, path, URL, type, helper, or env var. Search **the value, not just the name** — `"settings.json"` finds copies that `SETTINGS_PATH` misses.

Duplicating a value into a second file is a documented compounding failure: each session adds another copy until a one-line bug needs fixing in places nobody has an inventory of. When you find duplicates, reference an existing one and say so in a line — do not add a third, and do not silently refactor both as part of unrelated work.

Also check the stdlib and installed dependencies before hand-rolling `groupBy`, `chunk`, `retry`, or `deepClone`.

## Errors, honestly

**A crash with a stack trace beats a silent wrong answer.** Catch only when you can handle it, add context and rethrow, or translate it at a boundary. Otherwise let it propagate — not catching is a decision, usually the right one.

Never `catch (e) { log(e) }` or `except Exception: pass`. Catch specific types, preserve the cause chain (`raise X from e`, `%w`, `{ cause: e }`), log once at the boundary rather than at every level.

**Validate at the boundary, then trust your types.** Chained existence checks (`a && a.b && a.b.c`) deep in the system mean the boundary let a bad value through or the type is too loose — fix that, don't pad.

Beware fallbacks that lie: `parseFloat(input) || 1.0` turns `"abc"` into a plausible number; `??` not `||` when you mean absent.

## Verify, don't guess

Confirm signatures, config keys, flags, endpoints, error types, defaults, and version-specific behaviour before asserting them. Check the repo first (strongest evidence — it is the version you actually have), then the lockfile, vendored source, type definitions, docs matched to the installed version, or just run it.

**Never write an unconfirmed import.** Roughly 1 in 5 packages LLMs recommend do not exist. Confirm against the manifest or existing usage; if a dependency genuinely needs adding, say so rather than slipping it into a diff.

Keep three states distinguishable: **verified** (say how), **inferred** (say so), **unknown** (say what would resolve it). Never let inference wear the voice of verification.

**No false completion.** "Tests pass" only after running them. "Fixed" only after reproducing. If unverified, say so and give the one command that checks it.

## Before you finish

1. Delete every comment that restates code, narrates, records a change, or fills space. Over one line → compress or cut.
2. Is every changed line traceable to the request? Revert what is not.
3. Did you add a constant, type, or helper that already existed?
4. No `console.log`, `print`, `debugger`, or commented-out experiments.
5. Every catch handles, wraps, or rethrows. None just logs.
6. Any abstraction with one caller? Inline it.
7. Run the checker if available: `python3 scripts/slopcheck.py --diff`. Fix findings. If one is genuinely wrong, suppress it with a reason: `# slopcheck: ok — <why>`.

Then keep the summary short: what changed, where, what you deliberately did not do.

## Break the rules when

The project's own convention differs (house style always wins) · the algorithm is genuinely non-obvious (two lines, or a linked reference) · a documentation standard applies (regulated or safety-critical) · the user asked for teaching comments (then comment generously) · the file is generated or vendored (leave it alone).
