# Reuse and single source of truth

Load before adding any constant, path, type, helper, or config value.

## The compounding failure

[Documented](https://github.com/anthropics/claude-code/issues/37137) behaviour: each session defines the same constant, path, or helper again in a new file rather than checking whether it exists. Session 1 hardcodes `settings.json`. Session 2 hardcodes it somewhere else. Session 5 has five copies, and a one-line change now needs five edits in places nobody has an inventory of — so one gets missed, and the resulting bug is nearly undiagnosable because the two code paths disagree about a value that "obviously" matches.

This is the single worst long-horizon habit in agent-written code, because **it is invisible in any individual diff.** Every session's contribution looks fine. Only the accumulation is fatal, and by then no single change caused it.

## Search first

Before adding anything named, search. It costs one tool call.

| Adding | Search for |
|---|---|
| A constant | The literal value **and** plausible names |
| A file path | The filename string, anywhere |
| A URL or endpoint | The domain, the path fragment |
| A type or interface | The shape's field names, not just the type name |
| A utility function | What it *does*, not what you would call it |
| An env var | The variable name, and the config loader |
| A dependency | `package.json` / `pyproject.toml` / `go.mod` for something equivalent |

Search the value, not only the name — `"settings.json"` finds copies that `SETTINGS_PATH` misses. That asymmetry is exactly how duplicates survive a careless search.

Where to look, in order: the config or constants module, the directory you are editing, its siblings, then the whole repo. Also check the language's standard library and dependencies already installed — hand-rolling `groupBy`, `chunk`, `retry`, or `deepClone` when a dependency already exports it is the same failure wearing different clothes.

## When you find a duplicate

You found the value defined twice while doing something else.

1. **Do not add a third.** Reference one of the existing definitions.
2. **Say so in one line.** "`settings.json` is hardcoded in `config.ts:12` and `loader.ts:40`. Using the first. Worth consolidating separately?"
3. **Do not silently refactor both** into a new module as part of an unrelated change. That is scope creep, and it makes the diff unreviewable.

If consolidating *is* the task, then do it properly: establish the single source, update every reference, and verify nothing still holds a private copy.

## What belongs in one place

- Paths, filenames, directory names
- URLs, endpoints, hostnames
- Timeouts, limits, retry counts, page sizes
- Regexes used more than once
- Error messages shown to users
- Enum values and status strings
- Feature flag names
- Anything appearing in both code and tests

Test files copying a production constant is duplication too — and the worst kind, because it makes the test pass while production is wrong.

## Where to put it

Follow the project. If it has `constants.ts`, `settings.py`, or a config module, use that. Do not create a second convention.

If nothing exists, put the value in the module that owns the concept and export it. Do not open a `constants/` directory for one value — that is its own kind of premature structure.

## Types are truth too

The same rule governs types. A second `User` interface with the same fields, declared because importing felt like effort, means the two definitions will drift and the compiler will not tell you which is right.

Derive rather than redeclare: `Pick<User, "id" | "email">` beats a new shape. Generated API types beat hand-written mirrors of them.

## The check before you finish

For every name you added: did this already exist somewhere in the repo? If you did not search, you do not know — and "I do not think so" is not an answer to a question one grep resolves.
