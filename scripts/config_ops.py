#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not data.get("vault_root"):
        raise SystemExit("config.vault_root is required")
    return data


def ensure_dirs(vault: Path, cfg: dict) -> None:
    required = [
        cfg["inbox_dir"],
        cfg["attachments_dir"],
        cfg["needs_review_dir"],
        cfg["daily_dir"],
        cfg["weekly_dir"],
        cfg["monthly_dir"],
    ] + [item["path"] for item in cfg["categories"]]
    for rel in required:
        (vault / rel).mkdir(parents=True, exist_ok=True)

