#!/usr/bin/env python3
"""Install this portable Agent Skill into supported user-level skill roots."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path


SKILL_NAME = "user-preference-analyzer"
AGENTS = {"codex", "zed", "zcode", "deepseek-harness"}


def get_roots(agent: str, home: Path) -> list[Path]:
    roots: list[Path] = []
    if agent in {"all", "codex"}:
        codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser()
        roots.append(codex_home / "skills")
    if agent in {"all", "zed", "deepseek-harness"}:
        agents_home = Path(os.environ.get("DSH_AGENTS_HOME", home / ".agents")).expanduser()
        roots.append(agents_home / "skills")
    if agent in {"all", "zcode"}:
        zcode_home = Path(os.environ.get("ZCODE_HOME", home / ".zcode")).expanduser()
        roots.append(zcode_home / "skills")
    if agent in {"all", "deepseek-harness"}:
        dsh_home = Path(os.environ.get("DSH_HOME", home / ".dsh")).expanduser()
        roots.append(dsh_home / "skills")
    unique: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved = root.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def verify_source(source: Path) -> None:
    skill_file = source / "SKILL.md"
    if not skill_file.is_file():
        raise ValueError(f"Skill source does not contain SKILL.md: {source}")
    body = skill_file.read_text(encoding="utf-8")
    sections = body.split("---", 2)
    if len(sections) < 3 or f"name: {SKILL_NAME}" not in sections[1]:
        raise ValueError(f"SKILL.md name must be {SKILL_NAME}")


def install(source: Path, destination: Path, update: bool, dry_run: bool) -> str:
    if source.resolve() == destination.resolve():
        return f"SKIP already at source: {destination}"
    if destination.exists() and not update:
        return f"EXISTS (use --update to back up and refresh): {destination}"
    if dry_run:
        verb = "UPDATE" if destination.exists() else "INSTALL"
        return f"{verb}: {source} -> {destination}"

    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=f".{SKILL_NAME}.install-", dir=destination.parent))
    staged.rmdir()
    shutil.copytree(source, staged, symlinks=True)

    backup = None
    if destination.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = destination.parent / f"{SKILL_NAME}.backup-{stamp}"
        suffix = 1
        while backup.exists():
            backup = destination.parent / f"{SKILL_NAME}.backup-{stamp}-{suffix}"
            suffix += 1
        destination.rename(backup)
    try:
        staged.rename(destination)
    except Exception:
        if backup and backup.exists() and not destination.exists():
            backup.rename(destination)
        if staged.exists():
            shutil.rmtree(staged)
        raise
    note = f"INSTALLED: {destination}"
    if backup:
        note += f" (previous version backed up at {backup})"
    return note


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=["all", *sorted(AGENTS)], default="all")
    parser.add_argument("--source", type=Path, help="Skill folder; defaults to this script's parent Skill")
    parser.add_argument("--update", action="store_true", help="Back up and replace existing installs")
    parser.add_argument("--dry-run", action="store_true", help="Preview destination paths without writing")
    args = parser.parse_args()

    source = (args.source or Path(__file__).resolve().parents[1]).expanduser().resolve()
    try:
        verify_source(source)
        destinations = [root / SKILL_NAME for root in get_roots(args.agent, Path.home())]
        results = [install(source, destination, args.update, args.dry_run) for destination in destinations]
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for result in results:
        print(result)
    if any(result.startswith("EXISTS") for result in results):
        print("Some destinations were left unchanged. Re-run with --update to back them up and refresh.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
