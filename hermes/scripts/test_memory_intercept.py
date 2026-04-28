#!/usr/bin/env python3
"""Integration test: MemoryStore.add() rejects factually incorrect entries."""

import sys
import tempfile
from pathlib import Path

# Ensure imports resolve
sys.path.insert(0, str(Path.home() / ".hermes" / "hermes-agent"))
sys.path.insert(0, str(Path.home() / ".hermes" / "hermes-agent" / "tools"))
sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))

from memory_tool import MemoryStore


def test_rejects_false_os():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override memory dir via monkeypatch on get_memory_dir
        import memory_tool
        original_get_memory_dir = memory_tool.get_memory_dir
        memory_tool.get_memory_dir = lambda: Path(tmpdir)

        try:
            store = MemoryStore(memory_char_limit=5000, user_char_limit=5000)
            store.load_from_disk()  # creates empty files

            # Attempt to write false OS claim
            result = store.add("memory", "User runs OS: Windows for all development.")

            assert not result["success"], f"Expected rejection, got: {result}"
            assert "validation failed" in result["error"].lower() or "refuse" in result["error"].lower(), (
                f"Expected validation error, got: {result['error']}"
            )

            # Verify disk was NOT modified
            store.load_from_disk()
            assert "Windows" not in " ".join(store.memory_entries), "False entry leaked to disk!"

            print("PASS: MemoryStore.add() rejected false OS claim")
        finally:
            memory_tool.get_memory_dir = original_get_memory_dir


def test_accepts_true_os():
    import subprocess
    actual_os = subprocess.run(["uname", "-s"], capture_output=True, text=True).stdout.strip()

    with tempfile.TemporaryDirectory() as tmpdir:
        import memory_tool
        original_get_memory_dir = memory_tool.get_memory_dir
        memory_tool.get_memory_dir = lambda: Path(tmpdir)

        try:
            store = MemoryStore(memory_char_limit=5000, user_char_limit=5000)
            store.load_from_disk()

            result = store.add("memory", f"User runs OS: {actual_os}")
            assert result["success"], f"Expected acceptance for true OS, got: {result}"
            print(f"PASS: MemoryStore.add() accepted true OS claim ({actual_os})")
        finally:
            memory_tool.get_memory_dir = original_get_memory_dir


def test_accepts_preference():
    with tempfile.TemporaryDirectory() as tmpdir:
        import memory_tool
        original_get_memory_dir = memory_tool.get_memory_dir
        memory_tool.get_memory_dir = lambda: Path(tmpdir)

        try:
            store = MemoryStore(memory_char_limit=5000, user_char_limit=5000)
            store.load_from_disk()

            result = store.add("memory", "User prefers dark mode.")
            assert result["success"], f"Expected acceptance, got: {result}"
            print("PASS: MemoryStore.add() accepted preference entry")
        finally:
            memory_tool.get_memory_dir = original_get_memory_dir


if __name__ == "__main__":
    test_rejects_false_os()
    test_accepts_true_os()
    test_accepts_preference()
    print("\nAll integration tests passed.")
