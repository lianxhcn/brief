#!/usr/bin/env python3
"""Build public catalog pages from public issue JSON files only."""

from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path

from site_config import date_compact

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "content" / "issues"
TOPICS_DIR = ROOT / "topics"
SECTIONS = (
    ("lianxh-new", "连享新文", "连享会的新文章、讲义与资源说明。"),
    ("research-frontier", "论文前沿", "已筛选的论文与研究成果。"),
    ("methods-tools", "方法工具", "软件、方法、复现与数据处理工具。"),
    ("academic-updates", "学术动态", "会议、征文、专题征稿与合格公益性活动。"),
)
SECTION_MAP = {identifier: (title, description) for identifier, title, description in SECTIONS}
CATEGORIES = ("lianxh_posts", "papers", "tools", "research_resources", "conference_calls")
TAG_FIELDS = (("software", "软件平台"), ("methods", "研究方法"), ("fields", "研究领域"))


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def entries() -> list[dict]:
    collected: list[dict] = []
    for path in sorted(SOURCE_DIR.glob("*.json")):
        issue = json.loads(path.read_text(encoding="utf-8"))
        for category in CATEGORIES:
            for item in issue.get(category, []):
                catalog = item.get("catalog")
                if not isinstance(catalog, dict) or catalog.get("section") not in SECTION_MAP:
                    raise ValueError(f"{path}: {item.get('id', '<unknown>')} 缺少有效 catalog.section")
                for field, _ in TAG_FIELDS:
                    if not isinstance(catalog.get(field), list):
                        raise ValueError(f"{path}: {item.get('id', '<unknown>')} 的 catalog.{field} 必须是列表")
                if not isinstance(catalog.get("tags"), list):
                    raise ValueError(f"{path}: {item.get('id', '<unknown>')} 的 catalog.tags 必须是列表")
                collected.append({
                    "date": issue["date"], "status": issue["status"], "title": item["title"],
                    "note": item["page_note"], "section": catalog["section"],
                    "catalog": catalog, "category": category,
                })
    return sorted(collected, key=lambda value: (value["date"], value["title"]), reverse=True)


def card(entry: dict) -> str:
    date_link = f"../{date_compact(entry['date'])}/"
    title = escape(entry["title"])
    date_value = escape(entry["date"])
    status = escape(entry["status"].upper())
    note = escape(entry["note"])
    labels = []
    for field, label in TAG_FIELDS:
        values = entry["catalog"][field]
        if values:
            labels.append(f"{label}：{escape('、'.join(values))}")
    if entry["catalog"]["tags"]:
        labels.append(f"标签：{escape('、'.join(entry['catalog']['tags']))}")
    metadata = "；".join(labels) or "未设置附加标签。"
    return f'''<article class="catalog-card">
<h3>{title}</h3>
<p class="catalog-meta">日期：{date_value}；状态：{status}</p>
<p>{note}</p>
<p class="catalog-tags">{metadata}</p>
<p><a href="{date_link}">查看日期详版</a></p>
</article>'''


def page_header(title: str, description: str) -> list[str]:
    return [
        "<!-- 此文件由 scripts/build_catalog_pages.py 从 content/issues/*.json 生成。 -->",
        "---", f'title: "{title}"', "---", "",
        f'<p class="catalog-intro">{description} 当前公开条目均为 <strong>DEMO</strong>，仅用于验证页面结构，不代表真实资讯。</p>', "",
    ]


def section_page(identifier: str, title: str, description: str, values: list[dict]) -> str:
    lines = page_header(title, description)
    lines.extend(["## 公开期次", ""])
    if values:
        lines.extend(['<div class="catalog-grid">', *[card(value) for value in values], "</div>", ""])
    else:
        lines.extend(['<p class="catalog-empty">当前没有公开条目。</p>', ""])
    lines.extend(["[返回栏目索引](index.qmd)", ""])
    return "\n".join(lines)


def index_page(values: list[dict]) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for value in values:
        grouped[value["section"]].append(value)
    lines = page_header("栏目索引", "按内容类型浏览公开期次。软件、方法与研究领域是可叠加标签，不构成一级栏目。")
    lines.extend(["## 一级栏目", "", '<div class="catalog-grid">'])
    for identifier, title, description in SECTIONS:
        count = len(grouped[identifier])
        lines.append(f'''<article class="catalog-card">
<h3><a href="{identifier}.qmd">{title}</a></h3>
<p>{description}</p>
<p class="catalog-meta">当前 {count} 条公开条目；均为 DEMO。</p>
</article>''')
    lines.extend(["</div>", "", "## 标签概览", ""])
    for field, label in TAG_FIELDS:
        labels = sorted({str(tag) for value in values for tag in value["catalog"][field]})
        text = "、".join(labels) if labels else "暂无标签。"
        lines.append(f'''<section class="catalog-tag-group">
<h3>{label}</h3>
<p>{escape(text)}</p>
</section>''')
        lines.append("")
    return "\n".join(lines)


def write_if_changed(path: Path, text: str) -> None:
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
        print(f"WROTE {path.relative_to(ROOT)}")
    else:
        print(f"UNCHANGED {path.relative_to(ROOT)}")


def main() -> int:
    values = entries()
    TOPICS_DIR.mkdir(exist_ok=True)
    write_if_changed(TOPICS_DIR / "index.qmd", index_page(values))
    for identifier, title, description in SECTIONS:
        section_values = [value for value in values if value["section"] == identifier]
        write_if_changed(TOPICS_DIR / f"{identifier}.qmd", section_page(identifier, title, description, section_values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())