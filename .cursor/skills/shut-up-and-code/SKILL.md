---
name: shut-up-and-code
description: 'Write code that reads like a senior engineer wrote it, not like a model explaining itself. One-line comments, why not what, no narration, no changelog comments, no invented abstractions, no defensive padding, reuse before you write. Ships a checker and an optional hook because instructions alone are documented to fail. Invoke with /shut-up-and-code; stays on until "stop suac".'
disable-model-invocation: true
license: MIT
metadata:
  hermes:
    tags: [Code Quality, Comments, Anti-Slop, Restraint, Style]
    category: engineering
    related_skills: []
---

# shut-up-and-code

Write the code. Don't narrate it.

The reader is an engineer who can read code. They do not need a tour guide. Every comment that tells them what the next line does spends their attention and returns nothing.

## Persistence

These rules apply to every file you write or edit for the rest of the session. They do not expire after a few turns, they do not lapse when the language changes, and they do not relax because a file "feels complex." If you are unsure whether they still apply, they do.

Off only on "stop suac" or "normal mode". Confirm in one line.

## Why this skill needs a hook

Verbose commenting is a strong default. It is [documented](https://github.com/anthropics/claude-code/issues/65961) to survive a mandatory rule in `CLAUDE.md` *and* reinforcement through memory. Instructions are necessary and not sufficient.

So this skill has two halves. The rules below, and `scripts/slopcheck.py` — a deterministic checker you can wire as a `PostToolUse` hook so every file you touch gets checked and you fix it before the user ever sees it. See `references/enforcement.md`. **Use the checker when it is available. Do not treat your own judgement as sufficient here; the whole reason this skill exists is that the default reasserts itself.**

## Reference map

Load on demand.

| Need | File |
|---|---|
| What earns a comment, length discipline, per-language conventions | `references/comments.md` |
| Every slop pattern, by severity, detected and judgement-only | `references/slop-catalogue.md` |
| Rule of three, the do-not-add list, scope discipline | `references/restraint.md` |
| Search before you write; handling duplicates | `references/reuse-and-ssot.md` |
| Catch only what you handle; fallbacks that lie | `references/error-handling.md` |
| Hallucinated imports; verified vs inferred vs unknown | `references/verification.md` |
| Checker setup, reading findings, suppression etiquette | `references/enforcement.md` |

## Comments

### Rule 1 — the default is zero

A comment is not free. It must earn its line by carrying information the code cannot. Most code carries its own meaning. Write the code, stop, and move on.

Before writing any comment, answer: **what does a competent reader lose if I delete this?** If the answer is "nothing," delete it. If the answer is "they would have to read two more lines," delete it — they can read.

### Rule 2 — one line

One line. Under 80 characters. Two lines only when a genuine constraint cannot compress, and two is the hard ceiling.

Three or more lines above an implementation is a defect. If the rationale truly needs a paragraph, it belongs in a commit message, an ADR, or a docstring on a public API — not stacked above a function body.

```
BAD                                    GOOD
/**                                    // Stripe rounds half-up; we round half-even to match finance.
 * Calculates the total price.
 * This function takes the items
 * and adds up their prices, then
 * applies the tax rate.
 * @returns the total
 */
```

### Rule 3 — why, never what

The code says what. Only you know why. Comment the non-obvious: a constraint, a unit, a boundary condition, a rationale, a rejected alternative, a bug being worked around, a source.

```
BAD                                     GOOD
// Set the timeout to 30 seconds        // Gateway kills idle sockets at 35s; stay under it.
const timeout = 30_000;                 const timeout = 30_000;

// Loop through the users               // Sorted by ID so pagination cursors stay stable.
for (const u of users) {}               for (const u of users) {}

// Increment the counter                (no comment — obviously)
count++;
```

If you cannot state a why, there is no comment to write.

### Rule 4 — the ban list

Never write these. Not in any language, not for any reason.

| Banned | Example | Why |
|---|---|---|
| **Restating code** | `// Initialize the counter` | The line below says it |
| **Step narration** | `// Step 1: validate input` | Numbered tours belong in a commit message |
| **Changelog comments** | `// NEW: added retry`, `// Changed from v1` | Git records history; the source records the present |
| **Section dividers** | `// ===== Helpers =====` | Structure comes from functions and files |
| **Filler** | `// Note that`, `// This function simply` | Zero information, costs a line |
| **Commented-out code** | `// const old = ...` | Delete it. Version control remembers |
| **Placeholder confessions** | `// In a real implementation you would` | Either implement it or say so to the user, not the file |
| **Emoji** | `// 🚀 Fast path` | No |
| **Unowned TODOs** | `// TODO: handle this` | Add an issue ref or an owner, or do it now |
| **Obvious docstrings** | `"""Gets a user by ID."""` on `get_user(id)` | Rephrasing the signature is not documentation |

### Rule 5 — match the file

Read the file before you write in it. Count its comments. **Match its density and its voice.** A file with no comments does not want yours. A file with a specific docstring convention gets that convention, exactly.

Consistency with surrounding code outranks every preference in this skill, including these rules — a "correct" comment in the wrong house style is still wrong.

### Rule 6 — docstrings are for contracts

A docstring on a public API earns its place by adding what a signature cannot: units, ranges, error behaviour, thread safety, side effects, invariants, complexity.

It does not earn its place by rephrasing the name. `get_user(id)` does not need "Gets a user by id."

One-line summary. Structured tags (`@param`, `Args:`) only where they carry real constraints, and only where the project already uses them.

### Rule 7 — delete silently

When you decide against a comment, just don't write it. Do not tell the user you refrained. Do not add "// (no comment needed here)". The absence is the deliverable.

## Beyond comments

Comments are the loudest symptom. These are the rest, and they compound. Full catalogue with detection patterns in `references/slop-catalogue.md`.

### Restraint

**Simplest correct solution, at the size of the request.** A one-line change is delivered as a one-line change — not a checklist, not a migration plan, not a new module. Inflating a small task into a process is a [documented](https://github.com/anthropics/claude-code/issues/72106) failure that costs the user real money and real time.

No abstraction until there are three call sites. No config option nobody asked for. No `utils/` file for one function. No interface with one implementation. See `references/restraint.md`.

**Scope is exactly what was asked.** Do not rename things you were not asked to rename, reformat files you were not asked to reformat, or "improve" adjacent code in passing. Unrequested diff is unreviewable diff. Notice it, mention it in one line, move on.

### Reuse before you write

Search before you add. A constant, a path, a type, a helper — check whether it already exists, and reference it if it does.

Duplicating a value into a second file is a [documented](https://github.com/anthropics/claude-code/issues/37137) compounding failure: each session adds another copy, and a bug then needs fixing in places nobody knows about. When you find duplicates, point at the single source rather than adding a third copy. See `references/reuse-and-ssot.md`.

### Errors, honestly

Do not catch what you cannot handle. Do not log-and-continue as a substitute for handling. Do not guard against states the type system already excludes.

A crash with a stack trace is more useful than a silent wrong answer. See `references/error-handling.md`.

### Verify, don't guess

If a fact about an external library, API, or platform is load-bearing, look it up with the tools you have. Guessing from local code and asserting confidently is a [documented](https://github.com/anthropics/claude-code/issues/72106) failure — and roughly **1 in 5** package names LLMs recommend do not exist, so an unverified import is a real risk, not a hypothetical.

Never invent a function signature, a flag, a config key, or a package name. See `references/verification.md`.

## Before you finish

Run this on every file you touched. If the checker is wired up, it does most of it for you.

1. **Comment sweep.** Delete every comment that restates code, narrates a step, records a change, or fills space. Anything over one line: compress or cut.
2. **Diff sweep.** Is every changed line traceable to the request? Revert what is not.
3. **Reuse sweep.** Did you add a constant, type, or helper that already existed?
4. **Debug sweep.** No `console.log`, no `print`, no `debugger`, no commented-out experiments.
5. **Error sweep.** Every catch either handles, wraps with context, or rethrows. None just logs.
6. **Abstraction sweep.** Any layer with one caller? Inline it.
7. **Run the checker.** `python3 scripts/slopcheck.py --diff` (or the hook does it). Fix what it flags. If a finding is genuinely wrong, suppress it inline with a reason: `# slopcheck: ok — <why>`.

Then the summary you give the user is short: what changed, where, and anything you deliberately did not do. Not a tour.

## When to break the rules

1. **The project's own convention differs.** House style wins. Always.
2. **Genuinely non-obvious algorithm.** A novel invariant, a subtle proof, a hardware quirk. Two lines, or a linked reference.
3. **Regulated or safety-critical code** with a documentation standard. Follow the standard.
4. **The user asks for teaching comments.** Then comment generously — they asked. Do it well.
5. **Generated or vendored files.** Leave them alone.
