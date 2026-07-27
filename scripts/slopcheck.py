#!/usr/bin/env python3
"""slopcheck — flag AI-slop patterns in source files.

Deterministic, dependency-free, language-aware enough to be useful across the
languages people actually pair with a coding agent. Designed to run three ways:

    slopcheck.py src/foo.ts src/bar.py     explicit paths
    slopcheck.py --diff                    files changed vs HEAD
    slopcheck.py --diff main               files changed vs a base branch
    slopcheck.py --hook                    read a Claude Code hook event on stdin

Exit codes: 0 clean · 1 findings at or above the fail threshold · 2 bad usage.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SLASH = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".java", ".c", ".h",
         ".cc", ".cpp", ".hpp", ".cs", ".go", ".rs", ".swift", ".kt", ".kts",
         ".scala", ".php", ".dart", ".m", ".mm", ".proto", ".sol"}
HASH = {".py", ".rb", ".sh", ".bash", ".zsh", ".pl", ".r", ".jl", ".nim",
        ".ex", ".exs", ".cr", ".tf", ".hcl"}
DASH = {".sql", ".lua", ".hs", ".elm", ".ada"}

SKIP_DIRS = {"node_modules", "vendor", "dist", "build", "target", ".git",
             "__pycache__", ".venv", "venv", "third_party", "generated",
             ".next", "coverage", "migrations"}
SKIP_SUFFIX = (".min.js", ".min.css", ".lock", ".map", ".snap", ".pb.go",
               "_pb2.py", ".g.dart", ".generated.ts")

TEST_HINTS = ("test", "spec", "fixture", "conftest", "__tests__", "e2e")


def comment_prefixes(path: Path) -> tuple[str, ...]:
    ext = path.suffix.lower()
    if ext in SLASH:
        return ("//",)
    if ext in HASH:
        return ("#",)
    if ext in DASH:
        return ("--",)
    return ()


SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Finding:
    path: str
    line: int
    rule: str
    severity: str
    message: str
    fix: str
    excerpt: str = ""

    def as_dict(self) -> dict:
        return {"path": self.path, "line": self.line, "rule": self.rule,
                "severity": self.severity, "message": self.message,
                "fix": self.fix, "excerpt": self.excerpt}


@dataclass
class FileReport:
    path: str
    findings: list[Finding] = field(default_factory=list)


# Broad on purpose: a false negative loses one comment, a false positive loses a useful one.
STOPWORDS = {
    "a", "an", "the", "this", "that", "these", "those", "it", "its", "is",
    "are", "was", "were", "be", "being", "been", "to", "of", "in", "on", "for",
    "with", "and", "or", "if", "then", "we", "our", "you", "your", "will",
    "should", "can", "here", "now", "so", "as", "at", "by", "from", "into",
    "up", "down", "out", "all", "any", "each", "new", "not", "no", "s",
    # verbs that describe the mechanical act the code already shows
    "set", "sets", "setting", "get", "gets", "getting", "return", "returns",
    "returning", "create", "creates", "creating", "make", "makes", "add",
    "adds", "adding", "initialize", "initialise", "initializes", "init",
    "define", "defines", "declare", "declares", "call", "calls", "calling",
    "loop", "loops", "iterate", "iterates", "check", "checks", "checking",
    "assign", "assigns", "store", "stores", "update", "updates", "convert",
    "converts", "parse", "parses", "build", "builds", "instance", "value",
    "values", "variable", "function", "method", "class", "object", "result",
    "data", "list", "array", "dict", "map", "string", "number", "boolean",
    "true", "false", "none", "null", "over", "through", "each", "item",
    "items", "element", "elements", "key", "keys", "empty", "first", "last",
}

IDENT_SPLIT = re.compile(r"[^A-Za-z0-9]+")
CAMEL_SPLIT = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def tokenize(text: str) -> set[str]:
    """Lowercase word set, splitting identifiers on camelCase and separators."""
    out: set[str] = set()
    for chunk in IDENT_SPLIT.split(text):
        if not chunk:
            continue
        for piece in CAMEL_SPLIT.split(chunk):
            word = piece.lower()
            if len(word) > 1:
                out.add(word)
                if word.endswith("s") and len(word) > 3:
                    out.add(word[:-1])
    return out


def restates_code(comment: str, code: str) -> bool:
    """True when the comment adds no vocabulary the adjacent code lacks."""
    c_tokens = tokenize(comment) - STOPWORDS
    if not c_tokens:
        return True
    if len(c_tokens) > 6:
        return False
    code_tokens = tokenize(code)
    novel = {t for t in c_tokens if t not in code_tokens}
    # Also treat near-misses as matches: "retries" vs "retry", "config" vs
    # "configuration". Substring containment in either direction is enough.
    novel = {t for t in novel
             if not any(t in ct or ct in t for ct in code_tokens if len(ct) > 3)}
    return not novel


DIVIDER_GLYPHS = "-=*_#~/+.─━│═╌┄┈▬▔●◆★<>"
DIVIDER = re.compile(r"^[\s" + re.escape(DIVIDER_GLYPHS) + r"]{8,}$")


def is_divider(body: str) -> bool:
    """A rule, with or without a label sitting in the middle of it."""
    if DIVIDER.match(body):
        return True
    return sum(c in DIVIDER_GLYPHS for c in body) >= 6
STRING_LITERAL = re.compile(
    r'"(?:[^"\\\n]|\\.)*"' r"|'(?:[^'\\\n]|\\.)*'" r"|`(?:[^`\\]|\\.)*`")
SUPPRESS = re.compile(r"slopcheck:\s*(ok|ignore|disable)\b([^\n]*)", re.I)
NARRATION = re.compile(
    r"^(step\s*\d|\d\)|\d\.|first|second|third|next|then|now|finally|lastly)\b",
    re.I)
CHANGELOG = re.compile(
    r"^(new|added|add|changed|change|updated|update|removed|remove|fixed|fix|"
    r"refactored|renamed|moved|deprecated)\b[:\s]|^(v\d|as requested|per your|"
    r"as discussed|changed from|was previously|previously|old:|before:)",
    re.I)
AI_VOICE = re.compile(
    r"\b(note that|please note|it'?s worth noting|worth noting|keep in mind|"
    r"as you can see|here we|we will|let'?s|this (function|method|class|code|"
    r"block|line|variable) (simply|just|basically|essentially)|"
    r"in order to|for clarity|self[- ]explanatory|"
    r"(placeholder|dummy|example) (implementation|for now)|"
    r"in a real (world |production )?(implementation|app|system|scenario))\b",
    re.I)
BARE_TODO = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b(?!\s*[\(:\[]?\s*"
                       r"(#\d|[A-Z]{2,}-\d|@\w|https?://))")
CODEISH = re.compile(
    r"(;\s*$)|(^\s*(if|for|while|return|const|let|var|def|func|class|import|"
    r"from|public|private|else)\b.*[:{(])|(\w+\s*=\s*[\w\"'\[{].*)|(\w+\([^)]*\)\s*[;{]?$)")
DEBUG_LOG = re.compile(
    r"\b(console\.(log|debug|dir|trace)|debugger|pdb\.set_trace|"
    r"breakpoint\(\)|binding\.pry|var_dump|dd\(|dump\(|fmt\.Print(ln)?|"
    r"System\.out\.print(ln)?|dbg!)\s*\(?")
ENTRY_EXIT_LOG = re.compile(
    r"(log|print|console)\w*\s*\(\s*[\"'`].{0,20}"
    r"(entering|exiting|start(ing|ed)?\b|begin\b|called|invoked|"
    r"===|--- |>>>|\bdone\b|finished|end of)",
    re.I)
REDUNDANT_BOOL = re.compile(
    r"(==|!=|===|!==)\s*(true|false|True|False)\b|"
    r"\?\s*true\s*:\s*false|\?\s*false\s*:\s*true")
TRIPLE_GUARD = re.compile(
    r"if\s*\(?\s*(\w+(?:\.\w+)?)\s*&&\s*\1\.\w+\s*&&\s*\1\.\w+\.\w+")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️]")
CATCH_OPEN = re.compile(
    r"\b(catch\s*\(|except\b|rescue\b|catch\s*\{|\bif\s+err\s*!=\s*nil)")
ONLY_LOG_OR_PASS = re.compile(
    r"^\s*(pass|continue|return( (None|nil|null|false))?|"
    r"(console\.\w+|print|printf|log(ger)?\.\w+|logging\.\w+|"
    r"fmt\.Print\w*|System\.out\.\w+)\s*\(.*\)?;?)\s*;?\s*$")


# JSDoc @tags plus Google/NumPy section headers: contract info, exempt from the length rule.
DOC_TAG = re.compile(
    r"@(param|arg|returns?|rtype|throws|raises|exception|type|template|typedef|"
    r"example|deprecated|see|link|override|inheritdoc|since|yields?)\b"
    r"|^\s*(Args|Arguments|Params|Parameters|Returns|Yields|Raises|Throws|"
    r"Attributes|Examples?|Notes?|Warns|Warnings?|See Also|References)\s*:?\s*$"
    r"|^\s*-{3,}\s*$",
    re.I | re.M)
SIGNATURE = re.compile(
    r"\b(function|def|class|const|let|var|public|private|protected|static|"
    r"async|export|fn|func|sub|method)\b")


@dataclass
class Block:
    start: int          # 1-indexed first line
    end: int            # 1-indexed last line
    body: str           # prose with delimiters stripped
    kind: str           # "block" or "docstring"


def find_blocks(lines: list[str], path: Path) -> list[Block]:
    """Locate /* ... */ and Python triple-quoted comment spans."""
    ext = path.suffix.lower()
    blocks: list[Block] = []

    if ext in SLASH:
        i = 0
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith("/*"):
                start, parts = i, []
                while i < len(lines):
                    parts.append(lines[i])
                    if "*/" in lines[i] and not (i == start and lines[i].strip() == "/*"):
                        break
                    i += 1
                raw = "\n".join(parts)
                prose = re.sub(r"^\s*/?\*+/?", "", raw, flags=re.M)
                prose = prose.replace("*/", "").strip()
                blocks.append(Block(start + 1, min(i, len(lines) - 1) + 1, prose, "block"))
            i += 1

    elif ext == ".py":
        i = 0
        in_doc = False
        quote = ""
        start = 0
        parts: list[str] = []
        while i < len(lines):
            s = lines[i].strip()
            if not in_doc:
                m = re.match(r'^(?:[rubf]{0,2})("""|\'\'\')', s)
                if m:
                    quote = m.group(1)
                    rest = s[m.end():]
                    if quote in rest:
                        blocks.append(Block(i + 1, i + 1,
                                            rest.split(quote)[0].strip(), "docstring"))
                    else:
                        in_doc, start, parts = True, i, [rest]
            else:
                if quote in s:
                    parts.append(s.split(quote)[0])
                    blocks.append(Block(start + 1, i + 1,
                                        "\n".join(parts).strip(), "docstring"))
                    in_doc = False
                else:
                    parts.append(s)
            i += 1

    return blocks


