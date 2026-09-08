"""Read the single public-site configuration with only the Python standard library."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "site.json"


def load_site_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


SITE = load_site_config()


def date_compact(value: str) -> str:
    """Convert an ISO date to the public YYYYMMDD route component."""
    return date.fromisoformat(value).strftime("%Y%m%d")


def detail_url(value: str | dict) -> str:
    issue_date = value["date"] if isinstance(value, dict) else value
    route = SITE["detail_url_pattern"].format(date_compact=date_compact(issue_date))
    return SITE["public_base_url"].rstrip("/") + route


def is_demo_issue(issue: dict) -> bool:
    """Return whether an issue is local-only DEMO input.

    The year guard prevents an accidentally relabeled fixture from entering a
    public index. Keep this rule here so page builders and validators share
    one definition instead of duplicating date checks.
    """
    return issue.get("status") == "demo" or str(issue.get("date", "")).startswith("2099-")


def is_public_issue(issue: dict) -> bool:
    """Return whether an issue belongs in visitor-facing lists."""
    return issue.get("status") == "published" and not is_demo_issue(issue)

def issue_title(value: str | dict) -> str:
    """网站统一名称从已验证日期生成，避免读取旧数据 title。"""
    day = value['date'] if isinstance(value, dict) else value
    return '连享会 · 快讯 | ' + date.fromisoformat(day).strftime('%Y.%m.%d')
