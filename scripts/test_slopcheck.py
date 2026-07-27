#!/usr/bin/env python3
"""Assert slopcheck fires on the fixtures it should and stays quiet on the rest.

Run: python3 scripts/test_slopcheck.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "slopcheck.py"
SAMPLES = ROOT / "evals" / "samples"

# sample -> rules that must be present
MUST_FIRE = {
    "slop.ts": {"section-divider", "redundant-comment", "comment-block",
                "step-narration", "debug-logging", "swallowed-error",
                "changelog-comment", "commented-out-code", "filler-comment",
                "defensive-guard", "bare-todo", "redundant-boolean"},
    "slop.py": {"comment-block"},
}

# samples that must produce nothing at any severity
MUST_BE_CLEAN = ["clean.ts", "clean.py", "good-docs.ts", "suppressed.py"]

failures: list[str] = []


def findings_for(path: Path) -> list[dict]:
    r = subprocess.run(
        [sys.executable, str(CHECKER), str(path), "--json", "--fail-on", "never"],
        capture_output=True, text=True)
    if r.returncode != 0:
        failures.append(f"{path.name}: checker exited {r.returncode}\n{r.stderr}")
        return []
    return json.loads(r.stdout)["findings"]


def test_must_fire() -> None:
    for name, expected in MUST_FIRE.items():
        got = {f["rule"] for f in findings_for(SAMPLES / name)}
        missing = expected - got
        if missing:
            failures.append(f"{name}: expected rules not fired: {sorted(missing)}")


def test_must_be_clean() -> None:
    for name in MUST_BE_CLEAN:
        got = findings_for(SAMPLES / name)
        if got:
            detail = ", ".join(f"L{f['line']} {f['rule']}" for f in got)
            failures.append(f"{name}: expected clean, got {detail}")


def test_self_clean() -> None:
    """The checker must satisfy its own rules — see README."""
    for target in (CHECKER, Path(__file__)):
        if findings_for(target):
            failures.append(f"{target.name}: checker does not pass its own rules")


def test_exit_codes() -> None:
    cases = [(SAMPLES / "slop.ts", 1), (SAMPLES / "clean.ts", 0)]
    for path, expected in cases:
        r = subprocess.run([sys.executable, str(CHECKER), str(path), "-q"],
                           capture_output=True, text=True)
        if r.returncode != expected:
            failures.append(f"{path.name}: exit {r.returncode}, expected {expected}")


def test_hook_mode() -> None:
    event = json.dumps({"tool_name": "Edit",
                        "tool_input": {"file_path": str(SAMPLES / "slop.ts")}})
    r = subprocess.run([sys.executable, str(CHECKER), "--hook", "-q"],
                       input=event, capture_output=True, text=True)
    if r.returncode != 1:
        failures.append(f"hook mode: exit {r.returncode}, expected 1")
    if "finding" not in r.stderr:
        failures.append("hook mode: findings should go to stderr for the agent to read")


def test_redundancy_heuristic() -> None:
    """Unit-level checks on the rule that does the most work."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from slopcheck import restates_code  # noqa: PLC0415

    redundant = [
        ("Initialize the counter", "let counter = 0;"),
        ("Return the result", "return result;"),
        ("Loop through the users", "for (const user of users) {"),
        ("Set the timeout", "const timeout = 30_000;"),
        ("Gets a user by id", "def get_user(user_id):"),
    ]
    useful = [
        ("Gateway kills idle sockets at 35s; stay under it.", "const timeout = 30_000;"),
        ("Half-even to match the finance ledger.", "const total = round(sum);"),
        ("Sorted by ID so pagination cursors stay stable.", "for (const u of users) {"),
        ("webkit #12345: Safari fires resize twice on rotate.", "el.addEventListener('resize', f);"),
    ]
    for comment, code in redundant:
        if not restates_code(comment, code):
            failures.append(f"redundancy: should flag {comment!r} over {code!r}")
    for comment, code in useful:
        if restates_code(comment, code):
            failures.append(f"redundancy: should NOT flag {comment!r} over {code!r}")


def main() -> int:
    for fn in (test_must_fire, test_must_be_clean, test_self_clean,
               test_exit_codes, test_hook_mode, test_redundancy_heuristic):
        fn()

    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("slopcheck tests: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