def preceding_or_following_code(lines: list[str], block: Block) -> str:
    """The signature a doc block is attached to, looking below then above."""
    for j in range(block.end, min(block.end + 3, len(lines))):
        s = lines[j].strip() if j < len(lines) else ""
        if s and not s.startswith(("*", "/*", "//", '"""', "'''", "#")):
            return s
    for j in range(block.start - 2, max(block.start - 4, -1), -1):
        s = lines[j].strip() if 0 <= j < len(lines) else ""
        if s and SIGNATURE.search(s):
            return s
    return ""


def check_blocks(lines: list[str], path: Path, rel: str) -> list[Finding]:
    out: list[Finding] = []
    for b in find_blocks(lines, path):
        if not b.body:
            continue
        span = b.end - b.start + 1
        header = b.start <= 3 and re.search(
            r"copyright|license|spdx|eslint|@flow|generated", b.body, re.I)
        if header:
            continue

        prose_lines = [l.strip() for l in b.body.splitlines()
                       if l.strip() and not DOC_TAG.search(l)]
        prose = " ".join(prose_lines).strip()
        tagged = bool(DOC_TAG.search(b.body))

        # Structured API docs are judged on their prose only; everything else on
        # total span. A tagged block is doing work a reader needs.
        module_doc = b.start <= 2
        too_long = (not module_doc) and (
            len(prose_lines) >= 3 if tagged else span >= 4)
        if too_long:
            out.append(Finding(
                rel, b.start, "comment-block", "high",
                f"{span}-line comment block"
                + (f", {len(prose_lines)} lines of prose" if tagged else "") + ".",
                "Collapse to one line, or delete it. Multi-line prose belongs in a docstring on a public API, a commit message, or an ADR — not above an implementation.",
                b.body.splitlines()[0][:90] if b.body.splitlines() else ""))

        code = preceding_or_following_code(lines, b)
        if prose and code and not tagged and restates_code(prose, code):
            out.append(Finding(
                rel, b.start, "redundant-docstring", "high",
                "Doc block restates the signature.",
                "Delete it. A docstring earns its place by adding contracts, units, error behaviour, or rationale — not by rephrasing the name.",
                prose[:90]))
        elif prose and AI_VOICE.search(prose):
            out.append(Finding(
                rel, b.start, "filler-comment", "medium",
                "Doc block contains explanatory filler.",
                "Cut the preamble; keep only facts a reader cannot get from the code.",
                prose[:90]))
    return out


