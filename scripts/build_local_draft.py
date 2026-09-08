#!/usr/bin/env python3
"""Build local-only reviewed drafts from an already verified candidate ledger."""
from __future__ import annotations
from lianxh_exclusions import screen_post, normalized_url

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from site_config import date_compact

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, value: object):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_ledger(items: list[dict]):
    required = {"id", "kind", "title", "official_url", "source_url", "source_name",
                "verification_date", "core_or_extended", "why_selected", "dedup_key", "status"}
    for item in items:
        missing = sorted(required - item.keys())
        if missing:
            raise ValueError(f"{item.get('id', '<unknown>')} 缺少字段：{', '.join(missing)}")


def assemble_daily_issue(day: str, items: list[dict]) -> dict:
    # 新台账使用 payload 保存完整条目，支持论文、软件与可选会议混排。
    from editorial_rules import check_editorial
    mapping = {"paper": "papers", "tool": "tools", "post": "lianxh_posts",
               "resource": "research_resources", "conference": "conference_calls"}
    issue = {"issue_id": f"{day}-local-draft", "date": day, "status": "draft",
             "issue_type": "daily", "editorial_version": 2, "website_version": 3,
             "title": f"连享会 · 快讯 | {day.replace('-', '.')}"}
    issue.update({category: [] for category in mapping.values()})
    for candidate in items:
        if candidate["kind"] not in mapping or not isinstance(candidate.get("payload"), dict):
            raise ValueError("新版候选台账需要受支持的 kind 和完整 payload；请勿沿用旧工具专用台账。")
        if candidate["kind"] == "post" and screen_post(candidate["payload"])["action"] != "retain":
            continue
        payload = dict(candidate["payload"])
        payload["priority"] = candidate["core_or_extended"]
        issue[mapping[candidate["kind"]]].append(payload)
    return issue


def daily_issue(day: str, items: list[dict], *, as_of=None, history=()) -> dict:
    from editorial_rules import check_editorial
    issue = assemble_daily_issue(day, items)
    errors = check_editorial(issue)
    if as_of is not None:
        from trial_selection import selection_errors
        errors += selection_errors(issue, history, as_of)
    if errors:
        raise ValueError("\n".join(errors))
    return issue


def main() -> int:
    parser = argparse.ArgumentParser(description="从本地候选台账生成草稿；不写公开目录。")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--mode", choices=("daily", "conference"), required=True)
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args()
    raise RuntimeError("A-02 frozen：旧生产入口已停用；请使用 isolated_trial.py 的显式外部快照入口。")



if __name__ == "__main__":
    raise SystemExit(main())
