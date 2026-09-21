#!/usr/bin/env python3
"""Offline repository-organization checks for sun60iw2-upstream."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IGNORED_TRACKED_PARTS = {".tmp", "__pycache__", "stage"}
LOCAL_PATH_RE = re.compile(r"(?:/home/[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/)")
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def tracked_files() -> list[Path]:
    raw = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    )
    return [ROOT / item.decode() for item in raw.split(b"\0") if item]


def is_archived(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return "archive" in rel.parts or ".legacy" in rel.suffixes


def check_markdown_links(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    for match in LINK_RE.finditer(text):
        target = match.group(1).split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"broken link: {path.relative_to(ROOT)} -> {target}")


def main() -> int:
    errors: list[str] = []
    files = tracked_files()

    required = [
        ROOT / "AGENTS.md",
        ROOT / "README.md",
        ROOT / "docs/status.md",
        ROOT / "scripts/README.md",
        ROOT / "patches/README.md",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing required path: {path.relative_to(ROOT)}")

    for path in files:
        rel = path.relative_to(ROOT)
        if IGNORED_TRACKED_PARTS.intersection(rel.parts):
            errors.append(f"generated/local output is tracked: {rel}")

        if not path.is_file() or is_archived(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if LOCAL_PATH_RE.search(text):
            errors.append(f"host-specific absolute path in tracked source: {rel}")

    for path in ROOT.rglob("*.md"):
        if ".git" not in path.parts and not is_archived(path):
            check_markdown_links(path, errors)

    top_level_patches = sorted((ROOT / "patches").glob("*.patch"))
    for path in top_level_patches:
        errors.append(f"patch bypasses archive/wip/active boundary: {path.relative_to(ROOT)}")

    catalog = (ROOT / "scripts/README.md").read_text(encoding="utf-8")
    for path in sorted((ROOT / "scripts").iterdir()):
        if not path.is_file() or path.name == "README.md":
            continue
        if path.name not in catalog:
            errors.append(f"script is missing from scripts/README.md: {path.name}")
        first = path.read_bytes().splitlines()[:1]
        if first and first[0].startswith(b"#!") and not path.stat().st_mode & 0o111:
            errors.append(f"script has a shebang but is not executable: scripts/{path.name}")

    if errors:
        print("Repository layout: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Repository layout: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
