# Comments

Load when writing or reviewing comments, or when a file's comment style needs a decision.

## The principle

Ousterhout's rule, and the only one that matters: **comments should describe what is not obvious from the code.** Not what the code does — what a reader cannot deduce by reading it.

This cuts both ways, and the second half gets forgotten. Comments are not failures to be minimised to zero; they are how you express things code genuinely cannot hold — an abstraction's contract, a unit, a boundary, a rejected alternative, a reason. A codebase with zero comments and non-obvious invariants is also badly documented.

The failure mode in agent-written code is never "too few." It is a wall of prose restating the mechanics of the line below.

## The test

Before writing, ask: **what does a competent reader lose if I delete this?**

- "Nothing" → delete
- "They'd read one more line" → delete, they can read
- "They'd have to guess why 30 seconds and not 60" → keep, one line
- "They'd reintroduce a bug we already fixed" → keep, one line, name the bug

## What earns a comment

| Category | Example |
|---|---|
| **Unit or range** | `// milliseconds, not seconds — the SDK is inconsistent` |
| **External constraint** | `// Gateway kills idle sockets at 35s; stay under it.` |
| **Non-obvious ordering** | `// Must run before migrate(); migrate() reads this table.` |
| **Rejected alternative** | `// Tried a set here; insertion order matters downstream.` |
| **Bug being worked around** | `// Safari fires resize twice on rotate (webkit #12345).` |
| **Source of a magic value** | `// 3500 req/s is the documented per-prefix S3 limit.` |
| **Deliberate deviation** | `// Half-even, not half-up, to match the finance ledger.` |
| **Genuine invariant** | `// Callers hold the lock; this must not acquire it.` |

Every one is a *why*. Every one is one line.

## What does not

Restating code. Narrating steps. Recording changes. Decorating with dividers. Filling with "note that." Apologising for placeholders. Explaining what a well-named function already announces.

If a comment starts with "This function," ask why the function's name is not carrying that.

## Length

**One line, under 80 characters.** Two only when a real constraint cannot compress. Never three.

Why the hard cap works: it forces you to identify the single fact worth stating. Multi-line comments are almost always one fact plus padding, or several facts that belong in different places.

When rationale genuinely needs a paragraph:

- **Commit message.** Best home for "why this change." It travels with the diff, and `git blame` finds it.
- **ADR.** For decisions affecting more than one file.
- **Docstring on a public API.** For contracts callers need.
- **Test name.** `test_rounds_half_even_to_match_ledger` documents the requirement and enforces it.

Not stacked above an implementation, where it goes stale silently and nobody updates it.

## Docstrings

A docstring earns its place by adding what a signature cannot.

```python
# Worthless — rephrases the signature
def get_user(user_id: str) -> User:
    """Gets a user by their user ID."""

# Earns it
def get_user(user_id: str) -> User:
    """Raises NotFound if soft-deleted; cached for 60s."""
```

Rules: one-line summary. Structured tags (`@param`, `Args:`) only when they carry constraints the types do not, and only when the project already uses them. Do not introduce a docstring convention a file does not have.

For internal helpers: usually no docstring. A good name and a small body are better documentation than prose.

## Match the house

**Read the file first. Count its comments.** Then match its density and its voice.

This overrides every preference here. A file that comments every public method gets a comment on your new public method. A file with none gets none. A project using `//!` module docs gets `//!`. Consistency is worth more than any individual rule, because inconsistency is what makes a codebase hard to read.

Check: the file, then its siblings in the directory, then the project's linter config, then `CONTRIBUTING.md`. If the project has a documented standard, it wins outright.

## Language notes

- **Python** — docstrings for public functions if the project does; `#` comments sparingly. Type hints replace most "what" comments.
- **TypeScript** — types replace most docstrings. Reserve JSDoc for published API surface where consumers see hovers.
- **Go** — doc comments on exported identifiers are conventional and start with the identifier name. That is the house style; follow it.
- **Rust** — `///` on public items, `//!` for modules. `# Examples` blocks are compiled and tested, so they carry real value.
- **Java** — Javadoc on public API is expected. Do not Javadoc private methods.
- **SQL** — comment the *reason* for an index or a hint, never the query mechanics.

## Cleaning existing comments

Only in files you are already editing, and only comments adjacent to your change. Do not open a PR that deletes 400 comments nobody asked about — unreviewable diff is its own failure.

When you do remove one, do it silently as part of the change. No announcement, no `// removed redundant comment`.
