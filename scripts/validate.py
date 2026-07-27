#!/usr/bin/env python3
"""Structural checks for the shut-up-and-code plugin.

Validates that every manifest parses, the eval cases are well formed, every
reference file the skill points at actually exists, and the Cursor copy has not
drifted from the source skill.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "shut-up-and-code"
CURSOR_SKILL = ROOT / ".cursor" / "skills" / "shut-up-and-code"

MANIFESTS = [
    "plugin.json",
    "gemini-extension.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
]

REQUIRED_FRONTMATTER = ("name", "description")

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def check_manifests() -> None:
    for rel in MANIFESTS:
        path = ROOT / rel
        if not path.exists():
            fail(f"missing manifest: {rel}")
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            fail(f"{rel}: invalid JSON — {exc}")
            continue
        if data.get("name") != "shut-up-and-code":
            fail(f"{rel}: name should be 'shut-up-and-code', got {data.get('name')!r}")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    block = text[4:end]
    out: dict[str, str] = {}
    for line in block.splitlines():
        if line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def check_skill() -> None:
    path = SKILL / "SKILL.md"
    if not path.exists():
        fail("missing skills/shut-up-and-code/SKILL.md")
        return
    text = path.read_text()

    fm = parse_frontmatter(text)
    if fm is None:
        fail("SKILL.md: missing or malformed YAML frontmatter")
        return
    for key in REQUIRED_FRONTMATTER:
        if key not in fm:
            fail(f"SKILL.md: frontmatter missing '{key}'")
    if fm.get("name") != "shut-up-and-code":
        fail(f"SKILL.md: frontmatter name is {fm.get('name')!r}")

    # Every references/foo.md and assets/foo mentioned must exist.
    md_files = [path, *sorted((SKILL / "references").glob("*.md")), ROOT / "AGENTS.md", ROOT / "README.md"]
    for md in md_files:
        body = md.read_text()
        for ref in set(re.findall(r"references/([A-Za-z0-9._-]+\.md)", body)):
            if not (SKILL / "references" / ref).exists():
                fail(f"{md.relative_to(ROOT)}: points at missing references/{ref}")
        for asset in set(re.findall(r"assets/([A-Za-z0-9._-]+)", body)):
            if not (ROOT / "assets" / asset).exists():
                fail(f"{md.relative_to(ROOT)}: points at missing assets/{asset}")

    # Every reference file must be reachable from the skill's reference map.
    listed = set(re.findall(r"references/([A-Za-z0-9._-]+\.md)", text))
    for ref in sorted((SKILL / "references").glob("*.md")):
        if ref.name not in listed:
            fail(f"SKILL.md: reference file {ref.name} exists but is not listed in the reference map")


def check_cursor_sync() -> None:
    if not CURSOR_SKILL.exists():
        fail("missing .cursor/skills/shut-up-and-code (run scripts/sync-cursor.sh)")
        return
    for src in sorted(p for p in SKILL.rglob("*") if p.is_file()):
        mirror = CURSOR_SKILL / src.relative_to(SKILL)
        if not mirror.exists():
            fail(f"cursor copy missing {src.relative_to(SKILL)}")
        elif mirror.read_bytes() != src.read_bytes():
            fail(f"cursor copy out of sync: {src.relative_to(SKILL)}")


def check_evals() -> None:
    path = ROOT / "evals" / "cases.jsonl"
    if not path.exists():
        fail("missing evals/cases.jsonl")
        return
    seen: set[str] = set()
    for i, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"evals/cases.jsonl:{i}: invalid JSON — {exc}")
            continue
        for key in ("id", "prompt", "expects"):
            if key not in case:
                fail(f"evals/cases.jsonl:{i}: missing '{key}'")
        case_id = case.get("id")
        if case_id in seen:
            fail(f"evals/cases.jsonl:{i}: duplicate id {case_id!r}")
        seen.add(case_id)


def main() -> int:
    check_manifests()
    check_skill()
    check_cursor_sync()
    check_evals()

    if failures:
        print(f"FAILED ({len(failures)} problem(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("OK — manifests, skill, references, cursor copy, and evals all valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
