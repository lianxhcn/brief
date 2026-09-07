# 项目长期规则

canonical owner：身份、状态和跨模块治理。生效日期：2026-09-05。依据：Task ALL-01、基线、迁移清单及 D-20260905-02。治理文档内路径仅供维护定位，不复制到读者页面或微信群正文。

## 1. 身份与目录

- P-01 [HARD]：项目名称为连享会 · 快讯；开发仓库为 `G:\codex_project\github_lianxh\lianxh-group-briefs`；文档目录为 `G:\codex_project\lianxh-group-briefs-docs`。本地与远程名称不同为已确认状态，不擅自改名。
- P-02 [HARD]：公开仓库 `https://github.com/lianxhcn/brief`；Pages `https://lianxhcn.github.io/brief/`；正式 issue URL contract 为 `https://lianxhcn.github.io/brief/issues/YYYYMMDD/`。日期源码统一进入 `issues/YYYYMMDD/`。
- P-03 [HARD]：`config/site.json` 为运行时公开身份配置的唯一来源；本文件定义批准的契约，配置不能改写规则。读者页面不得出现私有路径、开发目录名或旧公开身份。
- P-04 [HARD]：仅 G 盘开发仓库承担开发；外部文档为 provenance，不把 D 盘镜像当开发副本，不为统一名称修改镜像或远程。

## 2. 规则系统

- P-05 [HARD]：正式规则分属本文件及 [architecture](architecture.md)、[content-rules](content-rules.md)、[ui-rules](ui-rules.md)、[automation-rules](automation-rules.md)。[decision-log](decision-log.md) 只记变化与原因；[tasks](tasks/README.md) 记审计、任务和债务，不另设竞争规则。
- P-06 [HARD]：AGENTS → 全部 canonical docs → 当前 Task → 冲突检查 → 执行。新实质冲突必须列明规则 ID、位置、方案影响及建议，等用户裁定；先改 canonical rule 与决策日志，再继续。
- P-07 [HARD]：HARD 为已确认强制规则；DEFAULT 可在不违反 HARD 时说明调整；PENDING 不得强制实施；DEPRECATED 不得指导生产。旧 Task 不能自行恢复效力。
- P-08 [HARD]：已裁定实现不合规按债务管理；旧测试成功不是新规则验收。未获裁定覆盖的新实质冲突仍须停止。
- P-09 [HARD]：保护未提交工作、用户文件及生产历史；禁止 destructive reset、force-push、无范围删除。不沿用旧任务的 Git / 发布授权。私有资料、凭据不得公开。
- P-10 [HARD]：ALL-01 只改治理文档及必要引用，不改 renderer、validator、tests、HTML/CSS、workflow、业务数据或正式输出。
- P-11 [HARD]：顺序 ALL-01 → 09 (网站) → 10 (微信) → 11 (自动化)。暂停新正式期次按 A-02，ALL-01 PASS 不代表解除。

## 3. 数据与生产

- P-12 [HARD]：统一结构化事实数据，两端不同 renderer；保留 core / extended，extended 不进微信，详见 R-01。
- P-13 [HARD]：DEMO 与生产彻底隔离，不进入正式首页、栏目、归档、搜索索引及结果、当日正式 issue 或微信正式短版。测试材料可保留，但不作为生产内容。
- P-14 [HARD]：废弃地址、旧日期源码布局和历史 DEMO 展示不得重新引入生产。保护已发布历史；旧兼容跳转由 Task 09 在范围内处理，本次不删除。

## 4. 废弃与待定登记

| 状态 | 历史规则 | 当前去向 |
|---|---|---|
| [DEPRECATED] | `lianxhcn/lianxh-group-briefs`；`https://lianxhcn.github.io/lianxh-group-briefs/` | P-02 |
| [DEPRECATED] | `/issues/YYYY-MM-DD.html`、`/issues/YYYY-MM-DD/`、`/YYYYMMDD/` 作为新期次路由；根目录逐日增加源码 | P-02；既有兼容跳转不是新链接规范 |
| [DEPRECATED] | 四群 `general / stata-causal / r-python-ml / finance` | 一份 `YYYY-MM-DD.txt` |
| [DEPRECATED] | 整期 📰、旧 Emoji、提要前缀、本期详版、URL 上下空行及冲突旧 validator 约束 | C-10 至 C-18 |
| [DEPRECATED] | 28 行 / 1200 字符、56 行 / 2200 字符及 24 行 / 900 字符旧目标 | 当前质量、条数及紧凑格式；不另造字符上限 |
| [DEPRECATED] | 旧 Task 09 / 10 分工；尚未首发等阶段描述 | 当前基线及任务顺序 |
| [PENDING] | 具体抓取入口、现有注册表覆盖与采集稳定性、软件版本去重最终 key；来源范围与筛选政策已于 2026-09-07 确认 | content-rules C-03 / C-04；D-20260907-03 |
| [PENDING] | 第一周时刻、完整邮件订阅、公开课稳定识别方案 | automation-rules / ui-rules |

历史材料中的“唯一”“固定”“不可修改”仅描述当时阶段；不得恢复为另一套执行入口。迁移依据见 [历史审计](tasks/all-01-audit.md)。
