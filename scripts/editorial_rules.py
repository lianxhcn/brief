"""日常快讯编辑规则 v2；历史发布稿保持原格式。"""
from datetime import date
from urllib.parse import urlparse

CATEGORIES = ("lianxh_posts", "papers", "tools", "research_resources", "conference_calls")
TOP_JOURNALS = {
    "American Economic Review", "The Quarterly Journal of Economics",
    "Journal of Political Economy", "Econometrica", "The Review of Economic Studies",
}
# 仅历史兼容使用；不约束当前 v2 的行数和字符数。
LEGACY_V2_MAX_LINES = 56
LEGACY_V2_MAX_CHARS = 2200


def uses_v2(issue):
    # 新草稿自动进入新版；发布时保留 editorial_version，避免退回旧校验。
    return issue.get("issue_type") == "daily" and (
        issue.get("editorial_version") == 2 or issue.get("status") == "draft"
    )


def core_items(issue):
    return [(category, item) for category in CATEGORIES
            for item in issue.get(category, []) if item.get("priority") == "core"]


def check_editorial(issue):
    """只检验结构和已记录的证据字段，不能代替人工核验来源。"""
    if not uses_v2(issue):
        return []
    errors = []
    entries = core_items(issue)
    if not 3 <= len(entries) <= 5:
        errors.append("日常短版需要 3–5 条 core 信息，会议计入总数。")
    # C-09：论文与软件数量只作编辑参考，不设置分类配额。
    for category, item in entries:
        label = item.get("id", "<unknown>")
        fields = ["retrieved_date"]
        urls = []
        if category == "papers":
            fields += ["publication_status", "published_date", "citation"]
            urls += ["homepage_url"]
            # 无可靠 PDF 时允许省略；有 PDF 才要求版本和合法 URL。
            if item.get("pdf_url"):
                fields += ["pdf_version"]
                urls += ["pdf_url"]
            if item.get("publication_status") not in {"published", "forthcoming", "working-paper"}:
                errors.append(f"{label}: 论文发表状态不合法。")
        elif category == "tools":
            fields += ["version", "release_date"]
            urls += ["source_url"]
        for field in fields:
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{label}: 缺少 {field}。")
        for field in urls:
            value = item.get(field, "")
            parsed = urlparse(value if isinstance(value, str) else "")
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors.append(f"{label}: 缺少合法 {field}。")
        # 年月精度论文按月初比较；不把检索日当作发表日。
        for field in ("retrieved_date", "published_date", "release_date"):
            if not item.get(field):
                continue
            try:
                value = item[field]
                when = date.fromisoformat(value + "-01" if len(value) == 7 else value)
                if when > date.fromisoformat(issue["date"]):
                    errors.append(f"{label}: {field} 晚于本期日期。")
            except (TypeError, ValueError):
                errors.append(f"{label}: {field} 日期格式不合法。")
    return errors
