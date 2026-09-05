# 维护说明

本文件只描述维护入口与实现定位，不是第二套规则。任何操作前先读 [AGENTS](../AGENTS.md) 及全部 canonical docs。当前暂停新正式期次生成和发布，见 A-02。

## 1. 规则与实现定位

目录职责见 [architecture](architecture.md)，内容见 [content-rules](content-rules.md)，网站见 [ui-rules](ui-rules.md)，运行与审批见 [automation-rules](automation-rules.md)。

现有入口为 `scripts/render_issue_pages.py`、`scripts/render_wechat.py`、`scripts/build_catalog_pages.py`、`scripts/build_local_draft.py`。它们保留已知旧行为，不能直接作为新规范的示例。原维护命令可从 Git 基线 `b5c8a0dfe1e57adae3f01f9100a1e73847e57e6e:docs/maintainer-guide.md` 追溯，后续 Task 应在隔离测试目录验证，不盲目在生产目录重跑。

## 2. 检查与发布边界

文档任务检查 Git 状态、差异、链接和规则覆盖。业务任务先核对运行环境及输出目录，再实施范围内的最小测试。旧的编辑单测、期次校验、身份校验和导航校验仍可用于相应历史实现核对，但不证明新 canonical 合规；特别是旧公共列表检查不覆盖 DEMO 搜索索引。

`quarto render` 会执行 `scripts/build_legacy_redirects.py`，现有代码同时处理 published 和 demo，不能因能构建就视为允许发布。历史跳转处置和生产 / 测试隔离见 [债务清单](tasks/implementation-debt.md)。

运行配置 `config/site.json` 服从 P-02。任何提交、推送、部署和定时操作均按 A-04 单独授权；本次规则治理不触发它们。
