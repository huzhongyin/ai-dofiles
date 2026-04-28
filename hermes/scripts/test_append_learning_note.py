#!/usr/bin/env python3
"""Tests for append_learning_note.py — verifies append-only, no overwrite."""

import os
import subprocess
import tempfile
import shutil

SCRIPT = os.path.expanduser("~/.hermes/scripts/append_learning_note.py")
NOTES_DIR = os.path.expanduser("~/.hermes/learning-notes")

def run_script(date: str, content: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    # Override notes dir to a temp location for testing
    env["LEARNING_NOTES_DIR"] = NOTES_DIR
    result = subprocess.run(
        ["python3", SCRIPT, date],
        input=content,
        capture_output=True,
        text=True,
        env=env,
    )
    return result

def test_create_new_file():
    """When file does not exist, create with header + content."""
    # Use a fake date so we don't touch real data
    test_date = "2099-01-01"
    test_path = os.path.join(NOTES_DIR, f"{test_date}.md")
    try:
        if os.path.exists(test_path):
            os.remove(test_path)

        result = run_script(test_date, "## Test Topic\n\nContent\n")
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        with open(test_path, "r") as f:
            data = f.read()
        assert f"# {test_date} 学习笔记" in data
        assert "## Test Topic" in data
        assert "Content" in data
        print("PASS: test_create_new_file")
    finally:
        if os.path.exists(test_path):
            os.remove(test_path)

def test_append_existing_file():
    """When file exists, append without destroying old content."""
    test_date = "2099-01-02"
    test_path = os.path.join(NOTES_DIR, f"{test_date}.md")
    try:
        if os.path.exists(test_path):
            os.remove(test_path)

        # First write
        r1 = run_script(test_date, "## First Note\n\nFirst body\n")
        assert r1.returncode == 0

        # Second write (append)
        r2 = run_script(test_date, "## Second Note\n\nSecond body\n")
        assert r2.returncode == 0

        with open(test_path, "r") as f:
            data = f.read()

        assert "## First Note" in data, "Old content was DESTROYED"
        assert "First body" in data
        assert "## Second Note" in data, "New content missing"
        assert "Second body" in data
        print("PASS: test_append_existing_file")
    finally:
        if os.path.exists(test_path):
            os.remove(test_path)

def test_multiple_appends():
    """Multiple appends all preserved."""
    test_date = "2099-01-03"
    test_path = os.path.join(NOTES_DIR, f"{test_date}.md")
    try:
        if os.path.exists(test_path):
            os.remove(test_path)

        for i in range(3):
            result = run_script(test_date, f"## Note {i}\n\nBody {i}\n")
            assert result.returncode == 0

        with open(test_path, "r") as f:
            data = f.read()

        for i in range(3):
            assert f"## Note {i}" in data, f"Note {i} missing after multiple appends!"
        print("PASS: test_multiple_appends")
    finally:
        if os.path.exists(test_path):
            os.remove(test_path)

if __name__ == "__main__":
    os.makedirs(NOTES_DIR, exist_ok=True)
    test_create_new_file()
    test_append_existing_file()
    test_multiple_appends()
    print("\nAll tests passed.")
