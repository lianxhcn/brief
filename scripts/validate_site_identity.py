#!/usr/bin/env python3
"""Check the public identity, routes, and web/WeChat separation for this site."""

from __future__ import annotations

import json
from pathlib import Path

from site_config import CONFIG_PATH, ROOT, SITE, date_compact, detail_url

EXPECTED_CONFIG = {
    "site_title": "连享会 · 快讯",
    "github_owner": "lianxhcn",
    "github_repository": "brief",
    "public_base_url": "https://lianxhcn.github.io/brief",
    "detail_url_pattern": "/{date_compact}/",
    "custom_domain": None,
    "alicloud_mirror": False,
}
FORBIDDEN_IDENTITIES = (
    "lianxhcn/lianxh-group-briefs",
    "lianxhcn.github.io/lianxh-group-briefs",
    "lianxhcn/lianxh-kx",
    "lianxhcn.github.io/lianxh-kx",
    "kx.lianxh.cn",
    "阿里云",
    "Alibaba Cloud",
    r"D:\\github_lianxh\\lianxh-group-briefs",
)
FOOTER = '<a href="https://www.lianxh.cn/" target="_blank" rel="noopener noreferrer">lianxh.cn</a>'
COURSE_URL = "https://www.lianxh.cn/KC.html"
DEMO_DATES = ("2099-01-01", "2099-01-02")


def read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{path}: 无法读取：{exc}")
        return ""


def check_config(errors: list[str]) -> None:
    try:
        with CONFIG_PATH.open(encoding="utf-8") as handle:
            parsed = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{CONFIG_PATH}: JSON 无法解析：{exc}")
        return
    if parsed != EXPECTED_CONFIG or SITE != EXPECTED_CONFIG:
        errors.append("config/site.json 的公开身份字段不符合冻结方案")


def qmd_pages() -> list[tuple[Path, Path]]:
    pages = [
        (ROOT / "index.qmd", ROOT / "_site" / "index.html"),
        (ROOT / "archive.qmd", ROOT / "_site" / "archive.html"),
    ]
    pages.extend(
        (path, ROOT / "_site" / "topics" / f"{path.stem}.html")
        for path in sorted((ROOT / "topics").glob("*.qmd"))
    )
    pages.extend(
        (
            ROOT / date_compact(day) / "index.qmd",
            ROOT / "_site" / date_compact(day) / "index.html",
        )
        for day in DEMO_DATES
    )
    return pages


def check_identity_text(path: Path, text: str, errors: list[str]) -> None:
    for forbidden in FORBIDDEN_IDENTITIES:
        if forbidden in text:
            errors.append(f"{path}: 残留旧公开身份 {forbidden}")


def check_public_pages(errors: list[str]) -> None:
    quarto_text = read_text(ROOT / "_quarto.yml", errors)
    if f'title: "{SITE["site_title"]}"' not in quarto_text:
        errors.append("_quarto.yml 未使用 config/site.json 中的站点名称")
    if FOOTER not in quarto_text:
        errors.append("_quarto.yml 缺少统一 lianxh.cn 页脚")
    for source, rendered in qmd_pages():
        source_text = read_text(source, errors)
        check_identity_text(source, source_text, errors)
        rendered_text = read_text(rendered, errors)
        check_identity_text(rendered, rendered_text, errors)
        if FOOTER not in rendered_text:
            errors.append(f"{rendered}: 缺少可点击的 lianxh.cn 页脚")
    for day in DEMO_DATES:
        source = ROOT / date_compact(day) / "index.qmd"
        if COURSE_URL not in read_text(source, errors):
            errors.append(f"{source}: 缺少网页课程 Callout")


def check_routes_and_wechat(errors: list[str]) -> None:
    for day in DEMO_DATES:
        compact = date_compact(day)
        expected = detail_url(day)
        rendered = ROOT / "_site" / compact / "index.html"
        if not rendered.exists():
            errors.append(f"{rendered}: 缺少 YYYYMMDD 日期页")
        legacy = ROOT / "_site" / "issues" / f"{day}.html"
        if legacy.exists():
            errors.append(f"{legacy}: 不应保留旧 /issues/ 日期页")
        for path in sorted((ROOT / "publish" / "wechat").glob(f"{day}-demo-*.txt")):
            text = read_text(path, errors)
            if expected not in text:
                errors.append(f"{path}: 未使用当天 brief 日期页 URL")
            if COURSE_URL in text or "lianxh.cn</a>" in text:
                errors.append(f"{path}: 微信文本不得含课程入口或网页页脚")
            check_identity_text(path, text, errors)


def check_active_tree(errors: list[str]) -> None:
    roots = [
        ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "_quarto.yml",
        ROOT / "index.qmd", ROOT / "archive.qmd", ROOT / "docs", ROOT / "config",
        ROOT / "content" / "issues", ROOT / "topics", ROOT / "publish" / "wechat",
        ROOT / ".github", ROOT / "_site", ROOT / "ops-local" / "preview",
    ]
    for root in roots:
        paths = [root] if root.is_file() else root.rglob("*") if root.exists() else []
        for path in paths:
            if (path.is_dir() or path == Path(__file__).resolve() or
                    path.suffix.lower() not in {".css", ".html", ".json", ".md", ".py", ".qmd", ".txt", ".yml"}):
                continue
            check_identity_text(path, read_text(path, errors), errors)


def main() -> int:
    errors: list[str] = []
    check_config(errors)
    check_public_pages(errors)
    check_routes_and_wechat(errors)
    check_active_tree(errors)
    if errors:
        print("FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("PASS: 公开身份、日期路由、网页页脚与微信群边界均已验证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
