#!/usr/bin/env python3
"""Build local-only reviewed drafts from an already verified candidate ledger."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from site_config import date_compact

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, value: object):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def recent_keys(state_dir: Path, today: date) -> set[str]:
    keys = set()
    for path in state_dir.glob("dedup-*.json"):
        data = load_json(path)
        for item in data.get("records", []):
            try:
                then = date.fromisoformat(item["verification_date"])
            except (KeyError, ValueError):
                continue
            if timedelta() < today - then <= timedelta(days=14):
                keys.add(item.get("dedup_key", ""))
    return keys


def check_ledger(items: list[dict]):
    required = {"id", "kind", "title", "official_url", "source_url", "source_name",
                "verification_date", "core_or_extended", "why_selected", "dedup_key", "status"}
    for item in items:
        missing = sorted(required - item.keys())
        if missing:
            raise ValueError(f"{item.get('id', '<unknown>')} 缺少字段：{', '.join(missing)}")


def daily_issue(day: str, items: list[dict]) -> dict:
    # 新台账使用 payload 保存完整条目，支持论文、软件与可选会议混排。
    from editorial_rules import check_editorial
    mapping = {"paper": "papers", "tool": "tools", "post": "lianxh_posts",
               "resource": "research_resources", "conference": "conference_calls"}
    issue = {"issue_id": f"{day}-local-draft", "date": day, "status": "draft",
             "issue_type": "daily", "editorial_version": 2,
             "title": f"连享会 · 快讯 | {day.replace('-', '.')}"}
    issue.update({category: [] for category in mapping.values()})
    for candidate in items:
        if candidate["kind"] not in mapping or not isinstance(candidate.get("payload"), dict):
            raise ValueError("新版候选台账需要受支持的 kind 和完整 payload；请勿沿用旧工具专用台账。")
        payload = dict(candidate["payload"])
        payload["priority"] = candidate["core_or_extended"]
        issue[mapping[candidate["kind"]]].append(payload)
    errors = check_editorial(issue)
    if errors:
        raise ValueError("\n".join(errors))
    return issue


def run(command: list[str]):
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.returncode:
        print(completed.stderr, file=sys.stderr, end="")
        raise RuntimeError("命令失败：" + " ".join(command))


def build_daily(day: str, ledger: list[dict], base: Path, state: Path):
    issue = daily_issue(day, ledger)
    dump_json(base / "issue.json", issue)
    dump_json(base / "candidate-ledger.json", ledger)
    page = base / "page"
    wechat = base / "wechat"
    run([sys.executable, "scripts/render_issue_pages.py", "--input", str(base / "issue.json"), "--output-dir", str(page)])
    run([sys.executable, "scripts/render_wechat.py", "--input", str(base / "issue.json"), "--output-dir", str(wechat)])
    run([sys.executable, "scripts/validate_issue.py", "--input", str(base / "issue.json"), "--history-dir", "content/issues", "--wechat-dir", str(wechat), "--issues-dir", str(page)])
    preview = ROOT / "ops-local" / "preview" / day
    preview.mkdir(parents=True, exist_ok=True)
    page_file = page / "issues" / date_compact(day) / "index.qmd"
    run(["quarto", "render", str(page_file)])
    rendered = page / "issues" / date_compact(day) / "index.html"
    if not rendered.exists():
        raise RuntimeError("Quarto 未生成本地预览。")
    shutil.move(str(rendered), preview / rendered.name)
    review = f"# 日常草稿审阅\n\n- 日期：{day}\n- core：{sum(x['core_or_extended'] == 'core' for x in ledger)}\n- extended：{sum(x['core_or_extended'] == 'extended' for x in ledger)}\n- 一份统一短版、详版与本地预览均已生成；尚未发布。\n"
    (base / "review.md").write_text(review, encoding="utf-8")
    dump_json(state / f"dedup-{day}.json", {"records": [{"dedup_key": x["dedup_key"], "verification_date": day} for x in ledger]})


def build_no_release(day: str, ledger: list[dict], base: Path):
    conference = base / "conference"
    conference.mkdir(parents=True, exist_ok=True)
    dump_json(conference / "candidate-ledger.json", ledger)
    rejected = [x for x in ledger if x["status"] != "eligible"]
    text = ["# no-release：会议信息草稿", "", f"核验日期：{day}", "", "独立会议快讯需要同日 2--3 条合格信息。本次合格数为 0，因此不生成群消息或公开页面。", "", "## 排除记录", ""]
    for item in rejected:
        text.append(f"- {item['title']}：{item['why_selected']}")
    (conference / "no-release.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="从本地候选台账生成草稿；不写公开目录。")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--mode", choices=("daily", "conference"), required=True)
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args()
    day = date.fromisoformat(args.date)
    registry = load_json(ROOT / "config/source-registry.yml")
    if not registry.get("conference_sources") or not registry.get("journal_sources"):
        raise ValueError("来源注册表不完整。")
    default_name = "daily-candidates.json" if args.mode == "daily" else "conference-candidates.json"
    ledger_path = args.ledger or ROOT / "ops-local" / "candidates" / args.date / default_name
    ledger = load_json(ledger_path)
    check_ledger(ledger)
    state = ROOT / "ops-local" / "state"
    keys = recent_keys(state, day)
    eligible = [x for x in ledger if x["status"] == "eligible" and x["dedup_key"] not in keys]
    base = ROOT / "ops-local" / "drafts" / args.date
    if args.mode == "daily":
        build_daily(args.date, eligible, base, state)
    else:
        build_no_release(args.date, ledger, base)
    print(f"WROTE local {args.mode} draft: {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
