#!/usr/bin/env python3
"""
Skill Manager: Unified skill installation and synchronization
for Hermes, Claude Code, Kiro, Kimi, Cursor, and other AI agents.

All skills are stored canonically in ~/.agents/skills/
Agent directories contain only symlinks to this unified location.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# Canonical unified directory
UNIFIED_DIR = Path.home() / ".agents" / "skills"

# Agent skill directories to sync
AGENT_DIRS = {
    "claude": Path.home() / ".claude" / "skills",
    "kiro": Path.home() / ".kiro" / "skills",
    "cursor": Path.home() / ".cursor" / "skills",
    "codex": Path.home() / ".codex" / "skills",
    "trae": Path.home() / ".trae" / "skills",
    "trae-cn": Path.home() / ".trae-cn" / "skills",
    "windsurf": Path.home() / ".windsurf" / "skills",
    "github-copilot": Path.home() / ".github" / "skills",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def resolve_link(link: Path) -> Path:
    """Resolve a symlink, following relative paths."""
    if link.is_symlink():
        target = link.readlink()
        if target.is_absolute():
            return target
        return (link.parent / target).resolve()
    return link


def install_from_git(url: str, name: Optional[str] = None) -> int:
    """Clone a skill from git into the unified directory."""
    ensure_dir(UNIFIED_DIR)

    if not name:
        name = url.rstrip("/").split("/")[-1].replace(".git", "")

    target = UNIFIED_DIR / name
    if target.exists():
        print(f"Skill '{name}' already exists at {target}")
        print("Run 'ai-skill sync' if you need to relink it.")
        return 1

    # Handle GitHub tree URLs pointing to subdirectories
    if "/tree/" in url:
        base_url, tree_part = url.split("/tree/", 1)
        parts = tree_part.split("/", 1)
        branch = parts[0]
        subpath = parts[1] if len(parts) > 1 else ""

        with tempfile.TemporaryDirectory() as tmp:
            clone_dir = Path(tmp) / "repo"
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", branch, base_url, str(clone_dir)],
                check=True,
                capture_output=True,
            )

            source = clone_dir / subpath if subpath else clone_dir
            if not source.exists():
                print(f"Subpath not found: {subpath}")
                return 1

            # If the source itself is a skill directory (contains SKILL.md)
            if (source / "SKILL.md").exists():
                shutil.move(str(source), str(target))
            else:
                # Look for immediate subdirectories containing SKILL.md
                candidates = [
                    d for d in source.iterdir()
                    if d.is_dir() and (d / "SKILL.md").exists()
                ]
                if len(candidates) == 1:
                    shutil.move(str(candidates[0]), str(target))
                elif len(candidates) > 1:
                    print(f"Multiple skills found: {[c.name for c in candidates]}")
                    print("Please install with: ai-skill install <url> --name <skill-name>")
                    return 1
                else:
                    print("No SKILL.md found in the specified path.")
                    return 1
    else:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(target)],
            check=True,
        )

    print(f"Installed '{name}' -> {target}")
    sync_agents()
    return 0


def install_from_script(url: str, name: Optional[str] = None, yes: bool = False) -> int:
    """
    Download and execute a remote install script in a sandboxed temp directory,
    then move the generated skill into the unified directory.
    """
    ensure_dir(UNIFIED_DIR)

    # Derive skill name from URL if not provided
    if not name:
        parsed = urlparse(url)
        basename = Path(parsed.path).name  # e.g. "install.sh"
        # Try to infer skill name from parent path or default to basename without extension
        name = Path(parsed.path).parent.name
        if name in ("", "/", "."):
            name = basename.rsplit(".", 1)[0] if "." in basename else basename

    target = UNIFIED_DIR / name
    if target.exists():
        print(f"Skill '{name}' already exists at {target}")
        print("Run 'ai-skill sync' if you need to relink it.")
        return 1

    if not yes:
        print(f"\n⚠️  Security Warning: about to download and execute a remote script.")
        print(f"   URL: {url}")
        print(f"   This will run in a temporary directory, but the script could perform any action.")
        try:
            resp = input("Proceed? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            resp = "n"
        if resp not in ("y", "yes"):
            print("Aborted.")
            return 1

    with tempfile.TemporaryDirectory() as tmp:
        script_path = Path(tmp) / "install.sh"
        print(f"Downloading script...")
        result = subprocess.run(
            ["curl", "-fsSL", "-o", str(script_path), url],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Failed to download script: {result.stderr}")
            return 1

        # Make executable
        script_path.chmod(0o755)

        # Execute in temp directory so the script drops files there
        print(f"Executing install script in sandbox...")
        exec_result = subprocess.run(
            ["bash", str(script_path)],
            cwd=tmp,
            capture_output=False,
        )
        if exec_result.returncode != 0:
            print("Install script failed.")
            return 1

        # Find the generated skill directory (must contain SKILL.md somewhere)
        tmp_path = Path(tmp)
        candidates = []
        for entry in tmp_path.rglob("SKILL.md"):
            skill_root = entry.parent
            # Avoid picking up nested SKILL.md inside another skill; prefer top-level dirs
            rel_depth = len(skill_root.relative_to(tmp_path).parts)
            candidates.append((rel_depth, skill_root))

        if not candidates:
            print("No SKILL.md found after running install script.")
            print("The script may have installed the skill outside the temp directory,")
            print("or it may use a non-standard layout.")
            return 1

        # Pick the shallowest candidate; if tie, pick alphabetically first parent
        candidates.sort(key=lambda x: (x[0], str(x[1])))
        source = candidates[0][1]

        # Move to unified dir
        shutil.move(str(source), str(target))

    print(f"Installed '{name}' -> {target}")
    sync_agents()
    return 0


def guess_url_type(url: str) -> str:
    """Guess whether the URL points to a git repo or an install script."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    if path.endswith(".sh"):
        return "script"
    if path.endswith(".git") or "/github.com/" in parsed.netloc.lower() or "/gitlab.com/" in parsed.netloc.lower():
        return "git"
    # Default fallback: if it looks like a git host, assume git
    if parsed.netloc.lower() in ("github.com", "gitlab.com", "bitbucket.org", "gitee.com"):
        return "git"
    return "git"


