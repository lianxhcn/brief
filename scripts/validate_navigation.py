#!/usr/bin/env python3
"""Validate the frozen Task 05-v2 navigation and catalog surfaces."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAV_TEXT = ("连享会 · 快讯", "最新快讯", "栏目索引", "历史归档", "连享会", "课程中心")
TOPICS = ("index", "lianxh-new", "research-frontier", "methods-tools", "academic-updates")
OLD_NAV = ("text: Stata 与因果", "text: R、Python 与机器学习", "text: 金融")


def main() -> int:
    errors: list[str] = []
    quarto = (ROOT / "_quarto.yml").read_text(encoding="utf-8")
    for value in NAV_TEXT:
        if value not in quarto:
            errors.append(f"_quarto.yml 缺少导航文字：{value}")
    for value in OLD_NAV:
        if value in quarto:
            errors.append(f"_quarto.yml 仍含旧一级导航：{value}")
    for url in ("https://www.lianxh.cn/", "https://www.lianxh.cn/KC.html"):
        source_pattern = rf'href: {re.escape(url)}\s+text: .+\s+target: _blank\s+rel: noopener noreferrer'
        if not re.search(source_pattern, quarto):
            errors.append(f"_quarto.yml 的外链缺少新窗口安全属性：{url}")
    home_html = (ROOT / "_site" / "index.html").read_text(encoding="utf-8")
    for url in ("https://www.lianxh.cn/", "https://www.lianxh.cn/KC.html"):
        match = re.search(rf'<a[^>]*href="{re.escape(url)}"[^>]*>', home_html)
        if not match or 'target="_blank"' not in match.group() or 'rel="noopener noreferrer"' not in match.group():
            errors.append(f"首页外链缺少新窗口安全属性：{url}")
    for stem in TOPICS:
        source = ROOT / "topics" / f"{stem}.qmd"
        rendered = ROOT / "_site" / "topics" / f"{stem}.html"
        if not source.exists() or not rendered.exists():
            errors.append(f"缺少栏目页：{source if not source.exists() else rendered}")
            continue
        source_text = source.read_text(encoding="utf-8")
        rendered_text = rendered.read_text(encoding="utf-8")
        if "DEMO" not in source_text:
            errors.append(f"{source}: 未标记 DEMO 状态")
        for value in NAV_TEXT:
            if value not in rendered_text:
                errors.append(f"{rendered}: 缺少导航文字：{value}")
        for value in ("Stata 与因果", "R、Python 与机器学习"):
            if value in rendered_text:
                errors.append(f"{rendered}: 仍将旧主题作为公开栏目")
    for stem in ("stata-causal", "r-python-ml", "finance"):
        if (ROOT / "topics" / f"{stem}.qmd").exists():
            errors.append(f"topics/{stem}.qmd 仍作为旧专题页保留")
    if errors:
        print("FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("PASS: 顶部导航、四个栏目页、DEMO 标记与外链属性均已验证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())