#!/usr/bin/env python3
"""Validate public issue JSON, generated pages, and WeChat plain text."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

VARIANTS = ("general", "stata-causal", "r-python-ml", "finance")
DAILY_CATEGORIES = ("lianxh_posts", "papers", "tools", "research_resources")
ALL_CATEGORIES = DAILY_CATEGORIES + ("conference_calls",)
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
URL_RE = re.compile(r"https?://[^\s<>()]+")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\([^\)]+\)")
FORBIDDEN_RE = re.compile(r"🌼|┏|┗")
SECRET_RE = re.compile(
    r"(?i)(?:api[_-]?key|password|secret|private[ _-]?key)\s*[:=]|"
    r"(?:ghp|github_pat)_[A-Za-z0-9_]+|(?:cookie|ssh)\s*[:=]"
)
WINDOWS_PATH_RE = re.compile(r"[A-Za-z]:[\\/](?:Users|Windows|Program Files|temp)[\\/]", re.I)
COURSE_URL = "https://www.lianxh.cn/KC.html"
COURSE_CLASS = 'class="course-hub-callout"'
COURSE_LINK_TEXT = "查看连享会课程与专题"


def read_json(path: Path, errors: list[str]) -> dict | None:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: JSON 无法读取：{exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path}: JSON 顶层必须是对象")
        return None
    return data


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_url(value: object) -> bool:
    if not nonempty(value):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and " " not in value


def item_url(item: dict, category: str) -> str | None:
    if category == "papers":
        return item.get("doi_url")
    if category == "conference_calls":
        return item.get("official_url")
    return item.get("url")


def all_items(issue: dict) -> list[tuple[str, dict]]:
    result: list[tuple[str, dict]] = []
    for category in ALL_CATEGORIES:
        values = issue.get(category, [])
        if isinstance(values, list):
            result.extend((category, value) for value in values if isinstance(value, dict))
    return result


def detail_url(issue: dict) -> str:
    return f"https://lianxhcn.github.io/lianxh-group-briefs/issues/{issue['date']}.html"


def validate_item(item: dict, category: str, source: Path, errors: list[str]) -> None:
    label = f"{source}: {category}"
    if not ID_RE.fullmatch(str(item.get("id", ""))):
        errors.append(f"{label}: id 必须是稳定的小写连字符标识")
    if item.get("priority") not in {"core", "extended"}:
        errors.append(f"{label}: priority 必须是 core 或 extended")
    for key in ("title", "page_note"):
        if not nonempty(item.get(key)):
            errors.append(f"{label}: 缺少非空 {key}")
    if item.get("priority") == "core" and not nonempty(item.get("wechat_summary")):
        errors.append(f"{label}: core 条目缺少非空 wechat_summary")
    url = item_url(item, category)
    if not valid_url(url):
        errors.append(f"{label}: 缺少合法的公开 URL")
    if category == "papers":
        if not nonempty(item.get("citation")):
            errors.append(f"{label}: 论文缺少 citation")
        if not isinstance(item.get("doi_url"), str) or not re.fullmatch(r"https://doi\.org/\S+", item["doi_url"]):
            errors.append(f"{label}: doi_url 必须是 https://doi.org/ URL")
        if item.get("replication_url") and not valid_url(item["replication_url"]):
            errors.append(f"{label}: replication_url 格式不合法")
    if category == "tools":
        for key in ("ecosystem", "name"):
            if not nonempty(item.get(key)):
                errors.append(f"{label}: 工具缺少 {key}")
        if item.get("ecosystem") not in {"Stata", "R", "Python"}:
            errors.append(f"{label}: tool.ecosystem 只能是 Stata、R 或 Python")
    if category == "conference_calls":
        for key in ("organizer_or_journal", "topic", "deadline", "official_url"):
            if not nonempty(item.get(key)):
                errors.append(f"{label}: 会议信息缺少 {key}")
        try:
            date.fromisoformat(item.get("deadline", ""))
        except ValueError:
            errors.append(f"{label}: deadline 必须为 YYYY-MM-DD")


def validate_schema(issue: dict, source: Path, errors: list[str]) -> None:
    required = ("issue_id", "date", "status", "issue_type", "title", "lianxh_posts", "papers", "tools")
    for key in required:
        if key not in issue:
            errors.append(f"{source}: 缺少字段 {key}")
    if not ID_RE.fullmatch(str(issue.get("issue_id", ""))):
        errors.append(f"{source}: issue_id 必须为小写连字符标识")
    try:
        date.fromisoformat(issue.get("date", ""))
    except ValueError:
        errors.append(f"{source}: date 必须为 YYYY-MM-DD")
    if issue.get("status") not in {"demo", "draft", "published"}:
        errors.append(f"{source}: status 必须是 demo、draft 或 published")
    if issue.get("issue_type") not in {"daily", "conference-bulletin"}:
        errors.append(f"{source}: issue_type 必须是 daily 或 conference-bulletin")
    for category in ALL_CATEGORIES:
        if category in issue and not isinstance(issue[category], list):
            errors.append(f"{source}: {category} 必须是数组")
    ids: list[str] = []
    for category, item in all_items(issue):
        ids.append(str(item.get("id", "")))
        validate_item(item, category, source, errors)
    if len(ids) != len(set(ids)):
        errors.append(f"{source}: 条目 id 不能重复")
    if issue.get("issue_type") == "daily":
        entries = [(category, item) for category, item in all_items(issue) if category != "conference_calls"]
        core = sum(item.get("priority") == "core" for _, item in entries)
        extended = sum(item.get("priority") == "extended" for _, item in entries)
        if not 3 <= core <= 5:
            errors.append(f"{source}: 日常期次 core 条目必须为 3--5 条，当前 {core} 条")
        if extended > 5:
            errors.append(f"{source}: 日常期次 extended 条目最多 5 条，当前 {extended} 条")
        if len(entries) > 10:
            errors.append(f"{source}: 日常期次总条目最多 10 条，当前 {len(entries)} 条")
    elif issue.get("issue_type") == "conference-bulletin":
        calls = issue.get("conference_calls", [])
        if not 2 <= len(calls) <= 3:
            errors.append(f"{source}: 会议信息增刊必须恰有 2--3 条，当前 {len(calls)} 条，不应发布")
        other = sum(len(issue.get(category, [])) for category in DAILY_CATEGORIES)
        if other:
            errors.append(f"{source}: 会议信息增刊不得混入日常内容条目")


def titles(issue: dict) -> set[str]:
    return {item["title"].strip().casefold() for _, item in all_items(issue) if nonempty(item.get("title"))}


def tool_names(issue: dict) -> set[str]:
    return {item["name"].strip().casefold() for category, item in all_items(issue) if category == "tools" and nonempty(item.get("name"))}


def dois(issue: dict) -> set[str]:
    return {item["doi_url"].casefold() for category, item in all_items(issue) if category == "papers" and nonempty(item.get("doi_url"))}


def validate_history(issue: dict, source: Path, history_dir: Path, errors: list[str]) -> None:
    try:
        current_date = date.fromisoformat(issue["date"])
    except (KeyError, ValueError):
        return
    for path in history_dir.glob("*.json"):
        if path.resolve() == source.resolve():
            continue
        other = read_json(path, errors)
        if other is None:
            continue
        try:
            other_date = date.fromisoformat(other["date"])
        except (KeyError, ValueError):
            continue
        if abs((current_date - other_date).days) > 14:
            continue
        for label, current, historical in (
            ("DOI", dois(issue), dois(other)),
            ("标题", titles(issue), titles(other)),
            ("工具", tool_names(issue), tool_names(other)),
        ):
            overlap = current & historical
            if overlap:
                errors.append(f"{path}: 14 天内出现相同{label}：{', '.join(sorted(overlap))}")


def core_urls(issue: dict) -> set[str]:
    urls: set[str] = set()
    for category, item in all_items(issue):
        if item.get("priority") != "core":
            continue
        url = item_url(item, category)
        if isinstance(url, str):
            urls.add(url)
        if category == "papers" and isinstance(item.get("replication_url"), str):
            urls.add(item["replication_url"])
    urls.add(detail_url(issue))
    return urls


def expected_wechat_paths(issue: dict, wechat_dir: Path) -> list[Path]:
    stem = f"{issue['date']}-{issue['status']}"
    if issue["issue_type"] == "conference-bulletin":
        return [wechat_dir / f"{stem}-conference.txt"]
    return [wechat_dir / f"{stem}-{variant}.txt" for variant in VARIANTS]


def validate_text_file(path: Path, expected_title: str, expected_urls: set[str], issue: dict, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"{path}: 缺少微信群文本")
        return
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != expected_title:
        errors.append(f"{path}: 标题格式不符合要求")
    if issue["status"] == "demo" and "DEMO" not in (lines[0] if lines else ""):
        errors.append(f"{path}: DEMO 标题未显著标明")
    if len(lines) > 28:
        errors.append(f"{path}: 共 {len(lines)} 行，超过 28 行")
    if len(text) > 1200:
        errors.append(f"{path}: 共 {len(text)} 字符，超过 1,200 字符")
    if MARKDOWN_LINK_RE.search(text) or re.search(r"<[A-Za-z][^>]*>", text):
        errors.append(f"{path}: 不得使用 Markdown 链接或 HTML")
    if FORBIDDEN_RE.search(text):
        errors.append(f"{path}: 不得出现小白菊或字符边框")
    permitted = {"🌸 新推文", "📘 近期论文", "🍀 方法与工具", "🍅 会议与征稿", "本期详版"}
    seen_urls: set[str] = set()
    for index, line in enumerate(lines):
        if line.startswith(("🌸", "📘", "🍀", "🍅")) and line not in permitted:
            errors.append(f"{path}:{index + 1}: 栏目标题不符合固定格式")
        matches = URL_RE.findall(line)
        if matches:
            seen_urls.update(matches)
            if len(matches) != 1 or line != matches[0]:
                errors.append(f"{path}:{index + 1}: URL 必须独占一行")
            if index == 0 or index == len(lines) - 1 or lines[index - 1] != "" or lines[index + 1] != "":
                errors.append(f"{path}:{index + 1}: URL 前后必须各有空行")
        elif "http://" in line or "https://" in line:
            errors.append(f"{path}:{index + 1}: URL 格式或行内排版不合法")
    if seen_urls != expected_urls:
        errors.append(f"{path}: URL 集合与 core 条目及当天详版不一致")
    extended_values = {
        value for category, item in all_items(issue) if item.get("priority") == "extended"
        for value in (item.get("title"), item_url(item, category), item.get("doi_url")) if isinstance(value, str)
    }
    if any(value in text for value in extended_values):
        errors.append(f"{path}: 不得出现 extended 条目标题、URL 或 DOI")
    if "本期详版" not in lines:
        errors.append(f"{path}: 缺少唯一的本期详版收束链接")


def validate_wechat(issue: dict, wechat_dir: Path, errors: list[str]) -> list[Path]:
    paths = expected_wechat_paths(issue, wechat_dir)
    stem = f"{issue['date']}-{issue['status']}"
    actual = sorted(wechat_dir.glob(f"{stem}-*.txt"))
    if set(actual) != set(paths):
        errors.append(f"{wechat_dir}: 对应期次文本数量或文件名不正确")
    date_text = issue["date"].replace("-", ".")
    prefix = "会议信息" if issue["issue_type"] == "conference-bulletin" else "连享会快讯"
    demo = " · DEMO" if issue["status"] == "demo" else ""
    title = f"🔹 {prefix} · {date_text}{demo} 🔹"
    urls = core_urls(issue)
    for path in paths:
        validate_text_file(path, title, urls, issue, errors)
    return paths


def validate_page(issue: dict, issues_dir: Path, errors: list[str]) -> Path:
    path = issues_dir / f"{issue['date']}.qmd"
    if not path.exists():
        errors.append(f"{path}: 缺少日期详版页面")
        return path
    text = path.read_text(encoding="utf-8")
    for value, description in (
        (COURSE_URL, "精确 KC.html URL"),
        (COURSE_CLASS, "课程入口 HTML class"),
        (COURSE_LINK_TEXT, "可见课程链接文字"),
        ("## 本期重点", "本期重点分区"),
        ("## 延伸信息", "延伸信息分区"),
        (issue["status"].upper(), "期次状态"),
    ):
        if value not in text:
            errors.append(f"{path}: 缺少{description}")
    for category, item in all_items(issue):
        if f"{{#{item.get('id')}}}" not in text:
            errors.append(f"{path}: 缺少条目稳定锚点 {item.get('id')}")
        for url in filter(None, (item_url(item, category), item.get("replication_url"))):
            if url not in text:
                errors.append(f"{path}: 未渲染数据源 URL {url}")
    return path


def validate_public_text(issue: dict, page: Path, wechat_paths: list[Path], errors: list[str]) -> None:
    paths = [page, *wechat_paths]
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if SECRET_RE.search(text):
            errors.append(f"{path}: 疑似私密信息特征")
        if WINDOWS_PATH_RE.search(text):
            errors.append(f"{path}: 含 Windows 绝对路径")
        if "ops-local" in text:
            errors.append(f"{path}: 公开页面或文本不得出现 ops-local")


def main() -> int:
    parser = argparse.ArgumentParser(description="校验期次 JSON、日期详版与微信群纯文本。")
    parser.add_argument("--input", required=True, type=Path, help="待校验的期次 JSON")
    parser.add_argument("--history-dir", required=True, type=Path, help="历史 JSON 所在目录")
    parser.add_argument("--wechat-dir", required=True, type=Path, help="微信群文本目录")
    parser.add_argument("--issues-dir", required=True, type=Path, help="日期详版 QMD 目录")
    args = parser.parse_args()
    errors: list[str] = []
    issue = read_json(args.input, errors)
    paths: list[Path] = []
    page = args.issues_dir / "missing.qmd"
    if issue is not None:
        validate_schema(issue, args.input, errors)
        if isinstance(issue.get("date"), str) and isinstance(issue.get("issue_type"), str) and isinstance(issue.get("status"), str):
            validate_history(issue, args.input, args.history_dir, errors)
            page = validate_page(issue, args.issues_dir, errors)
            paths = validate_wechat(issue, args.wechat_dir, errors)
            validate_public_text(issue, page, paths, errors)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {args.input}；日期详版与微信群文本已验证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())