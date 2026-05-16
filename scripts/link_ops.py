#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import yaml


PROTECTED_RE = re.compile(r"(!?\[\[[^\]]+\]\]|`[^`]*`)")


def add_wikilinks(vault: Path, cfg: dict, dry_run: bool) -> int:
    dict_path = vault / cfg["dictionary_path"]
    aliases: list[tuple[str, str]] = []
    if dict_path.exists():
        data = yaml.safe_load(dict_path.read_text(encoding="utf-8")) or {}
        for key, value in data.items():
            if isinstance(value, dict):
                target = str(value.get("target") or key)
                for alias in value.get("aliases") or [key]:
                    aliases.append((str(alias), target))
            else:
                aliases.append((str(key), str(key)))

    note_stems: dict[str, str] = {}
    for p in vault.rglob("*.md"):
        rel = p.relative_to(vault)
        if "backups" in rel.parts or "logs" in rel.parts or ".obsidian" in rel.parts:
            continue
        note_stems[p.stem] = p.stem
    for stem in sorted(note_stems):
        aliases.append((stem, stem))

    changed = 0
    for p in vault.rglob("*.md"):
        rel = p.relative_to(vault)
        if any(part in {"backups", "logs", ".obsidian"} for part in rel.parts):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        parts = PROTECTED_RE.split(text)
        updated_parts = []
        updated = False
        for part in parts:
            if not part or PROTECTED_RE.fullmatch(part):
                updated_parts.append(part)
                continue
            seg = part
            for alias, target in aliases:
                if len(alias) < 3 or target == p.stem:
                    continue
                seg2 = re.sub(rf"(?<![\w])({re.escape(alias)})(?![\w])", rf"[[{target}|\1]]", seg)
                if seg2 != seg:
                    updated = True
                    seg = seg2
            updated_parts.append(seg)
        if updated:
            changed += 1
            if not dry_run:
                p.write_text("".join(updated_parts), encoding="utf-8")
    return changed

