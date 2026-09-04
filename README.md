# 连享会 · 快讯

本项目维护连享会课程群快讯的公开网页详版，以及从同一 JSON 数据源生成的微信群短版。DEMO 只验证格式和流程，不能当作真实资讯。

## 目录职责

- `content/issues/` 保存每一期 JSON 数据源。
- `YYYYMMDD/` 保存由 `scripts/render_issue_pages.py` 生成的日期详版 QMD；网页 URL 固定为 `https://lianxhcn.github.io/brief/YYYYMMDD/`。
- `publish/wechat/` 保存由 `scripts/render_wechat.py` 生成的群消息文本。
- `scripts/` 保存生成与校验脚本，均只依赖 Python 标准库。
- `topics/` 保存由期次 JSON 自动生成的栏目索引与一级栏目页；不要手工复制条目标题、URL 或日期。
- `docs/` 保存公开内容规则；`ops-local/` 仅供本地运行，始终被 Git 忽略。

## 短版与详版

日常快讯共有 3--5 条 `core` 条目，群消息仅展示它们；网页详版还可展示至多 5 条 `extended` 条目，日常总条目不超过 10 条。四个群版本为 `general`、`stata-causal`、`r-python-ml`、`finance`；它们只能调整受众提示，标题、引文、DOI、URL 与当天详版链接必须一致。`extended` 内容不能出现在群消息中。

会议信息增刊使用 `conference-bulletin`，只生成一份共用群消息，并且必须恰有 2--3 条会议信息。每天的群消息只链接对应日期详版，不加入首页或连享会官网入口。

## 网页与课程入口

首页和每个日期详版包含连享会课程入口；该入口只出现在网页，不出现在微信群文本。公开页面不应包含群名称、私有路径、`ops-local` 或任何凭据。

## 公开身份与本地边界

公开名称为「连享会 · 快讯」，未来 GitHub 仓库为 `lianxhcn/brief`，当前唯一公开方案为 GitHub Pages。实际开发目录保留历史名称，但不得作为公开仓库名、URL、标题或群内短版标识。本项目不会自行创建远程仓库、提交、推送、部署或创建定时任务。

## 本地验证

```powershell
python scripts/render_issue_pages.py --input content/issues/2099-01-01-demo.json --output-dir .
python scripts/render_wechat.py --input content/issues/2099-01-01-demo.json --output-dir publish/wechat
python scripts/build_catalog_pages.py
python scripts/validate_issue.py --input content/issues/2099-01-01-demo.json --history-dir content/issues --wechat-dir publish/wechat --issues-dir .
python scripts/validate_site_identity.py
quarto render
python scripts/validate_navigation.py
git check-ignore -v ops-local/sentinel.txt
```

## 栏目索引

顶部导航按内容类型设置为“最新快讯”“栏目索引”“历史归档”。`topics/index.qmd` 与四个一级栏目页由 `scripts/build_catalog_pages.py` 从 `content/issues/*.json` 生成；运行该命令后再执行 `quarto render`。每个公开条目的 `catalog.section` 必填，取值只能是 `lianxh-new`、`research-frontier`、`methods-tools` 或 `academic-updates`；`software`、`methods`、`fields`、`tags` 均为可为空的列表。
