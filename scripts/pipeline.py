#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from backup_ops import backup_git
from classify_ops import Category, iter_inbox_files, move_with_unique, target_for_file
from config_ops import ensure_dirs, load_config
from link_ops import add_wikilinks
from summary_ops import create_summaries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generic Obsidian vault automation pipeline.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dry_run = args.dry_run
    cfg = load_config(args.config)
    vault = Path(cfg["vault_root"]).expanduser().resolve()
    ensure_dirs(vault, cfg)

    categories = [
        Category(path=item["path"], label=item.get("label", item["path"]), keywords=tuple(item.get("keywords", [])))
        for item in cfg["categories"]
    ]
    api_key = os.environ.get("OPENAI_API_KEY")

    print(f"mode={'dry-run' if dry_run else 'apply'}")
    moved = 0
    for path in iter_inbox_files(vault, cfg):
        category, reason = target_for_file(path, cfg, categories, api_key)
        dst = move_with_unique(path, vault / category, dry_run)
        moved += 1
        print(f"- move: {path.name} -> {dst.relative_to(vault)} ({reason})")

    linked = add_wikilinks(vault, cfg, dry_run)
    print(f"- wikilink updated files: {linked}")

    for line in create_summaries(vault, cfg, dry_run, api_key):
        print(f"- {line}")

    print(f"- moved files: {moved}")
    print(f"- {backup_git(vault, cfg, dry_run)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

