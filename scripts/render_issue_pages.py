#!/usr/bin/env python3
"""Generate a Quarto source page for one public issue JSON file."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

COURSE_CALLOUT = '''<aside class="course-hub-callout" role="note" aria-label="连享会课程入口">
  <p class="course-hub-callout__title">连享会课程</p>
  <p class="course-hub-callout__text">浏览连享会的课程、专题与学习资料。</p>
  <p class="course-hub-callout__action"><a href="https://www.lianxh.cn/KC.html" target="_blank" rel="noopener noreferrer">查看连享会课程与专题</a></p>
</aside>'''

CATEGORY_LABELS = {
    "lianxh_posts": "连享会新推文",
    "papers": "近期论文",
    "tools": "方法与工具",
    "research_resources": "研究资源",
    "conference_calls": "会议与征稿",
}


def escape(value: object) -> str:
    return html.escape(str(value), quote=False)


def item_links(item: dict, category: str) -> list[str]:
    links: list[str] = []
    if category == "papers":
        links.append(f"DOI：[{escape(item['doi_url'])}]({item['doi_url']})")
        if item.get("replication_url"):
            links.append(f"复现资料：[{escape(item['replication_url'])}]({item['replication_url']})")
    elif category == "conference_calls":
        links.append(f"官方链接：[{escape(item['official_url'])}]({item['official_url']})")
    else:
        links.append(f"资料链接：[{escape(item['url'])}]({item['url']})")
    return links


def render_item(item: dict, category: str) -> list[str]:
    lines = [f"### {escape(item['title'])} {{#{item['id']}}}", ""]
    if category == "papers":
        lines.extend([escape(item["citation"]), ""])
    elif category == "tools":
        lines.extend([f"生态：{escape(item['ecosystem'])}；名称：{escape(item['name'])}", ""])
    elif category == "conference_calls":
        lines.extend([
            f"主办方或期刊：{escape(item['organizer_or_journal'])}",
            "",
            f"主题或范围：{escape(item['topic'])}",
            "",
            f"截止日期：{escape(item['deadline'])}",
            "",
        ])
    lines.extend([escape(item["page_note"]), ""])
    for link in item_links(item, category):
        lines.extend([link, ""])
    return lines


def render_section(issue: dict, priority: str, heading: str) -> list[str]:
    lines: list[str] = [f"## {heading}", ""]
    found = False
    for category, label in CATEGORY_LABELS.items():
        items = [item for item in issue.get(category, []) if item.get("priority") == priority]
        if not items:
            continue
        found = True
        lines.extend([f"### {label}", ""])
        for item in items:
            lines.extend(render_item(item, category))
    if not found:
        lines.extend(["本期没有此分区内容。", ""])
    return lines


def render_page(issue: dict) -> str:
    status = issue["status"].upper()
    lines = [
        "---",
        f'title: "{escape(issue["title"])}"',
        "---",
        "",
        "## 状态",
        "",
        f"状态：**{status}**；日期：{issue['date']}。",
        "",
        COURSE_CALLOUT,
        "",
    ]
    lines.extend(render_section(issue, "core", "本期重点"))
    lines.extend(render_section(issue, "extended", "延伸信息"))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="从期次 JSON 生成 Quarto 日期详版。")
    parser.add_argument("--input", required=True, type=Path, help="期次 JSON 文件")
    parser.add_argument("--output-dir", required=True, type=Path, help="日期详版 QMD 输出目录")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as handle:
        issue = json.load(handle)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / f"{issue['date']}.qmd"
    output.write_text(render_page(issue), encoding="utf-8")
    print(f"WROTE {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())