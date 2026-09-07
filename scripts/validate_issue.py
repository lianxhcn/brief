#!/usr/bin/env python3
"""Validate public issue JSON, generated pages, and WeChat plain text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from site_config import date_compact, detail_url, is_demo_issue
from editorial_rules import uses_v2, check_editorial, LEGACY_V2_MAX_LINES, LEGACY_V2_MAX_CHARS
from render_wechat import title_line

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
CATALOG_SECTIONS = {"lianxh-new", "research-frontier", "methods-tools", "academic-updates"}
CATEGORY_SECTIONS = {
    "lianxh_posts": {"lianxh-new"},
    "papers": {"research-frontier"},
    "tools": {"methods-tools"},
    "research_resources": {"research-frontier", "methods-tools"},
    "conference_calls": {"academic-updates"},
}


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


def validate_catalog(item: dict, category: str, source: Path, errors: list[str]) -> None:
    label = f"{source}: {category}"
    catalog = item.get("catalog")
    if not isinstance(catalog, dict):
        errors.append(f"{label}: 缺少 catalog 对象")
        return
    section = catalog.get("section")
    if section not in CATALOG_SECTIONS:
        errors.append(f"{label}: catalog.section 必须是四个稳定标识之一")
    elif section not in CATEGORY_SECTIONS[category]:
        errors.append(f"{label}: 条目类型与 catalog.section 不一致")
    for key in ("software", "methods", "fields", "tags"):
        if not isinstance(catalog.get(key), list):
            errors.append(f"{label}: catalog.{key} 必须是列表")


def validate_item(item: dict, category: str, source: Path, errors: list[str]) -> None:
    label = f"{source}: {category}"
    if not ID_RE.fullmatch(str(item.get("id", ""))):
        errors.append(f"{label}: id 必须是稳定的小写连字符标识")
    if item.get("priority") not in {"core", "extended"}:
        errors.append(f"{label}: priority 必须是 core 或 extended")
    for key in ("title", "page_note"):
        if not nonempty(item.get(key)):
            errors.append(f"{label}: 缺少非空 {key}")
    if item.get("priority") == "core" and category != "conference_calls" and not nonempty(item.get("wechat_summary")):
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
    validate_catalog(item, category, source, errors)


def validate_schema(issue: dict, source: Path, errors: list[str]) -> None:
    errors.extend(f"{source}: {error}" for error in check_editorial(issue))
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
        entries = [(category, item) for category, item in all_items(issue) if uses_v2(issue) or category != "conference_calls"]
        core = sum(item.get("priority") == "core" for _, item in entries)
        extended = sum(item.get("priority") == "extended" for _, item in entries)
        if core > 5:
            errors.append(f"{source}: 日常期次 core 条目最多 5 条，当前 {core} 条")
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
        if uses_v2(issue) and category == "papers":
            urls.update(filter(None, (item.get("homepage_url"), item.get("pdf_url"))))
            continue
        url = item_url(item, category)
        if isinstance(url, str):
            urls.add(url)
        if category == "papers" and isinstance(item.get("replication_url"), str):
            urls.add(item["replication_url"])
    urls.add(detail_url(issue))
    return urls


def expected_wechat_paths(issue: dict, wechat_dir: Path) -> list[Path]:
    return [wechat_dir / f"{issue['date']}.txt"]


def validate_legacy_text_file(path: Path, expected_title: str, expected_urls: set[str], issue: dict, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"{path}: 缺少微信群文本")
        return
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != expected_title:
        errors.append(f"{path}: 标题格式不符合要求")
    if is_demo_issue(issue) and "DEMO" not in (lines[0] if lines else ""):
        errors.append(f"{path}: DEMO 标题未显著标明")
    line_limit = LEGACY_V2_MAX_LINES if uses_v2(issue) else 28
    char_limit = LEGACY_V2_MAX_CHARS if uses_v2(issue) else 1200
    if len(lines) > line_limit:
        errors.append(f"{path}: 共 {len(lines)} 行，超过 {line_limit} 行")
    if len(text) > char_limit:
        errors.append(f"{path}: 共 {len(text)} 字符，超过 {char_limit} 字符")
    if uses_v2(issue):
        for item in issue.get("papers", []):
            if item.get("priority") == "core":
                if f"提要：{item['wechat_summary']}" not in lines or f"引文：{item['citation']}" not in lines:
                    errors.append(f"{path}: 论文提要与引文必须分别独占一行")
    if MARKDOWN_LINK_RE.search(text) or re.search(r"<[A-Za-z][^>]*>", text):
        errors.append(f"{path}: 不得使用 Markdown 链接或 HTML")
    if FORBIDDEN_RE.search(text):
        errors.append(f"{path}: 不得出现小白菊或字符边框")
    permitted = {"📌 推文", "📘 论文", "🍀 新方法", "🍅 会议征稿", "本期详版"}
    seen_urls: set[str] = set()
    for index, line in enumerate(lines):
        if line.startswith(("📌", "📘", "🍀", "🍅")) and line not in permitted:
            errors.append(f"{path}:{index + 1}: 栏目标题不符合固定格式")
        matches = URL_RE.findall(line)
        if matches:
            seen_urls.update(matches)
            if len(matches) != 1 or line != f" {matches[0]} ":
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


def validate_text_file(path: Path, expected_title: str, expected_urls: set[str], issue: dict, errors: list[str]) -> None:
    """新 v2 的结构和逐字段校验；不调用 renderer，不继承历史长度限制。"""
    from editorial_rules import core_items
    from collections import Counter
    from wechat_format import item_lines, reader_links, format_url, valid_url_line, URL_TOKEN
    if not uses_v2(issue):
        return validate_legacy_text_file(path, expected_title, expected_urls, issue, errors)
    errors.extend(f"{path}: {error}" for error in check_editorial(issue))
    if not path.exists():
        errors.append(f"{path}: 缺少微信群文本")
        return
    text = path.read_text(encoding="utf-8")
    def fail(message):
        errors.append(f"{path}: {message}")
    # CRLF 经 read_text 标准化；行尾 U+0020 不作裁剪。
    if not text.endswith("\n") or "\n\n\n" in text:
        fail("结尾换行或连续空行不合规")
    blocks = text.removesuffix("\n").split("\n\n")
    entries = core_items(issue)
    if not blocks or blocks[0] != title_line(issue):
        fail("整期标题不精确")
    if len(blocks) != len(entries) + 2:
        fail("条目数量或条内 / 条间空行不合规")
    ids = [item.get("id") for _, item in entries]
    if len(set(ids)) != len(ids):
        fail("core id 重复")
    for number, (category, item) in enumerate(entries, 1):
        try:
            expected = item_lines(category, item, number)
        except (KeyError, TypeError, ValueError) as exc:
            fail(f"条目 metadata 无法安全格式化：{exc}")
            continue
        actual = blocks[number].splitlines() if number < len(blocks) - 1 else []
        # 精确字段核对同时保证连续序号、类型、来源、摘要与引文、URL 数量及顺序。
        if actual != expected:
            fail(f"core {number:02d} 的标题、摘要、短引文、字段或 reader-facing URL 不符合输入")
        required_links = [url for _, url in reader_links(category, item)]
        actual_links = URL_TOKEN.findall("\n".join(actual))
        maximum = 2 if category == "papers" else 1
        if len(actual_links) > maximum or Counter(actual_links) != Counter(required_links):
            fail(f"core {number:02d} 的 URL 数量或允许集合不符合类型规则")
    cta = "——\n" + format_url("🌐 更多内容", detail_url(issue))
    if not blocks or blocks[-1] != cta or text.count("——") != 1 or text.count("🌐 更多内容") != 1:
        fail("分隔线 / CTA 必须唯一且本期 URL 精确")
    for phrase in ("提要：", "摘要：", "简介：", "本期详版", "今日详情", "完整内容", "查看详情", "网页版"):
        if phrase in text:
            fail(f"禁止旧格式或前缀：{phrase}")
    if MARKDOWN_LINK_RE.search(text) or re.search(r"<[/!]?[A-Za-z][^>]*>", text):
        fail("不得使用 Markdown link 或 HTML")
    for line in text.splitlines():
        if ("https://" in line or "http://" in line) and not valid_url_line(line):
            fail("URL 必须在有标签的行内，左右各恰一个 U+0020，不能紧贴标点")
    # 补充独立泄漏检查；包括扩展论文主页、PDF、复现链接及裸 DOI。
    for _, item in all_items(issue):
        if item.get("priority") != "extended":
            continue
        values = [item.get("title")]
        values += [v for k, v in item.items() if k.endswith("url") or k == "doi"]
        if item.get("doi_url"):
            values.append(item["doi_url"].removeprefix("https://doi.org/"))
        if any(isinstance(v, str) and v and v in text for v in values):
            fail("extended 标题、URL 或 DOI 泄漏")
    # 已核验课程 URL 来自同一公开配置，不根据标题猜测课程实体。
    promotions = json.loads((Path(__file__).resolve().parents[1] / "config/promotions.json").read_text(encoding="utf-8"))
    course_urls = {COURSE_URL, promotions.get("course_source"), promotions.get("course_hub")}
    for course in promotions.get("approved_courses", []):
        course_urls.update((course.get("url"), course.get("source_url"), course.get("poster")))
        course_urls.update(link.get("url") for link in course.get("links", []))
    if any(url and url in text for url in course_urls) or re.search(r"课程推广|课程报名|报名课程|最新课程", text):
        fail("课程推广不得进入微信正文")
    # 分类图标仅允许出现在格式化标题 / CTA；不允许摘要带任意 Emoji。
    for line in text.splitlines():
        body = line.split(' ', 1)[1] if line.startswith(('📙 ', '✍️ ', '📰 ', '📦 ', '📅 ', '🌐 ')) else line
        if re.search(r"[\U0001F000-\U0001FAFF\u2600-\u27BF]", body):
            fail("非法或额外 Emoji")


# Task 09 checkpoint 51823d9 的已发布旧 v2 证据。只识别不可变历史，不能按日期猜兼容。
# 同时绑定 issue 全部事实和 TXT 内容；改动任一字节内容就必须走当前 v2 校验。
HISTORICAL_V2 = {'2026-09-05': ('ccb25691ea7d1d68e2eafe90203559066e30e1b571bd1d736ea94059ddcdc30e', '5778807f3ea86acf81dc3e8b85b71e265eddb3b38a585173f94a821b86663c11')}


def is_frozen_legacy(issue, path):
    expected = HISTORICAL_V2.get(issue.get('date'))
    if not expected or not path.is_file():
        return False
    facts = json.dumps(issue, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    text = path.read_text(encoding='utf-8').encode('utf-8')
    return (hashlib.sha256(facts).hexdigest(), hashlib.sha256(text).hexdigest()) == expected


def validate_wechat(issue: dict, wechat_dir: Path, errors: list[str], *, legacy: bool = False) -> list[Path]:
    paths = expected_wechat_paths(issue, wechat_dir)
    actual = sorted(wechat_dir.glob(f"{issue['date']}*.txt"))
    if set(actual) != set(paths):
        errors.append(f"{wechat_dir}: 对应期次文本数量或文件名不正确")
    date_text = issue["date"].replace("-", ".")
    demo = " · DEMO" if is_demo_issue(issue) else ""
    title = title_line(issue)
    urls = core_urls(issue)
    for path in paths:
        if legacy and uses_v2(issue) and not is_frozen_legacy(issue, path):
            errors.append(f"{path}: legacy 选项仅允许绑定的不可变历史，不可用于新 v2")
            continue
        if legacy or not uses_v2(issue):
            # 历史兼容是显式选择，不是当前 v2 canonical rule，也不自动降级。
            old_title = f"📰 连享会 · 快讯 | {date_text}" if uses_v2(issue) else title
            validate_legacy_text_file(path, old_title, urls, issue, errors)
        else:
            validate_text_file(path, title, urls, issue, errors)
    return paths


def validate_page(issue: dict, issues_dir: Path, errors: list[str]) -> Path:
    from site_config import is_public_issue
    from website_citations import website_citation
    from website_content import INTERNAL_PHRASES
    from website_promotions import render_promotion
    path = issues_dir / "issues" / date_compact(issue["date"]) / "index.qmd"
    if not path.exists():
        errors.append(f"{path}: 缺少日期详版页面")
        return path
    text = path.read_text(encoding="utf-8")
    public = is_public_issue(issue)
    if public:
        for phrase in INTERNAL_PHRASES:
            if phrase in text:
                errors.append(f"{path}: 公开正文含内部文案 {phrase}")
        if render_promotion() not in text:
            errors.append(f"{path}: 推广组件与配置不一致")
    for priority, heading in (("core", "本期重点"), ("extended", "延伸信息")):
        if any(i.get("priority") == priority for _, i in all_items(issue)) and f"## {heading}" not in text:
            errors.append(f"{path}: 缺少 {heading}")
    for category, item in all_items(issue):
        if f"{{#{item.get('id')}}}" not in text:
            errors.append(f"{path}: 缺少条目稳定锚点 {item.get('id')}")
        if category == "papers" and public:
            if website_citation(item) not in text:
                errors.append(f"{path}: myAPA 与已核验元数据不一致")
        else:
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
    parser.add_argument("--issues-dir", required=True, type=Path, help="日期页 QMD 根目录")
    parser.add_argument("--legacy-wechat", action="store_true", help="仅显式核查历史微信产物；不代表当前 v2 合规")
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
            # 维持既有网站构建命令：仅仓库历史目录中、双指纹完全匹配的旧产物走兼容。
            historical_path = args.wechat_dir / f"{issue['date']}.txt"
            archive_dir = Path(__file__).resolve().parents[1] / "publish/wechat"
            frozen = args.wechat_dir.resolve() == archive_dir.resolve() and is_frozen_legacy(issue, historical_path)
            paths = validate_wechat(issue, args.wechat_dir, errors, legacy=args.legacy_wechat or frozen)
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
