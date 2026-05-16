#!/usr/bin/env python3
from __future__ import annotations

# Backward-compatible shim.
from backup_ops import backup_git
from classify_ops import Category, iter_inbox_files, move_with_unique, openai_classify, rule_classify, target_for_file
from config_ops import ensure_dirs, load_config
from link_ops import add_wikilinks
from summary_ops import create_summaries

__all__ = [
    "Category",
    "add_wikilinks",
    "backup_git",
    "create_summaries",
    "ensure_dirs",
    "iter_inbox_files",
    "load_config",
    "move_with_unique",
    "openai_classify",
    "rule_classify",
    "target_for_file",
]

