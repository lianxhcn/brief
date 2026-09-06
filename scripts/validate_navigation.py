#!/usr/bin/env python3
"""Validate the Task 07 compact navigation and DEMO-free public lists."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAV_TEXT = ("连享会 · 快讯", "新推文", "新论文", "新方法", "会议征稿", "往期", "官网", "课程")
TOPICS = ("index", "lianxh-new", "research-frontier", "methods-tools", "academic-updates")


def main() -> int:
    errors: list[str] = []
    quarto = (ROOT / "_quarto.yml").read_text(encoding="utf-8")
    for value in NAV_TEXT:
        if value not in quarto:
            errors.append(f"_quarto.yml 缺少导航文字：{value}")
    if "search: true" not in quarto:
        errors.append("_quarto.yml 未启用搜索")
    for value in ("最新快讯", "栏目索引", "历史归档", "Stata 与因果", "R、Python 与机器学习"):
        if value in quarto:
            errors.append(f"_quarto.yml 仍含不应占用顶部导航的文字：{value}")
    for url in ("https://www.lianxh.cn/", "https://www.lianxh.cn/KC.html"):
        source_pattern = rf'href: {re.escape(url)}\s+text: .+\s+target: _blank\s+rel: noopener noreferrer'
        if not re.search(source_pattern, quarto):
            errors.append(f"_quarto.yml 的外链缺少新窗口安全属性：{url}")
    home_html = (ROOT / "_site" / "index.html").read_text(encoding="utf-8")
    for value in NAV_TEXT:
        if value not in home_html:
            errors.append(f"首页渲染结果缺少导航文字：{value}")
    if "quarto-search" not in home_html:
        errors.append("首页渲染结果缺少搜索功能")
    if "navbar-toggler" not in home_html:
        errors.append("首页渲染结果缺少窄屏折叠菜单触发器")
    styles = (ROOT / "styles.css").read_text(encoding="utf-8")
    if "overflow-x" in styles:
        errors.append("styles.css 不应为导航添加横向滚动")
    for source in (ROOT / "index.qmd", ROOT / "archive.qmd", *(ROOT / "topics" / f"{stem}.qmd" for stem in TOPICS)):
        text = source.read_text(encoding="utf-8")
        if "2099" in text or "DEMO" in text:
            errors.append(f"{source}: 公共列表仍暴露 DEMO 内容")
    for stem in TOPICS:
        source = ROOT / "topics" / f"{stem}.qmd"
        rendered = ROOT / "_site" / "topics" / f"{stem}.html"
        if not source.exists() or not rendered.exists():
            errors.append(f"缺少栏目页：{source if not source.exists() else rendered}")
            continue
        rendered_text = rendered.read_text(encoding="utf-8")
        if "2099" in rendered_text or "DEMO" in rendered_text:
            errors.append(f"{rendered}: 公共页面仍暴露 DEMO 内容")
    for stem in ("stata-causal", "r-python-ml", "finance"):
        if (ROOT / "topics" / f"{stem}.qmd").exists():
            errors.append(f"topics/{stem}.qmd 仍作为旧专题页保留")
    if errors:
        print("FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("PASS: 紧凑导航、搜索、窄屏折叠与 DEMO 隔离均已验证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