def is_license_header(idx: int, lines: list[str], prefixes: tuple[str, ...]) -> bool:
    """Comment blocks in the first few lines are headers, not narration."""
    if idx > 6:
        return False
    head = " ".join(lines[: idx + 4]).lower()
    return any(w in head for w in ("copyright", "license", "spdx", "@flow",
                                   "eslint", "shebang", "!/usr/bin",
                                   "-*- coding", "@ts-", "prettier",
                                   "type: ignore", "generated by"))


def strip_comment(line: str, prefixes: tuple[str, ...]) -> tuple[str, str] | None:
    """Return (indent_and_prefix, body) when the line is a whole-line comment."""
    stripped = line.strip()
    for p in prefixes:
        if stripped.startswith(p):
            return p, stripped[len(p):].strip()
    return None


def strip_strings(line: str) -> str:
    """Blank out string-literal contents so pattern definitions don't self-match."""
    return STRING_LITERAL.sub('""', line)


def suppressed(lines: list[str], idx: int, rule: str) -> bool:
    """Honour `slopcheck: ok` on the offending line or the line above it."""
    for j in (idx, idx - 1):
        if 0 <= j < len(lines):
            m = SUPPRESS.search(lines[j])
            if m and (not m.group(2).strip() or rule in m.group(2)):
                return True
    return False


