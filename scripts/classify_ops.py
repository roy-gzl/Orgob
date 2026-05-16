#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
ATTACHMENT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif"}


@dataclass(frozen=True)
class Category:
    path: str
    label: str
    keywords: tuple[str, ...]


def _extract_output_text(raw: dict) -> str:
    output_text = raw.get("output_text", "")
    if output_text:
        return str(output_text).strip()
    parts = []
    for item in raw.get("output", []):
        if not isinstance(item, dict):
            continue
        for block in item.get("content", []):
            if isinstance(block, dict) and block.get("type") in {"output_text", "text"}:
                parts.append(str(block.get("text", "")))
    return "\n".join(parts).strip()


def openai_classify(model: str, timeout_sec: int, prompt: str, filename: str, text: str, api_key: str) -> tuple[str, str]:
    payload = {
        "model": model,
        "input": f"{prompt}\n\nfilename: {filename}\n\ntext:\n{text[:12000]}",
        "max_output_tokens": 220,
    }
    req = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", "authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as res:
            raw = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail[:300]}") from exc

    output_text = _extract_output_text(raw)
    match = re.search(r"\{.*\}", output_text, re.DOTALL)
    if not match:
        raise RuntimeError("AI response has no JSON object")
    parsed = json.loads(match.group(0))
    return str(parsed.get("category", "")).strip(), str(parsed.get("reason", "")).strip()


def rule_classify(text: str, categories: list[Category], needs_review: str) -> tuple[str, str]:
    haystack = text.casefold()
    best_path = needs_review
    best_score = 0
    for cat in categories:
        score = sum(len(re.findall(re.escape(k.casefold()), haystack)) for k in cat.keywords)
        if score > best_score:
            best_score = score
            best_path = cat.path
    if best_score <= 0:
        return needs_review, "no keyword match"
    return best_path, f"rule score={best_score}"


def iter_inbox_files(vault: Path, cfg: dict) -> list[Path]:
    allowed = {ext.lower() for ext in cfg["allowed_extensions"]}
    base = vault / cfg["inbox_dir"]
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_file() and p.suffix.lower() in allowed])


def target_for_file(path: Path, cfg: dict, categories: list[Category], api_key: str | None) -> tuple[str, str]:
    ext = path.suffix.lower()
    if ext in ATTACHMENT_EXTENSIONS:
        return cfg["attachments_dir"], "attachment extension"

    text = path.read_text(encoding="utf-8", errors="ignore") if ext in {".md", ".txt"} else path.stem
    ai_cfg = cfg.get("ai", {})
    if ai_cfg.get("enabled") and api_key and ext in {".md", ".txt"}:
        try:
            category, reason = openai_classify(
                model=ai_cfg.get("model", "gpt-5.4-mini"),
                timeout_sec=int(ai_cfg.get("timeout_sec", 45)),
                prompt=str(ai_cfg.get("prompt", "")),
                filename=path.name,
                text=text,
                api_key=api_key,
            )
            return category or cfg["needs_review_dir"], f"ai: {reason or 'classified'}"
        except Exception as exc:
            fallback, why = rule_classify(text, categories, cfg["needs_review_dir"])
            return fallback, f"ai failed ({exc}); {why}"
    return rule_classify(text, categories, cfg["needs_review_dir"])


def move_with_unique(src: Path, dst_dir: Path, dry_run: bool) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if dst.exists():
        for i in range(1, 1000):
            cand = dst_dir / f"{src.stem}_{i:02d}{src.suffix}"
            if not cand.exists():
                dst = cand
                break
    if not dry_run:
        shutil.move(str(src), str(dst))
    return dst

