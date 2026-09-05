# 内容规则

## 每期构成 (2026-09-05 起)

日常群消息为 3–5 条 core 信息，其中包含 1–2 篇近期正式发表或 forthcoming 的顶刊论文、1–2 条 Stata、R 或 Python 命令/包的新发布或更新信息。软件生态轮换，不要求每天三种软件各占一条。会议有合格信息才发，可直接作为日常期次的一条，不强制凑数。其余位置可用于 arXiv 工作论文、连享会文章或研究资源。

顶刊检索默认覆盖 AER、QJE、JPE、Econometrica、REStud；需增加经管金融领域顶刊时，先在编辑审核中确认并更新 scripts/editorial_rules.py 的白名单。软件优先近 30 天、论文优先近 90 天；较早但有价值的材料须说明实际日期并由用户审核，不得标成当天首发。不足最低构成时保留候选和缺口说明，禁止编造或以旧消息凑数发布。

## 数据与核验

每期 JSON 为短版和详版的共同来源。新日常草稿使用 editorial_version: 2，发布时保留该字段。历史 published/DEMO 未设此字段的材料保留旧格式，不追溯改写。core 必须有 wechat_summary 与 page_note；extended 只进详版，最多 5 条；日常总计最多 10 条，包含会议。执行 14 天 DOI、标题、工具名去重。

论文保存 publication_status、journal、published_date、citation、doi_url、homepage_url、pdf_url、pdf_version、retrieved_date。工作论文优先 arXiv，不能冒充正式发表；forthcoming 必须有期刊或作者明确录用证据，R&R 不算。PDF 优先合法公开全文，作者稿与期刊排版稿分别注明版本，不能把付费登录页称为已验证 PDF。

工具保存 ecosystem、name、version、release_date、url、source_url、retrieved_date。以 CRAN、PyPI、SSC/Stata Journal 或维护者正式发布记录为准。文档版本可能领先发行版；通用功能不能写成该版新增功能。没有实测时明确说明，不能保证估计正确性或性能。

## 短版排版

标题使用“📰 连享会 · 快讯 | YYYY.MM.DD”，少量符号只用于标题和条目编号。各条以“01｜论文 · 简短标题”或“02｜软件 · 简短标题”开头。论文提要与完整引文分别独占一行；随后分别给出论文主页和 PDF，并标明 PDF 版本。

URL 独占一行，上下各留空行，URL 前后保留一个半角空格；不使用 Markdown 链接、HTML 或字符边框。新版上限 56 行、2,200 字符，以容纳分行引文和两个论文链接；实际尽量精简。所有群共用一份 YYYY-MM-DD.txt，课程入口只在网页，短版以当天详版链接收束。

## 草稿与发布

试运行第一周实行人工审核后发布。检索、生成和本地校验不代表获准公开。待审文件放在不提交的 ops-local/，不得进入公开索引。用户确认本期后才允许提交、推送和部署；不自动创建定时任务。当前流程不等于已启用每日自动采集。

网页生成到 issues/YYYYMMDD/。公开内容不得含私有路径或凭据。历史 conference-bulletin 仍支持独立 2–3 条增刊；新日常期次不要求会议数量。
