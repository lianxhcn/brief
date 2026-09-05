# Task ALL-01 审计与质量报告

审计日期 / retrieved_date：2026-09-05。范围：本地规则治理。基线 HEAD：`b5c8a0dfe1e57adae3f01f9100a1e73847e57e6e`，分支 main，origin 为 `https://github.com/lianxhcn/brief.git`。开始工作树无改动。

## 1. 输入与审查方式

完整阅读当前包 `task-all-01-project-long-term-rules-v1/03-codex/` 的 `00-project-current-baseline.md`、`02-rule-migration-checklist.md`、`01-task-all-01-project-long-term-rules.md`，并执行用户后续六项过渡裁定。外部包只读，不修改原始记录。

读取旧 AGENTS、README、全部四份 docs、config/site.json、source-registry.yml、.gitignore、Quarto 配置、GitHub Actions 工作流、renderers、editorial_rules、test_editorial_rules、build_local_draft；检查 validate_issue、validate_site_identity、validate_navigation 与本地搜索 / 微信产物。读取 logs/quality_report.md、logs/release-20260905.md，保留原报告不覆盖。

历史审计采用目录盘点、规则关键词扫描、关键规格和结果全文 / 定位阅读；不是把所有历史正文逐字复制或全量迁移。覆盖 Task 01–08、两版 Task 04、品牌包、START-HERE、README、MANIFEST、handoff、result。扫描范围排除 temp 和私有运行台账；一次大输出被工具截断后，对关键规格及 Task 08 现行规则段补读。

## 2. 历史来源与去向

以下路径相对外部文档目录 P-01，均保留原文，仅通过本审计说明权威状态。

| 来源 | 审计结论 / 迁移 |
|---|---|
| lianxh-group-briefs-handoff-v1 / 03-codex / 00-project-spec.md、task-01-bootstrap-local-project.md | Task 01 的旧 repo / Pages、四份短版、28/1200 废弃；14 天去重、真实性、私有目录隔离保留 |
| lianxh-group-briefs-task02-handoff-v1 / 03-codex / 00-project-spec.md、02-wechat-pages-detail.md；task-02-results.md | 旧 /issues/YYYY-MM-DD.html、旧 Emoji、URL 空行和格式上限废弃；同源双端、core/extended、稳定锚点和课程不入群保留 |
| lianxh-group-briefs-task-03-handoff / 03-codex / 00-project-spec.md、01-task-03-real-draft-pipeline.md；Task-03-定制每日快讯.md | 真实来源与核验、会议费用和本地待审保留；四份输出废弃，07:15 与最终白名单不定案 |
| brief-architecture-handoff-v1 / 03-codex / 00-project-spec.md、01-task-04-finalize-brief-architecture.md | brief 身份与配置来源保留；根日期路由、四版输出废弃；一次性清理权限不迁移 |
| task-04-v2-clean-rebuild-handoff-v1 / 03-codex / 00-project-spec.md、01-task-04-v2-clean-rebuild.md | 保护已有工作、开发与镜像边界保留；旧路由与四版废弃；2 期验收是历史阶段要求 |
| task-05-v2-navigation-handoff-v1 / 03-codex / 00-project-spec.md、01-task-05-v2-navigation-taxonomy.md | 栏目 metadata、响应式与安全外链迁 U-02 至 U-05；展示 DEMO 的旧阶段做法不再有效 |
| task-06-prepublish-commit-handoff-v1 / 03-codex / 00-project-spec.md、01-task-06-prepublish-commit.md | 有范围 Git、安全资产路径保留；历史提交授权不继承，旧 URL 废弃 |
| lianxh-brief-task07-handoff-v1 / 03-codex / 00-project-spec.md、01-task-07-unify-brief-workflow.md | 一份 TXT、导航职责、生产列表无 DEMO 保留并扩至搜索；旧标题和 Emoji 废弃 |
| lianxh-brief-task08-handoff-v1 / 03-codex / 00-project-spec.md、01-task-08-first-remote-publish.md | 首轮发布授权已完成，不再次创建 repo / push；旧根日期 URL 由当前基线替代 |
| task-08-completion-and-task-09-10-handoff-20260905.md §4–6 | 保留用户确认构成、人工审核与当前发布链；技术默认值单列；旧 Task 09 / 10 分工废弃；DEMO 搜索和端到端欠缺登记债务 |
| lianxh-brief-brand-assets-handoff-v2 / 03-codex | 只审查资产路径与保护原始成果，不处理或上传图片，不把一次性像素要求重设为长期规则 |
| 仓库旧 AGENTS / content-policy / source-selection-policy / automation-draft-prompt / maintainer-guide | 合并为唯一 canonical docs；旧政策改为迁移入口，原文可从基线 Git 对象追溯 |
| .github/workflows/deploy-pages.yml、config、scripts、tests、两份旧 logs | 作为实现证据，不作为新规则权威；旧测试成功不等于新规则验收 |

