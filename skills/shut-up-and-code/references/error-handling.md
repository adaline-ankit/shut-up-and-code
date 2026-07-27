# Error handling

Load when writing a `try`, a `catch`, a guard, or a validation.

## The principle

**A crash with a stack trace is more useful than a silent wrong answer.**

Agent-written code inverts this. It wraps things in try/catch reflexively, logs the error, and continues — producing code that never crashes and is therefore impossible to debug, because the failure surfaces three layers away as a null, an empty list, or a wrong number with no trace of where it came from.

Catch an exception only when you can do one of three things:

1. **Handle it** — a real fallback that leaves the system correct.
2. **Add context and rethrow** — you know something the caller does not.
3. **Translate it** — convert a low-level error into a domain error at a boundary.

If none apply, let it propagate. Not catching is a decision, and usually the right one.

## Swallowed errors

```js
// The most common slop pattern in existence
try {
  const user = await fetchUser(id);
} catch (e) {
  console.error(e);
}
```

The function continues with `user` undefined. The caller gets nothing and no error. The bug appears somewhere else entirely, and the log line is in a file nobody is tailing.

```python
# Worse
try:
    parse(payload)
except Exception:
    pass
```

`except Exception: pass` says "any failure here is acceptable and unremarkable." That is almost never true, and when it genuinely is, it needs a comment saying which failures and why — the one case where a comment is mandatory rather than optional.

Fixed:

```python
try:
    parse(payload)
except ValueError as e:
    raise InvalidPayload(f"row {i}: {e}") from e
```

Specific exception, context added, chain preserved, propagates.

## Rules

**Catch specific types.** `except Exception`, `catch (e)` with no narrowing, and `rescue => e` catch programming errors — typos, wrong arities, `KeyboardInterrupt` — and hide them as if they were expected runtime conditions.

**Preserve the chain.** `raise X from e` in Python, `new Error(msg, { cause: e })` in JS, `fmt.Errorf("...: %w", err)` in Go. A rethrow that drops the original discards the only useful part.

**Never log-and-rethrow.** It produces the same error N times in the log at N levels. Log once, at the boundary that decides what the user sees.

**Do not catch at the point of the call** if the caller is better placed to decide. Handling belongs where a decision can be made, which is usually higher up.

**Fail fast on programmer error.** Bad arguments, impossible states, broken invariants — raise immediately and loudly. Do not "handle" a bug.

## Defensive padding

Guarding against states that cannot occur adds noise and, worse, tells the next reader those states *can* occur.

```ts
// The type says it's a string. Trust it or fix the type.
if (name === undefined || name === null || name === "") { ... }

// Chained existence checks: fix the type, or use optional chaining
if (res && res.data && res.data.items && res.data.items.length > 0) { ... }
```

Better: `res?.data?.items?.length` — or model it properly so the question cannot arise.

**Validate at the boundary, then trust.** Parse and check untrusted input once, at the edge — HTTP handler, CLI parser, file reader, queue consumer — and convert it into a type that cannot be invalid. Everything inside that boundary trusts its types. Re-checking the same value at every layer is the padding pattern, and it never actually catches anything because the check that mattered already happened.

Corollary: if you feel the need to guard deep inside the system, the real defect is that the boundary let the bad value through, or that the type is too loose. Fix that instead.

## Fallbacks that lie

```js
const config = loadConfig() ?? {};                 // silently runs unconfigured
const rate = parseFloat(input) || 1.0;             // "abc" becomes 1.0
const count = data?.total ?? 0;                    // failure looks like zero
```

Each converts a failure into a plausible-looking value, which then flows through the system as if it were real. A default is correct only when the default is genuinely correct — not as a way to avoid deciding.

`||` is especially dangerous in JS because `0` and `""` are falsy: `port || 3000` overrides a deliberate `0`. Use `??` when you mean "absent."

## Retries

Only around genuinely transient failures — network, rate limits, lock contention. Never around a logic error, and never on a non-idempotent operation without an idempotency key.

Needs backoff, a cap, and a final failure that propagates. A retry loop that gives up silently is a swallowed error with extra latency.

Do not add retries speculatively to a call that has never failed.

## Logging

Log at the boundary, not everywhere. Include the identifiers needed to find the record; exclude secrets, tokens, and personal data.

Use the project's logger at a real level. `console.log` and bare `print` in library code are debug leftovers, and the checker flags them.

## The test

For each `catch` you wrote: **if this fires in production at 3am, does the log tell someone what broke and where?** If not, either add context or stop catching.
