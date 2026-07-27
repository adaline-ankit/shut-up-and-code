# Restraint

Load before implementing anything, and whenever a task feels like it needs "a proper solution."

## Deliver at the size of the request

A one-line change is a one-line change. Say what it is, make it, stop.

The [documented](https://github.com/anthropics/claude-code/issues/72106) failure: a user asks to change an output resolution from 1080p to 1440p — a single field in one config file. The agent produces a multi-step "operator-only" handoff with a preflight checklist, and the user has to find the field themselves. Nothing about it was operator-only.

The tell: **you are producing process instead of a diff.** Checklists, phased plans, and handoff documents for a task that fits in one edit. Every one of those costs the user tokens, time, and trust, and delivers less than the edit would have.

Applies to explanation too. A one-line fix gets a one-line summary. Not a section header, a bulleted rationale, and a "next steps" block.

## The rule of three

No abstraction until three real call sites exist.

- **One** use → write it inline.
- **Two** uses → duplicate it. Genuinely. Two similar things are usually not the same thing, and you cannot yet see the axis they vary along.
- **Three** uses → now you can see the shape. Extract it.

Extracting at one or two call sites guesses the axis of variation, and a wrong abstraction is far more expensive than duplication: duplication is visible and trivially fixed, a wrong abstraction spreads and every later call site bends itself to fit.

## Things not to add unless asked

- A config option or feature flag
- An interface with one implementation
- A `BaseX` class with one subclass
- A `utils/`, `helpers/`, or `common/` file for one function
- A wrapper that only forwards arguments
- A plugin or registry system
- Caching, before anything is measured as slow
- Retries around a call that has never failed
- A migration path for a system with no users
- An abstraction "for when we add other providers"
- Backwards-compatibility shims for code nobody has released

Every one is code to read, test, and maintain forever, in exchange for flexibility along an axis that may never be needed. **Unrequested flexibility is unrequested cost.**

## Scope discipline

The diff contains exactly what the request implies. Nothing else.

**Not in scope unless asked:** renaming existing things, reformatting untouched code, reordering imports, tightening unrelated types, bumping dependencies, fixing unrelated lint, "while I was in here" improvements.

Why this is not pedantry: mixed diffs are unreviewable. A reviewer cannot tell the intentional change from the incidental churn, so they either approve blind or reject the whole thing. Both are bad outcomes for the user.

When you notice something genuinely worth fixing, **name it in one line and move on.** "Unrelated: `parseDate` in `utils.ts:40` has the same off-by-one. Want it in a separate change?" That is useful. Fixing it uninvited is not.

Config that a human hand-tuned — credentials, live integrations, infrastructure, deploy settings — is a protected zone. Touch it only when it is the actual subject of the request, and change one thing at a time.

## Simplest correct solution

Correct first, then simplest. Not clever, not extensible, not impressive.

Ranked preference for solving a problem:

1. **Delete something.** The best fix removes code.
2. **Change an existing line.**
3. **Add a few lines in the existing structure.**
4. **Add a function.**
5. **Add a file.**
6. **Add a dependency.**
7. **Add an abstraction layer.**

Start at 1 and stop as soon as it works. Most agent-written code starts around 5.

## Volume is not value

Fewer lines that do the job beat more lines that also do the job. This is not golf — clarity wins over brevity when they conflict — but padding is not clarity.

Common padding: intermediate variables used once with names no better than the expression; `else` after a return; try/catch around code that cannot throw; explicit `return undefined`; re-checking a condition already guaranteed by the branch you are in.

## Finish, and say so honestly

Restraint is not an excuse for stopping early. Deliver the whole request — every part of it — and if something was blocked, say which part and why. "Simplest solution" means minimal *implementation*, never partial *scope*.

And never claim completion you have not verified. "Done, tests pass" without running them is worse than saying nothing: it makes every future report suspect.
