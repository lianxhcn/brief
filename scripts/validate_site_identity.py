#!/usr/bin/env python3
"""Check public identity, routes, unified WeChat output, and DEMO isolation."""

from __future__ import annotations

import json
from pathlib import Path

from site_config import CONFIG_PATH, ROOT, SITE, date_compact, detail_url, is_demo_issue

EXPECTED_CONFIG = {
    "site_title": "连享会 · 快讯",
    "github_owner": "lianxhcn",
    "github_repository": "brief",
    "public_base_url": "https://lianxhcn.github.io/brief",
    "detail_url_pattern": "/issues/{date_compact}/",
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
LEGACY_SUFFIXES = ("-general.txt", "-stata-causal.txt", "-r-python-ml.txt", "-finance.txt")


def read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{path}: 无法读取：{exc}")
        return ""


def load_issues(errors: list[str]) -> list[dict]:
    issues: list[dict] = []
    for path in sorted((ROOT / "content" / "issues").glob("*.json")):
        try:
            issues.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: 无法读取 JSON：{exc}")
    return issues


def check_config(errors: list[str]) -> None:
    try:
        parsed = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{CONFIG_PATH}: JSON 无法解析：{exc}")
        return
    if parsed != EXPECTED_CONFIG or SITE != EXPECTED_CONFIG:
        errors.append("config/site.json 的公开身份字段不符合冻结方案")


def check_identity_text(path: Path, text: str, errors: list[str]) -> None:
    for forbidden in FORBIDDEN_IDENTITIES:
        if forbidden in text:
            errors.append(f"{path}: 残留旧公开身份 {forbidden}")


def check_public_lists(errors: list[str]) -> None:
    sources = [ROOT / "index.qmd", ROOT / "archive.qmd"]
    sources.extend(sorted((ROOT / "topics").glob("*.qmd")))
    rendered = [ROOT / "_site" / "index.html", ROOT / "_site" / "archive.html"]
    rendered.extend(sorted((ROOT / "_site" / "topics").glob("*.html")))
    for path in [*sources, *rendered]:
        text = read_text(path, errors)
        if "2099" in text or "DEMO" in text:
            errors.append(f"{path}: 公开列表暴露 DEMO 内容")


def check_pages_and_wechat(issues: list[dict], errors: list[str]) -> None:
    for issue in issues:
        day = issue.get("date")
        if not isinstance(day, str):
            continue
        compact = date_compact(day)
        page_source = ROOT / "issues" / compact / "index.qmd"
        rendered = ROOT / "_site" / "issues" / compact / "index.html"
        if is_demo_issue(issue):
            if not page_source.exists() or not rendered.exists():
                errors.append(f"{compact}: DEMO 日期页缺少本地构建产物")
        expected = detail_url(issue)
        output = ROOT / "publish" / "wechat" / f"{day}.txt"
        text = read_text(output, errors)
        if expected not in text:
            errors.append(f"{output}: 未使用当天 brief 日期页 URL")
        if COURSE_URL in text or "lianxh.cn</a>" in text:
            errors.append(f"{output}: 微信文本不得含课程入口或网页页脚")
        check_identity_text(output, text, errors)
    for path in (ROOT / "publish" / "wechat").glob("*.txt"):
        if path.name.endswith(LEGACY_SUFFIXES):
            errors.append(f"{path}: 残留旧分群输出")


def check_active_tree(errors: list[str]) -> None:
    roots = [
        ROOT / "README.md", ROOT / "_quarto.yml",
        # 治理文档含合法的废弃身份记录，不属于读者页面。
        ROOT / "index.qmd", ROOT / "archive.qmd", ROOT / "config",
        ROOT / "content" / "issues", ROOT / "topics", ROOT / "publish" / "wechat",
        ROOT / "issues", ROOT / ".github", ROOT / "_site", ROOT / "ops-local" / "preview",
    ]
    for root in roots:
        paths = [root] if root.is_file() else root.rglob("*") if root.exists() else []
        for path in paths:
            if path.is_dir() or path.suffix.lower() not in {".css", ".html", ".json", ".md", ".py", ".qmd", ".txt", ".yml"}:
                continue
            check_identity_text(path, read_text(path, errors), errors)


def main() -> int:
    errors: list[str] = []
    check_config(errors)
    issues = load_issues(errors)
    check_public_lists(errors)
    check_pages_and_wechat(issues, errors)
    check_active_tree(errors)
    if errors:
        print("FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("PASS: 公开身份、日期路由、统一短版与 DEMO 隔离均已验证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
