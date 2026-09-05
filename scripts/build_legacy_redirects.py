"""构建旧日期 URL 的兼容跳转；只写 _site，不在源码根目录创建日期夹。"""
from __future__ import annotations

import html
import json
from pathlib import Path
from site_config import ROOT, date_compact, detail_url


def redirect_html(target: str) -> str:
    safe = html.escape(target, quote=True)
    # 保留旧条目锚点；禁用 JavaScript 时仍可通过刷新或链接进入新页面。
    return f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={safe}">
<link rel="canonical" href="{safe}">
<title>页面已迁移 · 连享会快讯</title>
<script>location.replace({json.dumps(target)} + location.search + location.hash);</script>
</head><body><p>页面已迁移，请访问 <a href="{safe}">日期详版</a>。</p></body></html>
"""


def main() -> int:
    output = (ROOT / "_site").resolve()
    if not (output / "index.html").exists():
        raise RuntimeError("请先运行 quarto render。")
    count = 0
    for source in sorted((ROOT / "content/issues").glob("*.json")):
        issue = json.loads(source.read_text(encoding="utf-8"))
        if issue.get("status") not in {"published", "demo"}:
            continue
        compact = date_compact(issue["date"])
        target = output / "issues" / compact / "index.html"
        if not target.exists():
            raise RuntimeError(f"跳转目标缺失：{target}")
        destination = output / compact / "index.html"
        if not destination.resolve().is_relative_to(output):
            raise RuntimeError("跳转路径越出构建目录。")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(redirect_html(detail_url(issue)), encoding="utf-8")
        count += 1
    print(f"Legacy date redirects: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
