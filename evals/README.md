# Evals

Two layers: the checker is tested automatically, the skill's behaviour is judged against a rubric.

## Automated

```bash
python3 scripts/test_slopcheck.py
```

Six test groups over the samples in [`samples/`](samples/):

| Group | Asserts |
|---|---|
| `must_fire` | Every rule fires on `slop.ts` / `slop.py` |
| `must_be_clean` | **Zero** findings on `clean.ts`, `clean.py`, `good-docs.ts`, `suppressed.py` |
| `self_clean` | The checker and this test file pass the checker's own rules |
| `exit_codes` | 1 on slop, 0 on clean |
| `hook_mode` | Reads a hook event from stdin, writes findings to stderr, exits 1 |
| `redundancy_heuristic` | Five known-redundant comment/code pairs flagged, four known-useful ones spared |

Runs in CI on every push.

## Samples

| File | Role |
|---|---|
`slop.ts` | Every detectable TypeScript pattern in one file |
`slop.py` | Redundant and over-long Python docstrings |
`clean.ts` | Tight code with one genuinely useful why-comment |
`clean.py` | Module docstring, a sourced magic number, no noise |
`good-docs.ts` | Legitimate JSDoc with `@param`/`@returns` — **must not** be flagged |
`suppressed.py` | A real swallowed-error suppressed with a reason — **must not** be flagged |

The last two exist because they are the failure modes that would kill adoption. A checker that flags valid JSDoc, or ignores a documented suppression, gets uninstalled within a day.

## Behavioural

30 cases in [`cases.jsonl`](cases.jsonl), scored with [`rubric.md`](rubric.md).

| Family | Cases | Failure it catches |
|---|---|---|
| `comment-*` | 3 | Redundant comments, mechanics over rationale |
| `no-narration` / `no-changelog` | 2 | Step tours and history in the source |
| `docstring-*` | 2 | Docstrings that rephrase signatures |
| `house-style-*` | 2 | **Zealotry** — stripping comments a project requires |
| `restraint-*` | 3 | One-line changes arriving as checklists; abstraction at one call site |
| `scope-creep-*` | 2 | Unreviewable mixed diffs |
| `ssot-*` | 2 | Duplicating a constant that already exists |
| `error-*` | 3 | Swallowed errors, defensive padding, fallbacks that lie |
| `verify-*` | 2 | Invented signatures and unconfirmed imports |
| `no-false-completion` | 1 | Claiming tests pass without running them |
| `checker-*` | 2 | Ignoring the checker; suppressing without a reason |
| `*-exception-*` | 2 | **Over-correction** — refusing to comment when code warrants it |
| `cleanup` / `silent-deletion` / `generated-file` | 3 | Lecturing the user; editing generated files |

Both directions are tested on purpose. `house-style-*` and `teaching-exception-1` catch a skill that has become a zealot; `comment-restraint-*` catch one that is a no-op. Passing only one is failing.
