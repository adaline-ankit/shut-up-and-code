# The slop catalogue

Every pattern the checker detects, plus the ones only judgement catches. Rule IDs match `scripts/slopcheck.py` output.

"Slop" is not broken code. It is code that works and is indifferent to the system it lands in: padded, over-defended, over-explained, stylistically foreign. It passes tests and costs the next reader real time.

## Comments

| Rule | Pattern | Fix |
|---|---|---|
| `redundant-comment` | Comment restates the line below | Delete |
| `comment-block` | ≥3 consecutive comment lines, or a ≥4-line block | Collapse to one line, or move to commit/ADR/docstring |
| `redundant-docstring` | Doc block rephrases the signature | Delete, or replace with contract info |
| `step-narration` | `// Step 1:`, `// First we...` | Delete |
| `changelog-comment` | `// NEW:`, `// Changed from`, `// as requested` | Delete — git holds history |
| `section-divider` | `// ===== Helpers =====` | Delete — structure comes from functions and files |
| `filler-comment` | `// Note that`, `// This simply` | Delete the preamble; keep any fact in ≤80 chars |
| `commented-out-code` | Dead code behind a comment marker | Delete |
| `bare-todo` | `// TODO: fix` with no owner or issue | Add a reference, or do it |
| `comment-too-long` | Single comment over 100 chars | Compress, or the code needs simplifying |
| `emoji-in-comment` | Emoji in source | Remove |

## Logging and debugging

| Rule | Pattern | Fix |
|---|---|---|
| `debug-logging` | `console.log`, `print(`, `debugger`, `pdb.set_trace` | Delete, or use the project logger at a real level |
| `entry-exit-logging` | `log("entering foo")`, `log("=== done ===")` | Delete — tracing is instrumentation's job |

Debug output left in source is the most common slop in shipped diffs, and the easiest to catch. Test files are exempt.

## Error handling

| Rule | Pattern | Fix |
|---|---|---|
| `swallowed-error` | `catch { log(e) }`, `except: pass` | Handle, wrap with context, or rethrow |
| `defensive-guard` | `if (a && a.b && a.b.c)` | Optional chaining, or fix the type |

See `error-handling.md`. The through-line: **a crash with a stack trace beats a silent wrong answer.**

## Redundancy

| Rule | Pattern | Fix |
|---|---|---|
| `redundant-boolean` | `x === true`, `y == False`, `? true : false` | Use the value |

## Judgement-only

The checker cannot see these. You have to.

### Unnecessary abstraction
A factory for one product. A strategy interface with one strategy. A `BaseHandler` with one subclass. A `utils/` module holding one function used once.

**Rule of three:** no abstraction until three real call sites exist. Two is a coincidence.

### Premature generality
Config options nobody requested. A plugin system for a script. `Optional[Dict[str, Any]]` parameters that are always the same shape. Generic type parameters with one instantiation.

Every unused axis of flexibility is code to read, test, and maintain, forever, for nothing.

### Duplicated source of truth
A constant, path, URL, or type redefined instead of imported. Compounds across sessions until a one-line bug needs fixing in four files. See `reuse-and-ssot.md`.

### Reimplemented stdlib
Hand-rolled `groupBy`, `chunk`, `debounce`, `deepClone`, `retry` when the language, framework, or an existing project helper already has one. Search before writing.

### Wrapper with no value
```js
function getUser(id) { return api.getUser(id); }
```
Adds a name, a stack frame, and a file to maintain. Delete it.

### Ceremony
Getters and setters over public fields in languages where properties exist. Interfaces for internal classes. DTOs that mirror the model exactly. Builders for three-field structs.

### Test theatre
Tests asserting mocks were called rather than behaviour. `expect(true).toBe(true)`. Tests that restate the implementation, so they pass whatever the code does and fail whenever it is refactored.

### Scope creep
Renames, reformats, "improvements" to adjacent code, and dependency bumps nobody asked for. Mixed into a feature diff, they make review impossible and bury the actual change.

### Confident guessing
Asserting an API's behaviour without checking. Inventing flags, config keys, and signatures that look plausible. Roughly 1 in 5 LLM-recommended package names do not exist — an unverified import is a live risk. See `verification.md`.

### False completion
"Done, all tests pass" without running them. "Fixed" without reproducing. This destroys trust faster than any bug.

## Severity

**High** — ships wrong behaviour or is guaranteed noise: swallowed errors, debug logging, redundant comments, comment blocks, commented-out code, duplicated truth, confident guessing, false completion.

**Medium** — costs maintenance: filler, bare TODOs, defensive guards, unnecessary abstraction, entry/exit logging.

**Low** — style: redundant booleans, emoji.

Fix high before finishing. Fix medium in code you are already touching. Note low, do not crusade.
