#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


def _openai_text(model: str, timeout_sec: int, prompt: str, payload_text: str, api_key: str) -> str:
    payload = {
        "model": model,
        "input": f"{prompt}\n\n{payload_text[:24000]}",
        "max_output_tokens": 2200,
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

    output_text = raw.get("output_text", "")
    if output_text:
        return str(output_text).strip() + "\n"
    parts = []
    for item in raw.get("output", []):
        if not isinstance(item, dict):
            continue
        for block in item.get("content", []):
            if isinstance(block, dict) and block.get("type") in {"output_text", "text"}:
                parts.append(str(block.get("text", "")))
    text = "\n".join(parts).strip()
    if not text:
        raise RuntimeError("OpenAI text response is empty")
    return text + "\n"


def create_summaries(vault: Path, cfg: dict, dry_run: bool, api_key: str | None) -> list[str]:
    ai_cfg = cfg.get("ai", {})
    summary_cfg = cfg.get("summary", {})
    if not (ai_cfg.get("enabled") and api_key):
        return ["summary skipped: ai not configured"]

    today = datetime.now().date()
    out: list[str] = []
    weekday = int(summary_cfg.get("weekly_weekday", 1))
    month_day = int(summary_cfg.get("monthly_day", 1))

    if today.weekday() == weekday:
        start = today - timedelta(days=7)
        docs = []
        cur = start
        while cur < today:
            f = vault / cfg["daily_dir"] / f"{cur.isoformat()}.md"
            if f.exists():
                docs.append((cur.isoformat(), f.read_text(encoding="utf-8", errors="ignore")))
            cur += timedelta(days=1)
        if docs:
            source = "\n\n".join([f"## {d}\n{t[:12000]}" for d, t in docs])
            md = _openai_text(
                ai_cfg.get("model", "gpt-5.4-mini"),
                int(ai_cfg.get("timeout_sec", 45)),
                str(summary_cfg.get("weekly_prompt", "")),
                source,
                api_key,
            )
            path = vault / cfg["weekly_dir"] / f"{today.isoformat()}_weekly.md"
            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(md, encoding="utf-8")
            out.append(f"weekly: {path.relative_to(vault)}")

    if today.day == month_day:
        month_key = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        weekly_base = vault / cfg["weekly_dir"]
        docs = []
        for p in sorted(weekly_base.glob("*.md")):
            if month_key in p.name:
                docs.append((p.name, p.read_text(encoding="utf-8", errors="ignore")))
        if docs:
            source = "\n\n".join([f"## {n}\n{t[:12000]}" for n, t in docs])
            md = _openai_text(
                ai_cfg.get("model", "gpt-5.4-mini"),
                int(ai_cfg.get("timeout_sec", 45)),
                str(summary_cfg.get("monthly_prompt", "")),
                source,
                api_key,
            )
            path = vault / cfg["monthly_dir"] / f"{month_key}_monthly.md"
            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(md, encoding="utf-8")
            out.append(f"monthly: {path.relative_to(vault)}")

    return out or ["summary skipped: not due today"]

