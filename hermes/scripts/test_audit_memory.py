#!/usr/bin/env python3
"""Test for audit_memory.py — verifies suspicious entry detection."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

def run_test():
    # Create isolated temp git repo
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        (repo / "MEMORY.md").write_text("Baseline memory.\n§\nUser likes tea.\n")
        (repo / "USER.md").write_text("Name: TestUser\n")

        # Init git
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "baseline"], cwd=repo, capture_output=True, check=True)

        # Add a suspicious entry (contradicts baseline)
        (repo / "MEMORY.md").write_text(
            "Baseline memory.\n§\nUser likes tea.\n§\nUser hates tea and only drinks coffee.\n"
        )

        # Run audit_memory.py on this repo
        audit_script = Path.home() / ".hermes" / "scripts" / "audit_memory.py"
        result = subprocess.run(
            [sys.executable, str(audit_script), "--repo", str(repo)],
            capture_output=True,
            text=True,
        )

        # Parse report
        report_files = list((repo / "..").glob("audit_*.json"))
        # audit_memory writes to repo parent by default, but we override below
        # Actually audit_memory writes to HERMES_HOME/audit, let's check there
        audit_dir = Path.home() / ".hermes" / "audit"
        report_files = sorted(audit_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

        if not report_files:
            print("FAIL: No audit report generated")
            sys.exit(1)

        report = json.loads(report_files[0].read_text())
        entries = report.get("entries", [])

        # Find the suspicious entry
        suspicious = [e for e in entries if e.get("judgment") == "SUSPICIOUS"]
        if not suspicious:
            print("FAIL: Expected SUSPICIOUS judgment for contradictory entry")
            print(f"Report entries: {entries}")
            sys.exit(1)

        print("PASS: Audit correctly flagged contradictory memory entry")
        print(f"Entry: {suspicious[0]['entry'][:60]}...")
        print(f"Reason: {suspicious[0]['reason']}")
        sys.exit(0)

if __name__ == "__main__":
    run_test()