def next_code_line(lines: list[str], i: int, prefixes: tuple[str, ...]) -> str:
    for j in range(i + 1, min(i + 4, len(lines))):
        s = lines[j].strip()
        if not s:
            continue
        if strip_comment(lines[j], prefixes):
            continue
        return s
    return ""


def check_file(path: Path, *, root: Path | None = None) -> FileReport:
    rel = str(path.relative_to(root)) if root and root in path.parents else str(path)
    report = FileReport(rel)
    prefixes = comment_prefixes(path)
    if not prefixes:
        return report

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return report

    lines = text.splitlines()
    is_test = any(h in str(path).lower() for h in TEST_HINTS)

    def add(f: Finding) -> None:
        if not suppressed(lines, f.line - 1, f.rule):
            report.findings.append(f)

    for f in check_blocks(lines, path, rel):
        add(f)
    block_lines = {n for b in find_blocks(lines, path)
                   for n in range(b.start, b.end + 1)}

    run_len = 0
    run_start = 0

    for i, raw in enumerate(lines):
        lineno = i + 1
        if lineno in block_lines:
            run_len = 0
            continue
        parsed = strip_comment(raw, prefixes)

        # ── whole-line comment rules ──
        if parsed:
            _, body = parsed
            header = is_license_header(i, lines, prefixes)

            if run_len == 0:
                run_start = lineno
            run_len += 1

            if not header and body:
                code = next_code_line(lines, i, prefixes)

                if is_divider(body):
                    add(Finding(rel, lineno, "section-divider", "high",
                                "Decorative divider comment.",
                                "Delete it. Structure comes from functions and files, not ASCII rules.",
                                raw.strip()[:90]))
                elif CHANGELOG.search(body):
                    add(Finding(rel, lineno, "changelog-comment", "high",
                                "Comment narrates a change instead of explaining the code.",
                                "Delete it. Git history records what changed; the comment should explain why the code is how it is.",
                                raw.strip()[:90]))
                elif CODEISH.search(body) and len(body) > 12:
                    add(Finding(rel, lineno, "commented-out-code", "high",
                                "Commented-out code.",
                                "Delete it. Version control remembers; commented code just rots.",
                                raw.strip()[:90]))
                elif NARRATION.match(body):
                    add(Finding(rel, lineno, "step-narration", "high",
                                "Comment narrates a step.",
                                "Delete it. Numbered narration belongs in a commit message, not the source.",
                                raw.strip()[:90]))
                elif code and restates_code(body, code):
                    add(Finding(rel, lineno, "redundant-comment", "high",
                                "Comment restates the code beneath it.",
                                "Delete it. Comment the why, or say nothing.",
                                raw.strip()[:90]))
                elif AI_VOICE.search(body):
                    add(Finding(rel, lineno, "filler-comment", "medium",
                                "Explanatory filler with no information.",
                                "Delete the preamble. If a fact remains, state it in under 80 characters.",
                                raw.strip()[:90]))
                elif BARE_TODO.search(body):
                    add(Finding(rel, lineno, "bare-todo", "medium",
                                "TODO with no owner or issue reference.",
                                "Add an issue link or an owner, or do the work now. Unowned TODOs are never done.",
                                raw.strip()[:90]))
                elif len(body) > 100:
                    add(Finding(rel, lineno, "comment-too-long", "medium",
                                f"Single comment is {len(body)} characters.",
                                "Cut to one line under 80 characters. If it cannot compress, the code needs simplifying.",
                                body[:90]))

                if EMOJI.search(body):
                    add(Finding(rel, lineno, "emoji-in-comment", "low",
                                "Emoji in a source comment.",
                                "Remove it.", raw.strip()[:90]))
        else:
            if run_len >= 3 and not is_license_header(run_start - 1, lines, prefixes):
                add(Finding(rel, run_start, "comment-block", "high",
                            f"{run_len} consecutive comment lines.",
                            "Collapse to at most one line. Multi-line prose belongs in a docstring, a commit message, or an ADR.",
                            lines[run_start - 1].strip()[:90]))
            run_len = 0

            code = strip_strings(raw.strip())

            if not is_test:
                if DEBUG_LOG.search(code):
                    add(Finding(rel, lineno, "debug-logging", "high",
                                "Debug logging left in source.",
                                "Delete it, or use the project's logger at a real level.",
                                code[:90]))
                elif ENTRY_EXIT_LOG.search(code):
                    add(Finding(rel, lineno, "entry-exit-logging", "medium",
                                "Function entry/exit logging.",
                                "Delete it. Tracing belongs in instrumentation, not hand-written log lines.",
                                code[:90]))

            if REDUNDANT_BOOL.search(code):
                add(Finding(rel, lineno, "redundant-boolean", "low",
                            "Explicit comparison against a boolean literal.",
                            "Use the value directly.", code[:90]))

            if TRIPLE_GUARD.search(code):
                add(Finding(rel, lineno, "defensive-guard", "medium",
                            "Chained existence checks.",
                            "Use optional chaining, or fix the type so the value cannot be absent.",
                            code[:90]))

            if CATCH_OPEN.search(code):
                body_lines = [l.strip() for l in lines[i + 1:i + 4] if l.strip()]
                meaningful = [l for l in body_lines
                              if not strip_comment(l, prefixes)
                              and not l.startswith(("}", ")", "end"))]
                if meaningful and all(ONLY_LOG_OR_PASS.match(l) for l in meaningful[:1]):
                    add(Finding(rel, lineno, "swallowed-error", "high",
                                "Error caught and only logged or ignored.",
                                "Handle it, wrap it with context, or let it propagate. Silent failure is worse than a crash.",
                                code[:90]))

    if run_len >= 3 and not is_license_header(run_start - 1, lines, prefixes):
        add(Finding(rel, run_start, "comment-block", "high",
                    f"{run_len} consecutive comment lines.",
                    "Collapse to at most one line.",
                    lines[run_start - 1].strip()[:90]))

    return report


