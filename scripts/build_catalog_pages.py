#!/usr/bin/env python3
"""Build visitor-facing lists from real published issue JSON files only."""

from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path

from site_config import date_compact, is_public_issue, issue_title
from website_tags import tag_links

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "content" / "issues"
TOPICS_DIR = ROOT / "topics"
from website_content import SECTIONS, DISPLAY_LABELS, public_summary, inline_code
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
    seen = set()
    from trial_selection import identities
    from public_history import collections, resolve
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
                if identities(item) & seen: continue
                seen.update(identities(item))
                collected.append({
                    "id": item["id"], "date": issue["date"], "title": item["title"], "note": public_summary(item),
                    "section": catalog["section"], "catalog": catalog,
                })
    for slug, data in collections():
        for row in data['entries']:
            item = resolve(row)
            if identities(item) & seen: continue
            seen.update(identities(item))
            collected.append(dict(id=item['id'], date=row['source_date'], title=item['title'], note=public_summary(item), section=item['catalog']['section'], catalog=item['catalog'], history_slug=slug))
    return sorted(collected, key=lambda value: (value["date"], value["title"]), reverse=True)


def card(entry: dict) -> str:
    date_link = f"../issues/{date_compact(entry['date'])}/#{entry['id']}"
    if entry.get('history_slug'):
        date_link = '../history/' + entry['history_slug'] + '/#' + entry['id']
    date_label = '来源日期' if entry.get('history_slug') else '期次日期'
    link_label = '查看历史条目' if entry.get('history_slug') else '查看本期'
    labels = []
    for field, label in TAG_FIELDS:
        values = entry["catalog"][field]
        if values:
            labels.append(f"<strong>{label}：</strong>{tag_links(values)}")
    if entry["catalog"]["tags"]:
        labels.append(f"<strong>标签：</strong>{tag_links(entry['catalog']['tags'])}")
    metadata = "；".join(labels) or ""
    return f'''<article class="catalog-card">
<h3>{escape(entry['title'])}</h3>
<p class="catalog-meta">{date_label}：{escape(entry['date'])}</p>
<p>{inline_code(entry['note'])}</p>
<p class="catalog-tags">{metadata}</p>
<p><a href="{date_link}">{link_label}</a></p>
</article>'''


def page_header(title: str, description: str) -> list[str]:
    return [
        "---", f'title: "{title}"', "---", "",
        "<!-- 此文件由 scripts/build_catalog_pages.py 从真实 published 期次生成。 -->", "",
        f'<p class="catalog-intro">{description}</p>', "",
    ]


PAGE_SIZE = 10
GENERATED_MARKER = '<!-- 此文件由 scripts/build_catalog_pages.py 从真实 published 期次生成。 -->'


