#!/usr/bin/env python3
"""从共享事实与已审核读者文案生成网站详版，不修改微信输出。"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

from site_config import date_compact, is_public_issue
from website_citations import website_citation, external_link
from website_content import CATEGORY_LABELS, public_summary
from website_promotions import render_promotion


def escape(value: object) -> str:
    return html.escape(str(value), quote=False)


def item_links(item: dict, category: str) -> list[str]:
    if category == 'papers':
        # Link/PDF/Google 已由 myAPA 输出，仅补充不重复的复现资源。
        return [external_link('复现资料', item['replication_url'])] if item.get('replication_url') else []
    if category == 'conference_calls':
        return [external_link('官方通知', item['official_url'])]
    url = item['url']
    label = {'cran.r-project.org': 'CRAN', 'pypi.org': 'PyPI'}.get(urlsplit(url).netloc)
    return [external_link(label or ('阅读全文' if category == 'lianxh_posts' else '官方文档'), url)]


def render_item(item: dict, category: str, public: bool = True) -> list[str]:
    lines = ['::: {.brief-entry}', '', f"#### {escape(item['title'])} {{#{item['id']}}}", '']
    if category == 'papers':
        lines.extend([website_citation(item) if public else escape(item['citation']), ''])
    if category == 'conference_calls':
        lines.extend([f"**投稿截止：{escape(item['deadline'])}**", ''])
    lines.extend([escape(public_summary(item) if public else item['page_note']), ''])
    lines.extend([' · '.join(item_links(item, category)), '', ':::', ''])
    return lines


def render_section(issue: dict, priority: str, heading: str) -> list[str]:
    groups = [(category, label, [i for i in issue.get(category, []) if i.get('priority') == priority])
              for category, label in CATEGORY_LABELS.items()]
    if not any(items for _, _, items in groups):
        return []
    lines = [f'## {heading}', '']
    for category, label, items in groups:
        if items:
            lines.extend([f'### {label}', ''])
            for item in items:
                lines.extend(render_item(item, category, is_public_issue(issue)))
    return lines


def render_page(issue: dict) -> str:
    public = is_public_issue(issue)
    # status/date 继续由原始 JSON 提供给验证器，正式正文不重复展示。
    title = '连享会 · 快讯 | ' + issue['date'].replace('-', '.') if public else issue['title']
    lines = ['---', 'title: ' + json.dumps(title, ensure_ascii=False), 'body-classes: issue-page', 'toc-depth: 3']
    if not public:
        lines.extend(['search: false', 'sitemap: false',
                      'header-includes: \'<meta name="robots" content="noindex, nofollow">\''])
    lines.extend(['---', ''])
    if not public:
        lines.extend([f"测试状态：{issue['status'].upper()}", ''])
    lines.extend(render_section(issue, 'core', '本期重点'))
    lines.extend(render_section(issue, 'extended', '延伸信息'))
    if public:
        lines.extend([render_promotion(), ''])
    return '\n'.join(lines).rstrip() + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    issue = json.loads(args.input.read_text(encoding='utf-8'))
    output = args.output_dir / 'issues' / date_compact(issue['date']) / 'index.qmd'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_page(issue), encoding='utf-8')
    print(f'WROTE {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