## 3. 迁移清单逐组结果

| 检查组 | canonical 去向 / 结果 |
|---|---|
| 项目名称、开发 / 文档目录、repo、Pages、issue URL | P-01 至 P-04；实际 remote 与基线一致，本地异名无需改名 |
| 同源、双 renderer、core/extended、质量、14 天去重 | R-01 至 R-03、C-01、C-02 |
| 每日新推文、必须入群、优先、直链、无占位 | C-08 |
| 条数、Emoji、标题、摘要、短引文 | C-09 至 C-13 |
| URL 数量、空格、标点、无 Markdown link、空行、分割线、CTA | C-14 至 C-18 |
| 网站 myAPA 字段、DOI、可靠 PDF、Scholar 编码、缺失省略 | C-19、C-20 |
| 日期源码、浏览职责、移动端、订阅与推广 | P-02、U-01 至 U-10 |
| DEMO 不进入正式搜索 | P-13；本地 search.json 不合规登记 I-09-01 |
| 发布链、完整自动化未完成、人工审核、当日批准 | A-01 至 A-11 |
| 旧 repo / Pages / 路由、四版、旧格式、字符限制、任务编号 | project-rules 第 4 节废弃登记 |
| 最终来源、去重 key、时刻、邮件、公开课 | C-03 / C-04、A-10、U-08 / U-10，全部 PENDING |
| 禁止业务修改 | P-10；只改 Markdown 治理与引用 |

## 4. 冲突裁定与剩余债务

首次发现旧规则和实现与新 HARD 不一致，按要求返回 BLOCKED，未写文件。用户随后明确批准 D-20260905-02：新规则生效，旧行为转为债务，暂停新正式期次；本次不再把该类差异重复当作 BLOCKED。

已裁定差异包括旧标题、提要、URL 空行、CTA、旧 validator / tests、网站 myAPA 与 DEMO 搜索。不改现有实现，全部有 Task 09 / 10 / 11 去向与验收要求，见 implementation-debt。

全局 myAPA 的缺失链接占位 / DOI PDF 兜底属于默认；项目任务明确要求省略，按 C-20 执行。全局无 Emoji 的中文写作习惯不限制项目明确批准的微信分类白名单。旧“本地路径不得公开”约束读者内容和私有运行信息；任务明确要求治理文档记录开发 / 文档定位，两者分开适用。未发现仍需新裁定的实质 HARD 冲突。

## 5. 写入与保护

更新 AGENTS、README 维护入口、旧四份 docs。新建五份领域规则、decision-log、tasks/README、implementation-debt 和本报告。不复制或改动外部历史包；不覆写旧 logs/quality_report.md，当前质量证据集中在本报告。

普通 apply_patch 因 Windows 目录权限写入失败，确认目标后通过受审查的提权命令仅写授权文档；没有修改 ACL、系统环境或 Git 全局设置。Git ignore Permission denied 警告对应命令退出 0，记录后继续。

## 6. 验证记录

