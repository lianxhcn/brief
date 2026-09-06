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
from website_content import SECTIONS, DISPLAY_LABELS, public_summary
SECTION_MAP = {identifier: (title, description) for identifier, title, description in SECTIONS}
CATEGORIES = ("lianxh_posts", "papers", "tools", "research_resources", "conference_calls")
TAG_FIELDS = (("software", "软件"), ("methods", "方法"), ("fields", "研究领域"))
from website_promotions import render_promotion, render_home_promotion



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
                    "id": item["id"], "date": issue["date"], "title": item["title"], "note": public_summary(item),
                    "section": catalog["section"], "catalog": catalog,
                })
    return sorted(collected, key=lambda value: (value["date"], value["title"]), reverse=True)


def card(entry: dict) -> str:
    date_link = f"../issues/{date_compact(entry['date'])}/#{entry['id']}"
    labels = []
    for field, label in TAG_FIELDS:
        values = entry["catalog"][field]
        if values:
            labels.append(f"<strong>{label}：</strong>{escape('、'.join(values))}")
    if entry["catalog"]["tags"]:
        labels.append(f"<strong>标签：</strong>{escape('、'.join(entry['catalog']['tags']))}")
    metadata = "；".join(labels) or "未设置附加标签。"
    return f'''<article class="catalog-card">
<h3>{escape(entry['title'])}</h3>
<p class="catalog-meta">日期：{escape(entry['date'])}</p>
<p>{escape(entry['note'])}</p>
<p class="catalog-tags">{metadata}</p>
<p><a href="{date_link}">查看本期</a></p>
</article>'''


def page_header(title: str, description: str) -> list[str]:
    return [
        "---", f'title: "{title}"', "---", "",
        "<!-- 此文件由 scripts/build_catalog_pages.py 从真实 published 期次生成。 -->", "",
        f'<p class="catalog-intro">{description}</p>', "",
    ]


def section_page(title: str, description: str, values: list[dict]) -> str:
    intro = '<a href="https://www.lianxh.cn" target="_blank" rel="noopener noreferrer">lianxh.cn 最新推文</a>' if title == '新推文' else ''
    lines = page_header(title, intro)
    if values:
        lines.extend(['<div class="catalog-grid">', *[card(value) for value in values], "</div>", ""])
    else:
        lines.extend(["<p class=\"catalog-empty\">正式快讯将在首次发布后归档。</p>", ""])
    lines.extend([render_promotion(), ""])
    return "\n".join(lines)


def index_page(values: list[dict]) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for value in values:
        grouped[value["section"]].append(value)
    lines = page_header("栏目索引", "按栏目或标签查找感兴趣的内容。")
    lines.extend(["## 内容栏目", "", '<div class="catalog-grid catalog-grid--overview">'])
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
    lines.extend([render_promotion(), ""])
    return "\n".join(lines)


def home_page(issues: list[dict]) -> str:
    lines = [
        "---", 'title: "连享会 · 快讯"', "---", "",
        '<div class="brief-cover">',
        '  <img src="assets/brand/brief/lianxh-brief-cover.jpg" alt="连享会 · 快讯栏目封面">',
        "</div>", "",
        "连享会 · 快讯收录新推文、近期论文、Stata、R、Python 工具，以及会议征稿信息。", "",
        "微信群版分享简要信息，网页版提供完整介绍与阅读资料。可按栏目、日期或关键词继续浏览。", "",
        "## 最新期次", "",
    ]
    if issues:
        for issue in issues[:1]:
            lines.append(f"- [{escape(issue['title'])}](issues/{date_compact(issue['date'])}/)")
    else:
        lines.append("<p class=\"catalog-empty\">正式快讯将在首次发布后归档。</p>")
    lines.extend(["", "## 按内容浏览", "", '<div class="catalog-grid catalog-grid--overview">'])
    for key, _, description in SECTIONS:
        lines.append(f'<article class="catalog-card"><h3><a href="topics/{key}.qmd">{DISPLAY_LABELS[key]}</a></h3><p>{description}</p></article>')
    lines.extend(['</div>', '', '使用顶部搜索查找标题、工具或关键词。', ''])
    lines.extend(["", "可按内容类型查看[栏目索引](topics/index.qmd)，或在[往期](archive.qmd)中按日期查阅公开期次。", ""])
    lines.extend([render_home_promotion(), ""])
    return "\n".join(lines)


def archive_page(issues: list[dict]) -> str:
    lines = ["---", 'title: "往期"', "---", "", "下列链接直达按日期生成的网页版。", ""]
    if issues:
        month = None
        for issue in issues:
            if issue["date"][:7] != month:
                month = issue["date"][:7]
                lines.extend([f"## {month}", ""])
            lines.append(f"- [{issue['date']}｜连享会 · 快讯](issues/{date_compact(issue['date'])}/)")
    else:
        lines.append("正式快讯将在首次发布后归档。")
    lines.extend(["", render_promotion(), ""])
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
        write_if_changed(TOPICS_DIR / f"{identifier}.qmd", section_page(DISPLAY_LABELS[identifier], description, section_values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