def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    return str(path).endswith(SKIP_SUFFIX)


def expand(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            out.extend(f for f in sorted(p.rglob("*"))
                       if f.is_file() and comment_prefixes(f) and not should_skip(f))
        elif p.is_file() and not should_skip(p):
            out.append(p)
    return out


def changed_files(base: str | None) -> list[Path]:
    rev = base or "HEAD"
    cmds = [["git", "diff", "--name-only", "--diff-filter=ACMR", rev],
            ["git", "diff", "--name-only", "--diff-filter=ACMR", "--cached"]]
    names: set[str] = set()
    for cmd in cmds:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.SubprocessError):
            continue  # slopcheck: ok — git absence is expected, other commands still run
        if r.returncode == 0:
            names.update(n for n in r.stdout.split("\n") if n.strip())
    return [p for p in (Path(n) for n in sorted(names))
            if p.is_file() and comment_prefixes(p) and not should_skip(p)]


def hook_files() -> list[Path]:
    """Extract edited file paths from a Claude Code hook event on stdin."""
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return []
    ti = event.get("tool_input") or {}
    candidates = [ti.get("file_path"), ti.get("path"), ti.get("notebook_path")]
    for edit in ti.get("edits") or []:
        if isinstance(edit, dict):
            candidates.append(edit.get("file_path"))
    seen: list[Path] = []
    for c in candidates:
        if not c:
            continue
        p = Path(c)
        if p.is_file() and comment_prefixes(p) and not should_skip(p) and p not in seen:
            seen.append(p)
    return seen


