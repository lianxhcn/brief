#!/usr/bin/env python3
"""Build visitor-facing lists from real published issue JSON files only."""

from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path

from site_config import date_compact, is_public_issue

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "content" / "issues"
TOPICS_DIR = ROOT / "topics"
SECTIONS = (
    ("lianxh-new", "推文", "连享会的新文章、讲义与资源说明。"),
    ("research-frontier", "论文", "已筛选的论文与研究成果。"),
    ("methods-tools", "新方法", "软件、方法、复现与数据处理工具。"),
    ("academic-updates", "会议征稿", "会议、征文、专题征稿与合格公益性活动。"),
)
SECTION_MAP = {identifier: (title, description) for identifier, title, description in SECTIONS}
CATEGORIES = ("lianxh_posts", "papers", "tools", "research_resources", "conference_calls")
TAG_FIELDS = (("software", "软件平台"), ("methods", "研究方法"), ("fields", "研究领域"))
COURSE_CALLOUT = '''<aside class="course-hub-callout" role="note" aria-label="连享会课程入口">
  <p class="course-hub-callout__title">连享会课程</p>
  <p class="course-hub-callout__text">浏览连享会的课程、专题与学习资料。</p>
  <p class="course-hub-callout__action"><a href="https://www.lianxh.cn/KC.html" target="_blank" rel="noopener noreferrer">查看连享会课程与专题</a></p>
</aside>'''


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def public_issues() -> list[dict]:
    issues: list[dict] = []
    for path in sorted(SOURCE_DIR.glob("*.json")):
        issue = json.loads(path.read_text(encoding="utf-8"))
        if is_public_issue(issue):
            issues.append(issue)
    return sorted(issues, key=lambda issue: issue["date"], reverse=True)


def entries(issues: list[dict]) -> list[dict]:
    collected: list[dict] = []
    for issue in issues:
        for category in CATEGORIES:
            for item in issue.get(category, []):
                catalog = item.get("catalog")
                if not isinstance(catalog, dict) or catalog.get("section") not in SECTION_MAP:
                    raise ValueError(f"{issue['issue_id']}: {item.get('id', '<unknown>')} 缺少有效 catalog.section")
                for field, _ in TAG_FIELDS:
                    if not isinstance(catalog.get(field), list):
                        raise ValueError(f"{issue['issue_id']}: {item.get('id', '<unknown>')} 的 catalog.{field} 必须是列表")
                if not isinstance(catalog.get("tags"), list):
                    raise ValueError(f"{issue['issue_id']}: {item.get('id', '<unknown>')} 的 catalog.tags 必须是列表")
                collected.append({
                    "date": issue["date"], "title": item["title"], "note": item["page_note"],
                    "section": catalog["section"], "catalog": catalog,
                })
    return sorted(collected, key=lambda value: (value["date"], value["title"]), reverse=True)


def card(entry: dict) -> str:
    date_link = f"../{date_compact(entry['date'])}/"
    labels = []
    for field, label in TAG_FIELDS:
        values = entry["catalog"][field]
        if values:
            labels.append(f"{label}：{escape('、'.join(values))}")
    if entry["catalog"]["tags"]:
        labels.append(f"标签：{escape('、'.join(entry['catalog']['tags']))}")
    metadata = "；".join(labels) or "未设置附加标签。"
    return f'''<article class="catalog-card">
<h3>{escape(entry['title'])}</h3>
<p class="catalog-meta">日期：{escape(entry['date'])}</p>
<p>{escape(entry['note'])}</p>
<p class="catalog-tags">{metadata}</p>
<p><a href="{date_link}">查看日期详版</a></p>
</article>'''


def page_header(title: str, description: str) -> list[str]:
    return [
        "---", f'title: "{title}"', "---", "",
        "<!-- 此文件由 scripts/build_catalog_pages.py 从真实 published 期次生成。 -->", "",
        f'<p class="catalog-intro">{description}</p>', "",
    ]


def section_page(title: str, description: str, values: list[dict]) -> str:
    lines = page_header(title, description)
    lines.extend(["## 公开期次", ""])
    if values:
        lines.extend(['<div class="catalog-grid">', *[card(value) for value in values], "</div>", ""])
    else:
        lines.extend(["<p class=\"catalog-empty\">正式快讯将在首次发布后归档。</p>", ""])
    lines.extend(["[查看栏目索引](index.qmd)", ""])
    return "\n".join(lines)


def index_page(values: list[dict]) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for value in values:
        grouped[value["section"]].append(value)
    lines = page_header("栏目索引", "按内容类型浏览公开期次。软件、方法与研究领域是可叠加标签，不构成一级栏目。")
    lines.extend(["## 内容栏目", "", '<div class="catalog-grid">'])
    for identifier, title, description in SECTIONS:
        lines.append(f'''<article class="catalog-card">
<h3><a href="{identifier}.qmd">{title}</a></h3>
<p>{description}</p>
<p class="catalog-meta">当前 {len(grouped[identifier])} 条公开条目。</p>
</article>''')
    lines.extend(["</div>", "", "## 标签概览", ""])
    for field, label in TAG_FIELDS:
        values_text = sorted({str(tag) for value in values for tag in value["catalog"][field]})
        text = "、".join(values_text) if values_text else "暂无标签。"
        lines.extend([f'''<section class="catalog-tag-group">
<h3>{label}</h3>
<p>{escape(text)}</p>
</section>''', ""])
    return "\n".join(lines)


def home_page(issues: list[dict]) -> str:
    lines = [
        "---", 'title: "连享会 · 快讯"', "---", "",
        '<div class="brief-cover">',
        '  <img src="assets/brand/brief/lianxh-brief-cover.jpg" alt="连享会 · 快讯栏目封面">',
        "</div>", "",
        "这是连享会 · 快讯的公开归档。网页详版和全课程群共用的短版均由同一数据源生成。", "",
        COURSE_CALLOUT, "", "## 快讯归档", "",
    ]
    if issues:
        for issue in issues:
            lines.append(f"- [{escape(issue['title'])}]({date_compact(issue['date'])}/)")
    else:
        lines.append("<p class=\"catalog-empty\">正式快讯将在首次发布后归档。</p>")
    lines.extend(["", "可按内容类型查看[栏目索引](topics/index.qmd)，或在[往期](archive.qmd)中按日期查阅公开期次。", ""])
    return "\n".join(lines)


def archive_page(issues: list[dict]) -> str:
    lines = ["---", 'title: "往期"', "---", "", "下列链接直达按日期生成的公开详版。", ""]
    if issues:
        for issue in issues:
            lines.append(f"- [{issue['date']}：{escape(issue['title'])}]({date_compact(issue['date'])}/)")
    else:
        lines.append("正式快讯将在首次发布后归档。")
    lines.append("")
    return "\n".join(lines)


def write_if_changed(path: Path, text: str) -> None:
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
        print(f"WROTE {path.relative_to(ROOT)}")
    else:
        print(f"UNCHANGED {path.relative_to(ROOT)}")


def main() -> int:
    issues = public_issues()
    values = entries(issues)
    TOPICS_DIR.mkdir(exist_ok=True)
    write_if_changed(ROOT / "index.qmd", home_page(issues))
    write_if_changed(ROOT / "archive.qmd", archive_page(issues))
    write_if_changed(TOPICS_DIR / "index.qmd", index_page(values))
    for identifier, title, description in SECTIONS:
        section_values = [value for value in values if value["section"] == identifier]
        write_if_changed(TOPICS_DIR / f"{identifier}.qmd", section_page(title, description, section_values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
