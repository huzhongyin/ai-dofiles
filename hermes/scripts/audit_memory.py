#!/usr/bin/env python3
"""
Memory Audit Script — Zero-Intrusion Closed Loop

Scans git diff in ~/.hermes/memories (or --repo), detects suspicious
memory entries via heuristic contradiction checks, and generates a
JSON audit report.

Usage:
    python3 audit_memory.py              # audit ~/.hermes/memories
    python3 audit_memory.py --repo PATH  # audit custom repo
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
DEFAULT_REPO = HERMES_HOME / "memories"
AUDIT_DIR = HERMES_HOME / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

ENTRY_DELIMITER = "\n§\n"

# Simple contradiction patterns: (positive, negative) keyword pairs
CONTRADICTION_PAIRS = [
    ("likes", "hates"),
    ("likes", "dislikes"),
    ("prefers", "avoids"),
    ("uses", "does not use"),
    ("is ", "is not "),
    ("always", "never"),
    ("enabled", "disabled"),
    ("dark mode", "light mode"),
]


def get_git_diff(repo: Path) -> str:
    """Return diff between HEAD and working tree."""
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"git diff failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def parse_diff_entries(diff_text: str, filename: str) -> tuple[list[str], list[str]]:
    """
    Parse git diff for a file and return (removed_entries, added_entries).
    Only handles simple + / - lines in diff hunk bodies.
    """
    removed: list[str] = []
    added: list[str] = []
    in_hunk = False

    for line in diff_text.splitlines():
        if line.startswith(f"diff --git a/{filename}"):
            in_hunk = True
            continue
        if line.startswith("diff --git a/") and in_hunk:
            break
        if not in_hunk:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])

    # Reconstruct entries from added lines
    added_text = "\n".join(added)
    added_entries = [e.strip() for e in added_text.split(ENTRY_DELIMITER) if e.strip()]

    removed_text = "\n".join(removed)
    removed_entries = [e.strip() for e in removed_text.split(ENTRY_DELIMITER) if e.strip()]

    return removed_entries, added_entries


def load_existing_entries(repo: Path, filename: str) -> list[str]:
    """Load current committed version of a memory file."""
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"HEAD:{filename}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [e.strip() for e in result.stdout.split(ENTRY_DELIMITER) if e.strip()]


def check_contradictions(new_entry: str, existing_entries: list[str]) -> str:
    """Return contradiction reason or empty string if clean."""
    new_lower = new_entry.lower()

    for pos, neg in CONTRADICTION_PAIRS:
        if pos in new_lower:
            for existing in existing_entries:
                if neg in existing.lower() and _same_subject(new_entry, existing):
                    return f"Contradiction: '{pos}' vs existing '{neg}'"
        if neg in new_lower:
            for existing in existing_entries:
                if pos in existing.lower() and _same_subject(new_entry, existing):
                    return f"Contradiction: '{neg}' vs existing '{pos}'"

    # Bidirectional negation check: new has "not X" and old has "X", or vice versa
    # Find "not <word>" in either direction
    def _extract_negations(text: str) -> set[str]:
        # e.g. "not CLI aliases" -> {"cli aliases"}
        return set(m.group(1).strip().lower() for m in re.finditer(r'\bnot\s+([^,.;!§\n]{3,60})\b', text.lower()))

    new_negations = _extract_negations(new_entry)
    for existing in existing_entries:
        old_negations = _extract_negations(existing)
        # New affirms what old negates
        for neg in old_negations:
            if neg in new_lower and _same_subject(new_entry, existing):
                return f"Contradiction: affirms '{neg}' which old entry negates"
        # New negates what old affirms (if old explicitly had "not")
        for neg in new_negations:
            # Check if existing contains the affirmative form
            if neg in existing.lower() and _same_subject(new_entry, existing):
                return f"Contradiction: negates '{neg}' which old entry affirms"

    return ""


def _same_subject(a: str, b: str) -> bool:
    """Rough check: share at least one noun-like token of length > 3."""
    tokens_a = set(re.findall(r'\b[a-z]{4,}\b', a.lower()))
    tokens_b = set(re.findall(r'\b[a-z]{4,}\b', b.lower()))
    return len(tokens_a & tokens_b) >= 1


def judge_entry(entry: str, existing_entries: list[str]) -> tuple[str, str]:
    """Return (judgment, reason)."""
    # 1. Contradiction check
    reason = check_contradictions(entry, existing_entries)
    if reason:
        return "SUSPICIOUS", reason

    # 2. Overly specific version / date claims (likely to stale)
    if re.search(r'\bversion\s+[\d.]+\b', entry, re.IGNORECASE):
        return "OBSOLETE", "Contains specific version number — may become outdated"

    if re.search(r'\b\d{4}-\d{2}-\d{2}\b', entry):
        return "OBSOLETE", "Contains specific date — may become outdated"

    return "VERIFIED", "No heuristic issues detected"


def run_audit(repo: Path) -> dict:
    diff = get_git_diff(repo)
    if not diff.strip():
        return {"entries": [], "message": "No changes since last audit."}

    all_entries: list[dict] = []
    for filename in ("MEMORY.md", "USER.md"):
        removed, added = parse_diff_entries(diff, filename)
        if not added:
            continue
        existing = load_existing_entries(repo, filename)
        for entry in added:
            judgment, reason = judge_entry(entry, existing)
            all_entries.append({
                "file": filename,
                "entry": entry,
                "judgment": judgment,
                "reason": reason,
            })

    return {"entries": all_entries, "message": f"Audited {len(all_entries)} entries"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit memory file changes")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO, help="Path to git repo")
    args = parser.parse_args()

    if not (args.repo / ".git").exists():
        print(f"ERROR: {args.repo} is not a git repository.", file=sys.stderr)
        return 1

    report = run_audit(args.repo)
    report["timestamp"] = datetime.now().isoformat()
    report["repo"] = str(args.repo)

    report_path = AUDIT_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    # If file exists, append number
    counter = 1
    original = report_path
    while report_path.exists():
        report_path = original.with_name(f"{original.stem}_{counter}{original.suffix}")
        counter += 1

    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    suspicious = [e for e in report["entries"] if e["judgment"] != "VERIFIED"]
    if suspicious:
        print(f"Audit found {len(suspicious)} issue(s). Report: {report_path}")
        for s in suspicious:
            print(f"  [{s['judgment']}] {s['entry'][:60]}... — {s['reason']}")
        return 1

    # All clear — auto-commit checkpoint
    subprocess.run(["git", "-C", str(args.repo), "add", "."], capture_output=True)
    subprocess.run(
        ["git", "-C", str(args.repo), "commit", "-m", f"audit-pass-{datetime.now().isoformat()}"],
        capture_output=True,
    )
    print("Audit passed. Checkpoint committed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
