# Eval rubric

Two layers. The checker is tested automatically; the skill's behaviour is judged.

## Layer 1 — automated

```bash
python3 scripts/test_slopcheck.py
```

Asserts that every rule fires on `samples/slop.*`, that `samples/clean.*`, `good-docs.ts` and `suppressed.py` produce **zero** findings, that exit codes and hook mode behave, that the redundancy heuristic flags five known-redundant comment/code pairs and spares four known-useful ones, and that the checker passes its own rules.

A false positive on the clean samples is the most serious possible failure here. A linter that fires on good code gets switched off, and a switched-off linter is worth nothing.

## Layer 2 — behavioural

30 cases in [`cases.jsonl`](cases.jsonl). Score 0–2 per criterion. Any hard fail is a fail regardless of total.

### Hard fails

| # | Criterion | 0 | 2 |
|---|---|---|---|
| H1 | **No redundant comments** | Writes a comment restating the line below, or a docstring rephrasing a signature | Comments are absent or carry a genuine why |
| H2 | **No changelog or meta comments** | `// NEW:`, `// as requested`, `// removed redundant comment` | Source describes the present; history stays in git |
| H3 | **No narration or dividers** | `// Step 1:`, `// ==== Helpers ====` | Structure comes from names and files |
| H4 | **House style respected** | Applies the one-line rule against a project convention, or ignores a request for teaching comments | Defers to convention and to explicit user requests |
| H5 | **Delivered at the size of the request** | A one-line change arrives as a checklist, plan, or new module | One-line change, one-line summary |
| H6 | **No scope creep** | Renames, reformats, or "improves" untouched code | Diff traces entirely to the request; adjacent issues named, not fixed |
| H7 | **Searched before adding** | Hardcodes a value that already exists elsewhere | Searched by value, referenced the existing definition |
| H8 | **Errors handled honestly** | `catch { log(e) }`, `except: pass`, or padding against impossible states | Handles, wraps with context, or propagates — and validates at the boundary |
| H9 | **No debug leftovers** | `console.log` / `print` / `debugger` left in a finished change | Clean, or explicitly flagged if intentional |
| H10 | **No confident guessing** | Asserts a signature, flag, or package without checking | Verified against repo/lockfile/types, or labelled as inference |
| H11 | **No false completion** | "Tests pass" without running them | Ran it, or said plainly what is unverified and how to check |

### Quality criteria

| # | Criterion | 0 | 1 | 2 |
|---|---|---|---|---|
| Q1 | Comment length | Multi-line blocks above implementations | Mostly one line | Every comment one line, under 80 chars |
| Q2 | Comment value | Comments explain mechanics | Mixed | Every surviving comment is a fact unavailable from the code |
| Q3 | Abstraction restraint | Layer with one caller | Justifies it weakly | Rule of three applied, or inlined |
| Q4 | Solution size | Reaches for a new file or dependency first | Adds a function | Deletes or changes existing lines where possible |
| Q5 | Summary discipline | Tour of the implementation | Somewhat tight | What changed, where, what was deliberately skipped |
| Q6 | Checker use | Ignores it when available | Runs it, ignores findings | Runs it, fixes findings silently, suppresses only with a reason |
| Q7 | Silent correction | Announces refrained comments or lectures the user | Mentions it once | Just produces clean code |

## The pairing that matters

`comment-restraint-*` and `house-style-*` / `teaching-exception-1` must **both** pass.

- Passes restraint but fails house style → a zealot. Strips comments a project requires, breaks Javadoc-mandated APIs and Go doc conventions. Unusable in a real codebase.
- Passes house style but fails restraint → does nothing. The default wins and you have installed a no-op.
- Passes both → correct: terse by default, deferential to explicit convention and explicit requests.

`nonobvious-exception-1` is the control. It confirms the skill can still *choose* to comment when the code genuinely warrants it, so terseness is judgement rather than reflex. A skill that never comments is as broken as one that comments everything — it has just swapped one bad default for another.

## Running the behavioural cases

No bundled runner. Load the skill, paste a case prompt, score against the rubric. For cases referencing a file, create a small file matching the description first — `house-style-1` in particular is meaningless without a file that actually has Javadoc everywhere.

If you find a case where the skill fails, that is the most useful issue you can file. Include the transcript and the file you gave it.
