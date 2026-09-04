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
