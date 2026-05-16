#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


def backup_git(vault: Path, cfg: dict, dry_run: bool) -> str:
    g = cfg.get("git_backup", {})
    if not g.get("enabled"):
        return "git backup disabled"
    if dry_run:
        return "git backup dry-run"

    subprocess.run(["git", "init"], cwd=vault, check=False, capture_output=True, text=True)
    subprocess.run(["git", "add", "-A"], cwd=vault, check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=vault, check=False)
    if diff.returncode == 0:
        return "git backup: no changes"

    msg = f"vault backup {datetime.now().isoformat(timespec='seconds')}"
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Vault Backup Bot",
            "-c",
            "user.email=vault-backup@local",
            "commit",
            "-m",
            msg,
        ],
        cwd=vault,
        check=True,
    )
    if g.get("push"):
        remote = str(g.get("remote", "origin"))
        subprocess.run(["git", "push", "-u", remote, "HEAD"], cwd=vault, check=True)
        return "git backup: committed and pushed"
    return "git backup: committed"

