#!/usr/bin/env python3
"""Safely append a learning note to ~/.hermes/learning-notes/YYYY-MM-DD.md.

Usage:
    python3 append_learning_note.py YYYY-MM-DD <<'EOF'
    ## Topic Title

    ### Question
    ...
    EOF

If the file does not exist, creates it with the daily header.
If the file exists, appends content without touching existing notes.
"""

import os
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 append_learning_note.py YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    date = sys.argv[1]
    notes_dir = os.environ.get("LEARNING_NOTES_DIR", os.path.expanduser("~/.hermes/learning-notes"))
    os.makedirs(notes_dir, exist_ok=True)

    filepath = os.path.join(notes_dir, f"{date}.md")
    content = sys.stdin.read()

    # Normalize content: ensure it ends with a newline
    if not content.endswith("\n"):
        content += "\n"

    if os.path.exists(filepath):
        # Append mode — existing content is never read or modified
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content)
        print(f"Appended to {filepath}")
    else:
        # Create new file with daily header
        header = f"# {date} 学习笔记\n\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(header + content)
        print(f"Created {filepath}")


if __name__ == "__main__":
    main()
