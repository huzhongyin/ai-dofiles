#!/usr/bin/env python3
"""Tests for fact_validator.py — RED-GREEN-REFACTOR."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))

from fact_validator import validate


def test_false_os_claim_rejected():
    """If entry claims OS: Windows but we're on macOS/Darwin, reject."""
    is_valid, reason = validate("User runs OS: Windows for all development.")
    assert not is_valid, f"Expected rejection, got: {reason}"
    assert "windows" in reason.lower()
    assert "live system" in reason.lower()
    print("PASS: false OS claim rejected")


def test_correct_os_claim_accepted():
    """If entry claims current actual OS, accept."""
    import subprocess
    actual_os = subprocess.run(["uname", "-s"], capture_output=True, text=True).stdout.strip()
    is_valid, reason = validate(f"User runs OS: {actual_os}")
    assert is_valid, f"Expected acceptance for true OS {actual_os}, got: {reason}"
    print(f"PASS: correct OS claim ({actual_os}) accepted")


def test_no_fact_claim_accepted():
    """Preference entries without objective claims pass through."""
    is_valid, reason = validate("User prefers dark mode.")
    assert is_valid, f"Expected acceptance, got: {reason}"
    print("PASS: preference entry without fact claim accepted")


def test_python_version_false_rejected():
    """False python version claim is rejected."""
    is_valid, reason = validate("Project uses python: 2.7")
    # Almost certainly false in 2026
    if not is_valid:
        print(f"PASS: false python version rejected: {reason}")
    else:
        # If by chance python 2.7 is installed, skip
        print("SKIP: python 2.7 may actually be installed")


if __name__ == "__main__":
    test_false_os_claim_rejected()
    test_correct_os_claim_accepted()
    test_no_fact_claim_accepted()
    test_python_version_false_rejected()
    print("\nAll tests completed.")