def render(reports: list[FileReport], *, verbose: bool, quiet: bool) -> str:
    findings = [f for r in reports for f in r.findings]
    if not findings:
        return "" if quiet else "slopcheck: clean"

    shown = findings if verbose else [f for f in findings if f.severity != "low"]
    if not shown:
        return "" if quiet else "slopcheck: clean (low-severity only; -v to see)"

    counts: dict[str, int] = {}
    for f in shown:
        counts[f.rule] = counts.get(f.rule, 0) + 1
    summary = " · ".join(f"{k} {v}" for k, v in
                         sorted(counts.items(), key=lambda kv: -kv[1]))

    if quiet:
        return f"slopcheck: {len(shown)} finding(s) — {summary}"

    out = [f"slopcheck: {len(shown)} finding(s) — {summary}", ""]
    shown.sort(key=lambda f: (-SEVERITY_ORDER[f.severity], f.path, f.line))
    for f in shown:
        out.append(f"{f.path}:{f.line}  [{f.severity}] {f.rule}")
        out.append(f"    {f.message}")
        if f.excerpt:
            out.append(f"    > {f.excerpt}")
        out.append(f"    fix: {f.fix}")
        out.append("")
    return "\n".join(out).rstrip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="slopcheck",
        description="Flag AI-slop patterns in source files.")
    ap.add_argument("paths", nargs="*", help="files or directories")
    ap.add_argument("--diff", nargs="?", const="", metavar="BASE",
                    help="check files changed vs BASE (default HEAD)")
    ap.add_argument("--hook", action="store_true",
                    help="read a Claude Code hook event from stdin")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="include low-severity findings")
    ap.add_argument("-q", "--quiet", action="store_true", help="one-line summary")
    ap.add_argument("--fail-on", choices=["high", "medium", "low", "never"],
                    default="high", help="exit 1 at this severity or above")
    args = ap.parse_args(argv)

    if args.hook:
        files = hook_files()
    elif args.diff is not None:
        files = changed_files(args.diff or None)
    elif args.paths:
        files = expand(args.paths)
    else:
        ap.print_usage(sys.stderr)
        return 2

    root = Path.cwd()
    reports = [check_file(f, root=root) for f in files]

    if args.json:
        print(json.dumps({
            "files_checked": len(files),
            "findings": [f.as_dict() for r in reports for f in r.findings],
        }, indent=2))
    else:
        text = render(reports, verbose=args.verbose, quiet=args.quiet)
        if text:
            # Hook mode writes to stderr so the agent reads it as feedback.
            print(text, file=sys.stderr if args.hook else sys.stdout)

    if args.fail_on == "never":
        return 0
    threshold = SEVERITY_ORDER[args.fail_on]
    hit = any(SEVERITY_ORDER[f.severity] >= threshold
              for r in reports for f in r.findings)
    return 1 if hit else 0


if __name__ == "__main__":
    sys.exit(main())
