#!/usr/bin/env python3
"""Render plain-text WeChat messages from one public issue JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from site_config import detail_url

VARIANTS = ("general", "stata-causal", "r-python-ml", "finance")
SECTION_LABELS = {
    "lianxh_posts": "🌸 新推文",
    "papers": "📘 近期论文",
    "tools": "🍀 方法与工具",
    "conference_calls": "🍅 会议与征稿",
}


def add_url(lines: list[str], url: str) -> None:
    lines.extend(["", url, ""])


def title_line(issue: dict) -> str:
    date_text = issue["date"].replace("-", ".")
    prefix = "会议信息" if issue["issue_type"] == "conference-bulletin" else "连享会快讯"
    demo = " · DEMO" if issue["status"] == "demo" else ""
    return f"{prefix} | {date_text}{demo}"


def add_daily_item(lines: list[str], item: dict, category: str) -> None:
    if category == "papers":
        lines.append(f"{item['citation']}；{item['wechat_summary']}")
        add_url(lines, item["doi_url"])
        if item.get("replication_url"):
            lines.append("复现资料（演示）")
            add_url(lines, item["replication_url"])
    elif category == "tools":
        lines.append(f"{item['ecosystem']}：{item['name']}；{item['wechat_summary']}")
        add_url(lines, item["url"])
    else:
        lines.append(f"{item['title']}；{item['wechat_summary']}")
        add_url(lines, item["url"])


def render_daily(issue: dict) -> str:
    lines = [title_line(issue), ""]
    for category in ("lianxh_posts", "papers", "tools"):
        items = [item for item in issue.get(category, []) if item.get("priority") == "core"]
        if not items:
            continue
        lines.append(SECTION_LABELS[category])
        for item in items:
            add_daily_item(lines, item, category)
    lines.append("本期详版")
    add_url(lines, detail_url(issue))
    return "\n".join(lines) + "\n"


def render_conference(issue: dict) -> str:
    lines = [title_line(issue), "", SECTION_LABELS["conference_calls"]]
    for item in issue.get("conference_calls", []):
        lines.append(item["title"])
        lines.append(f"主题或范围：{item['topic']}；截止日期：{item['deadline']}")
        add_url(lines, item["official_url"])
    lines.append("本期详版")
    add_url(lines, detail_url(issue))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成微信群纯文本短版。")
    parser.add_argument("--input", required=True, type=Path, help="期次 JSON 文件")
    parser.add_argument("--output-dir", required=True, type=Path, help="输出目录")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as handle:
        issue = json.load(handle)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if issue["issue_type"] == "conference-bulletin":
        output = args.output_dir / f"{issue['date']}-{issue['status']}-conference.txt"
        output.write_text(render_conference(issue), encoding="utf-8")
        print(f"WROTE {output}")
    else:
        rendered = render_daily(issue)
        for variant in VARIANTS:
            output = args.output_dir / f"{issue['date']}-{issue['status']}-{variant}.txt"
            output.write_text(rendered, encoding="utf-8")
            print(f"WROTE {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
