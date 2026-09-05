# 维护说明

本文件面向维护者，记录数据、页面生成和校验流程；面向读者的介绍见仓库根目录 [README.md](../README.md)。

## 目录职责

- `content/issues/` 保存每一期 JSON 数据源。
- `issues/YYYYMMDD/` 保存由 `scripts/render_issue_pages.py` 生成的日期详版 QMD；网页 URL 固定为 `https://lianxhcn.github.io/brief/issues/YYYYMMDD/`。
- `publish/wechat/` 保存由 `scripts/render_wechat.py` 生成的统一课程群短版。
- `scripts/` 保存生成与校验脚本，均只依赖 Python 标准库。
- `topics/` 保存由期次 JSON 自动生成的栏目索引与栏目页；不要手工复制条目标题、URL 或日期。
- `docs/` 保存公开内容规则；`ops-local/` 仅供本地运行，始终被 Git 忽略。

## 短版与详版

新版日常短版包含 3–5 条 `core`：顶刊正式发表或 forthcoming 论文 1–2 篇、Stata/R/Python 软件发布或更新 1–2 条；会议可选。工作论文优先 arXiv。论文提要与引文分行，主页与 PDF 分列。网页还可展示至多 5 条 `extended`，但日常总计最多 10 条；`extended` 不进入群消息。具体字段和排版见 [内容规则](content-policy.md)。

新期次保留 `editorial_version: 2`。`build_local_draft.py` 的新版候选台账以 `payload` 保存完整条目，支持 paper、tool、post、resource、conference 五类；旧工具专用台账需补全后再用。试运行第一周人工审核后发布。

会议信息增刊使用 `conference-bulletin`，只生成一份共用群消息，并且必须恰有 2--3 条会议信息。每天的群消息只链接对应日期详版，不加入首页或连享会官网入口。

## 网页与课程入口

首页和每个日期详版包含连享会课程入口；该入口只出现在网页，不出现在课程群短版。公开页面不应包含群名称、私有路径、`ops-local` 或任何凭据。

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

顶部导航依次为“推文、论文、新方法、会议征稿、往期、官网、课程、搜索”。`topics/index.qmd` 与四个栏目页由 `scripts/build_catalog_pages.py` 从 `content/issues/*.json` 生成；运行该命令后再执行 `quarto render`。页面构建只收录真实 `published` 期次，DEMO 仅保留为本地直接访问的渲染输入。每个公开条目的 `catalog.section` 必填，取值只能是 `lianxh-new`、`research-frontier`、`methods-tools` 或 `academic-updates`；`software`、`methods`、`fields`、`tags` 均为可为空的列表。

## 发布边界

公开身份以 `config/site.json` 为唯一来源。提交、推送、部署和定时任务都需要用户在当前任务中明确授权；发布前应只暂存已核验的文件清单。

## 旧日期链接兼容

`quarto render` 完成后会运行 `scripts/build_legacy_redirects.py`，只在 `_site/YYYYMMDD/` 生成旧网址跳转页，指向 `/issues/YYYYMMDD/`。源码根目录不再逐日新增日期文件夹。既有公开期次与 DEMO 测试地址均保留兼容入口。