已执行的只读命令包括 git status --short、branch --show-current、remote -v、rev-parse HEAD、rg 文件 / 规则扫描、Get-Content、Select-String。本次未访问互联网，来源 URL 仅作为本地基线记录，未声称在线可访问性已验证；未读取凭据或私有候选台账。

最终静态验收在写入完成后进行：必要文件、规则 ID 唯一性、所有本地 Markdown 链接、暂停条款、废弃 / 待定覆盖、Git diff --check 和修改范围。实际结果见本报告后续“最终验收记录”。

未运行 renderer、validator、单测或 Quarto 构建：本次无业务代码变化，旧测试无法证明新规范，且不生成正式内容。不是将未跑业务测试记为通过。

## 7. 后续任务

Task 09：I-09-01 至 I-09-03。Task 10：I-10-01 至 I-10-03。Task 11：I-11-01 至 I-11-02。任务候选不等于已授权立即执行；A-02 继续有效。

## 8. 最终验收记录

TASK ALL-01 RESULT: PASS

此 PASS 仅表示治理任务完成，不表示生产实现合规或发布恢复。

| 验收项 | 结果与证据 |
|---|---|
| 7 个必要规则入口 / 文件及 tasks 目录 | PASS：均存在，职责由 P-05 及各文件 owner 说明 |
| 唯一 authoritative rule system | PASS：旧两份 policy 与定时提示词变为迁移入口；维护说明不再定义规则；外部历史仅 provenance |
| 启动及冲突流程 | PASS：AGENTS 写明完整必读顺序与等待裁定流程 |
| 规则状态 | PASS：HARD / DEFAULT / PENDING / DEPRECATED 显式区分；领域规则 ID 无重复 |
| 历史规则不复活 | PASS：旧身份 / 路由 / DEMO 展示 / 四版 / 格式 / 编号均有去向，旧实现登记债务 |
| 不修改业务行为 | PASS：变更仅 AGENTS.md、README.md 和 docs/*.md / docs/tasks/*.md；未暂存、提交、推送、生成或部署 |
| 后续任务可独立引用 | PASS：8 项实现债务绑定规则 ID、Task 09 / 10 / 11 及验收要求 |

本地 Markdown 链接检查：37 个，0 个失效。必要文件检查、规则 ID 重复检查、新文件尾随空白检查均通过。git diff --check 退出 0。Git 的 LF → CRLF 提示未改变规范内容，未调整全局换行设置。

### 8.1 新建 / 修改文件

修改 6 个：AGENTS.md、README.md、docs/content-policy.md、docs/source-selection-policy.md、docs/automation-draft-prompt.md、docs/maintainer-guide.md。

新建 9 个：docs/project-rules.md、docs/architecture.md、docs/content-rules.md、docs/ui-rules.md、docs/automation-rules.md、docs/decision-log.md、docs/tasks/README.md、docs/tasks/implementation-debt.md、docs/tasks/all-01-audit.md。

### 8.2 Git 差异

实际 git diff --stat (只统计已跟踪文件，不含未跟踪的新文档)：

```text
 AGENTS.md                       | 49 ++++++++++++++++++++++++++++++++---------
 README.md                       |  2 ++
 docs/automation-draft-prompt.md |  8 ++++---
 docs/content-policy.md          | 28 +++--------------------
 docs/maintainer-guide.md        | 48 +++++++---------------------------------
 docs/source-selection-policy.md | 13 +++--------
 6 files changed, 60 insertions(+), 88 deletions(-)
```

另有上述 9 个新 Markdown 文件未跟踪；未使用 git add 来制造完整 diff。实际交付共 15 个文件，业务代码变更为 0，暂存区为空。

### 8.3 仍未完成的工作

Task 09 / 10 / 11 的 8 项债务仍 open；完整来源白名单、软件版本去重 key、第一周时刻、完整邮件订阅、公开课识别仍 PENDING；无需要用户再次裁定的规则冲突。未检查外网链接、线上最新状态或修复生产实现。暂停是治理规则，尚无新的程序拦截；A-02 继续有效。
