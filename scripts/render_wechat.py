#!/usr/bin/env python3
"""Render one unified plain-text WeChat brief from one public issue JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from site_config import detail_url, is_demo_issue
from editorial_rules import uses_v2, core_items, check_editorial

SECTION_LABELS = {
    "lianxh_posts": "📌 推文",
    "papers": "📘 论文",
    "tools": "🍀 新方法",
    "research_resources": "🍀 新方法",
    "conference_calls": "🍅 会议征稿",
}
CORE_CATEGORY_ORDER = (
    "lianxh_posts",
    "papers",
    "tools",
    "research_resources",
    "conference_calls",
)


def add_url(lines: list[str], url: str) -> None:
    """Add a URL on its own line with the required surrounding spacing."""
    lines.extend(["", f" {url} ", ""])


def title_line(issue: dict) -> str:
    date_text = issue["date"].replace("-", ".")
    demo = " · DEMO" if is_demo_issue(issue) else ""
    if uses_v2(issue):
        return f"📰 连享会 · 快讯 | {date_text}"
    return f"连享会快讯 · {date_text}{demo}"


def add_daily_item(lines: list[str], item: dict, category: str) -> None:
    if category == "papers":
        lines.append(f"{item['citation']}；{item['wechat_summary']}")
        add_url(lines, item["doi_url"])
        if item.get("replication_url"):
            lines.append("复现资料")
            add_url(lines, item["replication_url"])
    elif category == "tools":
        lines.append(f"{item['ecosystem']}：{item['name']}；{item['wechat_summary']}")
        add_url(lines, item["url"])
    else:
        lines.append(f"{item['title']}；{item['wechat_summary']}")
        add_url(lines, item["url"])


def render_daily_v2(issue: dict) -> str:
    errors = check_editorial(issue)
    if errors:
        raise ValueError("\n".join(errors))
    lines = [title_line(issue), ""]
    labels = {"papers": "论文", "tools": "软件", "lianxh_posts": "推文",
              "research_resources": "资源", "conference_calls": "会议征稿"}
    for number, (category, item) in enumerate(core_items(issue), 1):
        lines.append(f"{number:02d}｜{labels[category]} · {item['title']}")
        lines.append(f"提要：{item['wechat_summary']}")
        if category == "papers":
            # 提要、完整引文分别独占一行；PDF 版本不可省略。
            lines.append(f"引文：{item['citation']}")
            lines.append("论文主页")
            add_url(lines, item["homepage_url"])
            lines.append(f"PDF ({item['pdf_version']})")
            add_url(lines, item["pdf_url"])
        elif category == "tools":
            lines.append(f"版本：{item['ecosystem']} / {item['name']} {item['version']}；发布：{item['release_date']}")
            add_url(lines, item["url"])
        elif category == "conference_calls":
            lines.append(f"截止：{item['deadline']}")
            add_url(lines, item["official_url"])
        else:
            add_url(lines, item["url"])
    lines.append("本期详版")
    add_url(lines, detail_url(issue))
    return "\n".join(lines) + "\n"


def render_daily(issue: dict) -> str:
    """Render all eligible core items once, without audience variants."""
    if uses_v2(issue):
        return render_daily_v2(issue)
    lines = [title_line(issue), ""]
    used_labels: set[str] = set()
    selected = 0
    for category in CORE_CATEGORY_ORDER:
        if selected >= 5:
            break
        items = [item for item in issue.get(category, []) if item.get("priority") == "core"]
        if not items:
            continue
        label = SECTION_LABELS[category]
        if label not in used_labels:
            lines.append(label)
            used_labels.add(label)
        for item in items:
            if selected >= 5:
                break
            add_daily_item(lines, item, category)
            selected += 1
    lines.append("本期详版")
    add_url(lines, detail_url(issue))
    return "\n".join(lines) + "\n"


def render_conference(issue: dict) -> str:
    lines = [title_line(issue), "", SECTION_LABELS["conference_calls"]]
    for item in issue.get("conference_calls", []):
        if item.get("priority") != "core":
            continue
        lines.append(item["title"])
        lines.append(f"主题或范围：{item['topic']}；截止日期：{item['deadline']}")
        add_url(lines, item["official_url"])
    lines.append("本期详版")
    add_url(lines, detail_url(issue))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成全课程群共用的微信群纯文本短版。")
    parser.add_argument("--input", required=True, type=Path, help="期次 JSON 文件")
    parser.add_argument("--output-dir", required=True, type=Path, help="输出目录")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as handle:
        issue = json.load(handle)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rendered = render_conference(issue) if issue["issue_type"] == "conference-bulletin" else render_daily(issue)
    output = args.output_dir / f"{issue['date']}.txt"
    output.write_text(rendered, encoding="utf-8")
    print(f"WROTE {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