def page_count(values):
    return max(1, (len(values) + PAGE_SIZE - 1) // PAGE_SIZE)


def page_name(stem, page, extension='qmd'):
    return f"{stem}{'-' + str(page) if page > 1 else ''}.{extension}"


def page_slice(values, page):
    if not 1 <= page <= page_count(values):
        raise ValueError('分页编号超出范围')
    return values[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]


def pagination(stem, values, page, position='上方'):
    total = page_count(values)
    links = []
    if page > 1:
        links.append(f'<a href="{page_name(stem, 1, "html")}">首页</a>')
        links.append(f'<a rel="prev" href="{page_name(stem, page - 1, "html")}">上一页</a>')
    links.append(f'<span aria-current="page">第 {page} / {total} 页 · 共 {len(values)} 条</span>')
    if page < total:
        links.append(f'<a rel="next" href="{page_name(stem, page + 1, "html")}">下一页</a>')
        links.append(f'<a href="{page_name(stem, total, "html")}">末页</a>')
    return f'<nav class="catalog-pagination" aria-label="{position}分页">' + ''.join(links) + '</nav>'


def section_page(title: str, description: str, values: list[dict], page=1, identifier=None) -> str:
    identifier = identifier or next(key for key, name, _ in SECTIONS if name == title)
    selected = page_slice(values, page)
    intro = '<a href="https://www.lianxh.cn" target="_blank" rel="noopener noreferrer">lianxh.cn 最新推文</a>' if title == '新推文' else ''
    lines = page_header(title if page == 1 else f'{title} · 第 {page} 页', intro)
    lines += ['<p class="catalog-meta">每页最多 10 条 · 按关键词查找请使用顶部搜索</p>', '', pagination(identifier, values, page), '']
    if selected:
        lines.extend(['<div class="catalog-grid">', *[card(value) for value in selected], "</div>", ""])
    else:
        lines.extend(['<p class="catalog-empty">正式快讯将在首次发布后归档。</p>', ''])
    if page_count(values) > 1:
        lines.extend([pagination(identifier, values, page, '下方'), ''])
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
    for field, label in (*TAG_FIELDS, ("tags", "内容标签")):
        values_text = sorted({str(tag) for value in values for tag in value["catalog"][field]})
        text = tag_links(values_text) if values_text else "暂无标签。"
        lines.extend([f'''<section class="catalog-tag-group">
<h3>{label}</h3>
<p>{text}</p>
</section>''', ""])
    lines.extend([render_promotion(), ""])
    return "\n".join(lines)


def home_page(issues: list[dict]) -> str:
    lines = [
        "---", 'title: "连享会 · 快讯"', "body-classes: home-page", "---", "",
        '<div class="brief-cover">',
        '  <img src="assets/brand/brief/lianxh-brief-cover.jpg" alt="连享会 · 快讯栏目封面">',
        "</div>", "",
        "连享会 · 快讯收录新推文、近期论文、Stata、R、Python 工具，以及会议征稿信息。", "",
        "微信群版分享简要信息，网页版提供完整介绍与阅读资料。可按栏目、日期或关键词继续浏览。", "",
        "## 最新期次", "",
    ]
    if issues:
        for issue in issues[:3]:
            lines.append(f"- [{issue_title(issue)}](issues/{date_compact(issue['date'])}/)")
    else:
        lines.append("<p class=\"catalog-empty\">正式快讯将在首次发布后归档。</p>")
    lines.extend(["", "## 按内容浏览", "", '<div class="catalog-grid catalog-grid--overview">'])
    for key, _, description in SECTIONS:
        lines.append(f'<article class="catalog-card"><h3><a href="topics/{key}.qmd">{DISPLAY_LABELS[key]}</a></h3></article>')
    lines.extend(['</div>', '', '使用顶部搜索查找标题、工具或关键词。', ''])
    lines.extend(["", "可按内容类型查看[栏目索引](topics/index.qmd)，或在[往期](archive.qmd)中按日期查阅公开期次。", ""])
    lines.extend([render_home_promotion(), ""])
    return "\n".join(lines)


def archive_years(issues):
    return sorted({issue['date'][:4] for issue in issues}, reverse=True)


def archive_navigation(years, page):
    if len(years) <= 1:
        return ''
    links = []
    for n, year in enumerate(years, 1):
        if n == page:
            links.append(f'<span aria-current="page">{year} 年</span>')
        else:
            links.append(f'<a href="{page_name("archive", n, "html")}">{year} 年</a>')
    return '<nav class="catalog-pagination" aria-label="归档年份">' + ''.join(links) + '</nav>'


def archive_page(issues: list[dict], page=1) -> str:
    years = archive_years(issues)
    if not 1 <= page <= max(1, len(years)):
        raise ValueError('归档年份页超出范围')
    lines = page_header('往期', '按年份和月份展开，查阅每日快讯')
    lines.insert(2, 'toc: false')
    if (ROOT / "history/20260815-20260907/index.qmd").exists():
        lines.extend(["[历史精选：2026-08-15 至 2026-09-07](history/20260815-20260907/)", ""])
    if years:
        year = years[page - 1]
        selected = sorted([i for i in issues if i['date'].startswith(year + '-')], key=lambda i: i['date'], reverse=True)
        months = sorted({i['date'][:7] for i in selected}, reverse=True)
        lines += [archive_navigation(years, page), '', '<div class="archive-tree">',
                  f'<details class="archive-year" open><summary>{year} 年 <span>{len(selected)} 期</span></summary>']
        month_open = ' open' if len(issues) <= 31 and len(years) == 1 else ''
        for month in months:
            days = [i for i in selected if i['date'].startswith(month + '-')]
            lines += [f'<details class="archive-month"{month_open}><summary>{int(month[5:])} 月 <span>{len(days)} 期</span></summary>', '<ul class="archive-days">']
            for issue in days:
                lines.append(f'<li><a href="issues/{date_compact(issue["date"])}/">{issue_title(issue)}</a></li>')
            lines += ['</ul>', '</details>']
        lines += ['</details>', '</div>', '']
    else:
        lines += ['正式快讯将在首次发布后归档。', '']
    lines += [render_promotion(), '']
    return "\n".join(lines)


def write_if_changed(path: Path, text: str) -> None:
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
        print(f"WROTE {path.relative_to(ROOT)}")
    else:
        print(f"UNCHANGED {path.relative_to(ROOT)}")


def catalog_outputs(issues, values):
    outputs = {'index.qmd': home_page(issues), 'topics/index.qmd': index_page(values)}
    for page in range(1, max(1, len(archive_years(issues))) + 1):
        outputs[page_name('archive', page)] = archive_page(issues, page)
    for key, title, description in SECTIONS:
        selected = [value for value in values if value['section'] == key]
        for page in range(1, page_count(selected) + 1):
            outputs['topics/' + page_name(key, page)] = section_page(title, description, selected, page, key)
    return outputs


def stale_catalog_pages(outputs):
    # 只识别本生成器拥有的分页文件，避免误删手工页面。
    import re
    stems = ['archive', *['topics/' + key for key, _, _ in SECTIONS]]
    stale = []
    for stem in stems:
        parent, name = (ROOT / stem).parent, Path(stem).name
        for path in parent.glob(name + '-*.qmd'):
            if not re.fullmatch(re.escape(name) + r'-[2-9][0-9]*\.qmd|' + re.escape(name) + r'-1[0-9]+\.qmd', path.name):
                continue
            if path.relative_to(ROOT).as_posix() not in outputs:
                if GENERATED_MARKER not in path.read_text(encoding='utf-8'):
                    raise ValueError('分页文件与手工文件冲突：' + str(path))
                stale.append(path)
    return stale


def main() -> int:
    # 单独入口也经过正式构建的内容验收，避免两套生成逻辑分叉。
    from build_website import build
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
