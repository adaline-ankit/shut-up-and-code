# Verify, don't guess

Load before asserting how an external library, API, or platform behaves — and before claiming work is done.

## The failure

[Documented](https://github.com/anthropics/claude-code/issues/72106): an agent with a logged-in browser session, the ability to read vendor docs, and web search used none of them. It reasoned from local source, asserted a confidently wrong architecture, and the paying user found all three root causes manually — for facts that were "a doc-read or a dashboard-look away."

Guessing is not faster. It is faster *to produce* and much slower to correct, because a wrong assertion sends the user down a path and costs a correction round trip on top of the work.

## Hallucinated dependencies are a real risk

Across 16 models and 576,000 generated samples, **19.7% of recommended packages did not exist**. That is not an edge case — one in five.

So: **never write an import you have not confirmed.** Confirm by checking the manifest (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`), the lockfile, or existing imports elsewhere in the repo. If a package genuinely needs adding, say so explicitly and let the user decide — do not slip a new dependency into a diff.

The same applies to what you import *from* a package. A real package with an invented export fails just as hard, and it looks more plausible.

## What must be verified, never assumed

- Function signatures, argument order, and return shapes
- Config keys, env var names, CLI flags
- API endpoints, request and response schemas, status codes
- Error types and what actually gets thrown
- Version-specific behaviour, and whether the project's pinned version has it
- Default values
- Whether a file, table, column, or route exists
- Platform limits and quotas

## How to check, cheapest first

1. **The repo.** Existing usage is the strongest evidence available — it is the version you actually have, in the configuration you actually run. Grep for the symbol.
2. **The lockfile.** Confirms the exact installed version before you reason about behaviour.
3. **Vendored source.** `node_modules`, `site-packages`, the module cache. The real implementation, not documentation about it.
4. **Type definitions.** `.d.ts`, stubs, protobufs. Machine-checked and version-accurate.
5. **Official docs**, matched to the installed version. Not the latest docs for an older pin — a top source of confident errors.
6. **Run it.** A REPL line or a scratch script settles most questions in seconds, with zero ambiguity.

Use the tools you have. If a browser session, a doc fetcher, or web search is available and the fact is load-bearing, use them before asserting.

## Say what you know

Three honest states, and they must be distinguishable in your output:

- **Verified** — "checked `node_modules/foo/index.d.ts`: the second argument is an options object."
- **Inferred** — "the codebase uses it this way in three places, so presumably X." Marked as inference.
- **Unknown** — "I don't know whether this version supports Y. One way to find out: ___."

Never let inference wear the voice of verification. Confident phrasing about an unchecked fact is the specific behaviour that erodes trust, because the user cannot tell your guesses from your knowledge — so eventually they have to check everything, and the assistance is worth nothing.

## False completion

Do not claim done without evidence.

- "Tests pass" → only after running them, with the output.
- "Fixed" → only after reproducing the failure and seeing it stop.
- "Works" → only after executing the path.

If you could not verify, say which part is unverified and how the user can check it in one command. An honest "implemented, not yet run — `npm test src/auth.spec.ts` will confirm" is worth more than a confident "done," and it costs you nothing.

## When the answer does not exist

Some things genuinely cannot be checked from here — a private API, a service that needs credentials, behaviour under production load. Say so, state what you assumed, and name the one experiment that resolves it.

An honest unknown is a normal engineering output. A fabricated certainty is a defect that outlives the session.