def install_npx(pkg: str) -> int:
    """Install via npx skills, then sync everything into unified dir."""
    print(f"Running: npx skills add {pkg} -g -y")
    result = subprocess.run(
        ["npx", "skills", "add", pkg, "-g", "-y"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("npx skills install may have failed or partially succeeded.")
    print("Running sync to unify into ~/.agents/skills/ ...")
    sync_agents()
    return 0


def sync_agents() -> None:
    """
    Scan all agent skill directories. Move any real files/dirs into unified dir,
    remove stale symlinks, and recreate fresh symlinks pointing to unified dir.
    Also cleans up cyclic symlinks that may exist inside the unified dir itself.
    """
    ensure_dir(UNIFIED_DIR)

    # --- Phase 0: Clean up cyclic/internal symlinks inside unified dir ---
    for skill in UNIFIED_DIR.iterdir():
        if not skill.is_dir() or skill.name.startswith("."):
            continue
        inner_link = skill / skill.name
        if inner_link.is_symlink():
            target = resolve_link(inner_link)
            # If the inner link points back to an agent dir or to itself, it's cyclic
            if str(UNIFIED_DIR) in str(target) or any(str(agent_dir) in str(target) for agent_dir in AGENT_DIRS.values()):
                inner_link.unlink()
                print(f"[unified] Removed cyclic symlink: {skill.name}/{skill.name}")

    # --- Phase 1: Collect real skills from agent dirs into unified dir ---
    for agent_name, agent_dir in AGENT_DIRS.items():
        if not agent_dir.exists():
            continue

        for entry in agent_dir.iterdir():
            if entry.name.startswith("."):
                continue

            if entry.is_symlink():
                resolved = resolve_link(entry)
                # If it already points into unified dir, keep it
                if str(UNIFIED_DIR) in str(resolved):
                    continue
                # Otherwise it's a stale/external symlink -> remove
                entry.unlink()
                print(f"[{agent_name}] Removed stale symlink: {entry.name}")

            elif entry.is_dir() or entry.is_file():
                dest = UNIFIED_DIR / entry.name
                if dest.exists():
                    # Already exists in unified dir; remove duplicate from agent
                    if entry.is_dir():
                        shutil.rmtree(entry)
                    else:
                        entry.unlink()
                    print(f"[{agent_name}] Removed duplicate: {entry.name}")
                else:
                    shutil.move(str(entry), str(dest))
                    print(f"[{agent_name}] Moved to unified: {entry.name}")

    # --- Phase 2: Ensure every unified skill is linked in every agent dir ---
    unified_skills = [s for s in UNIFIED_DIR.iterdir() if not s.name.startswith(".")]

    for agent_name, agent_dir in AGENT_DIRS.items():
        ensure_dir(agent_dir)

        for skill in unified_skills:
            link_path = agent_dir / skill.name

            if link_path.is_symlink():
                resolved = resolve_link(link_path)
                if str(skill) == str(resolved):
                    continue
                link_path.unlink()
            elif link_path.exists():
                # Should not happen after Phase 1, but be safe
                if link_path.is_dir():
                    shutil.rmtree(link_path)
                else:
                    link_path.unlink()

            link_path.symlink_to(skill)
            print(f"[{agent_name}] Linked {skill.name}")

    print("\nSync complete. All agents now point to ~/.agents/skills/")


def list_skills() -> None:
    """List all skills in the unified directory."""
    ensure_dir(UNIFIED_DIR)
    skills = sorted([s.name for s in UNIFIED_DIR.iterdir() if s.is_dir() and not s.name.startswith(".")])
    print(f"Unified skills ({len(skills)} total):")
    for s in skills:
        print(f"  - {s}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified AI Skill Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-skill install https://github.com/vercel-labs/skills/tree/main/skills/find-skills
  ai-skill install https://example.com/api/skills/my-skill/install.sh
  ai-skill install https://example.com/api/skills/my-skill/install.sh --name my-skill
  ai-skill install https://example.com/api/skills/my-skill/install.sh -y
  ai-skill npx vercel-labs/agent-skills
  ai-skill sync
  ai-skill list
        """,
    )
    subparsers = parser.add_subparsers(dest="command")

    # install
    install_parser = subparsers.add_parser("install", help="Install skill from git URL or install script")
    install_parser.add_argument("url", help="Git clone URL, GitHub tree URL, or install script URL (.sh)")
    install_parser.add_argument("--name", help="Override skill directory name")
    install_parser.add_argument("--yes", "-y", action="store_true", help="Skip security confirmation for script installs")

    # npx
    npx_parser = subparsers.add_parser("npx", help="Install via npx skills CLI")
    npx_parser.add_argument("pkg", help="Package identifier (e.g. owner/repo or owner/repo@skill)")

    # sync
    subparsers.add_parser("sync", help="Unify all agent skill dirs into ~/.agents/skills/")

    # list
    subparsers.add_parser("list", help="List installed unified skills")

    args = parser.parse_args()

    if args.command == "install":
        url_type = guess_url_type(args.url)
        if url_type == "script":
            return install_from_script(args.url, args.name, yes=args.yes)
        return install_from_git(args.url, args.name)
    elif args.command == "npx":
        return install_npx(args.pkg)
    elif args.command == "sync":
        sync_agents()
        return 0
    elif args.command == "list":
        list_skills()
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
