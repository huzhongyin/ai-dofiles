#!/usr/bin/env python3
"""
Fact Validator — Real-time environment fact checking for memory entries.

Detects objective environment claims in memory content and cross-checks
them against the live system. Returns (is_valid, reason).

Extensible: add new FACT_PATTERNS to cover more claim types.
"""

import re
import subprocess
from typing import Callable, Tuple

FactCheck = Tuple[str, str, Callable[[], str]]
# (pattern_regex, claim_description, checker_command)


def _run_cmd(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return (result.stdout or "").strip()
    except Exception as e:
        return f"<error: {e}>"


# Pattern: regex to detect claim, description, command to get ground truth
FACT_PATTERNS: list[FactCheck] = [
    (
        r'\bOS\s*[:=]\s*(\w+)',
        "OS claim",
        lambda: _run_cmd(["uname", "-s"]),
    ),
    (
        r'\bpython\s*[:=]\s*([\d.]+)',
        "Python version claim",
        lambda: _run_cmd(["python3", "--version"]),
    ),
    (
        r'\bnode\s*[:=]\s*([\d.]+)',
        "Node.js version claim",
        lambda: _run_cmd(["node", "--version"]),
    ),
    (
        r'\bshell\s*[:=]\s*(\w+)',
        "Shell claim",
        lambda: _run_cmd(["echo", "$SHELL"]) or _run_cmd(["basename", _run_cmd(["echo", "$SHELL"])]),
    ),
]


def validate(content: str) -> Tuple[bool, str]:
    """
    Cross-check memory content against live system facts.

    Returns (is_valid, reason).
    - is_valid=True: no contradictions found (or claim untestable)
    - is_valid=False: claim contradicts live system state
    """
    content_lower = content.lower()

    for pattern, desc, checker in FACT_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            continue

        claimed = match.group(1).strip().lower()
        actual = checker().lower()

        # Soft matching: claimed value must appear in actual output
        if claimed not in actual and actual not in claimed:
            # Special case: python3 --version outputs "Python 3.x.x", user may write "3.x"
            if desc == "Python version claim" and claimed in actual:
                continue
            return False, (
                f"{desc} validation failed: entry claims '{claimed}', "
                f"but live system reports '{actual}'. "
                f"Refuse to persist factually incorrect memory."
            )

    return True, ""
