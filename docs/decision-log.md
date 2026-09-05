# 规则决策日志

只记录变化及原因，不复制完整规则。记录日期：2026-09-05。

## D-20260905-01：唯一 canonical 规则体系

来源：Task ALL-01、当前基线与迁移清单。确定 AGENTS 入口、五份领域 canonical docs 与本日志，当前身份、issue URL 和 ALL-01 → 09 → 10 → 11 顺序。历史包保留 provenance，不再竞争执行权。原因：避免跨对话遗忘及旧阶段要求覆盖新决策。

## D-20260905-02：用户明确裁定过渡安排

来源：ALL-01 首次 BLOCKED 后，用户在当前对话中的六项明确裁定和继续执行授权。

新 HARD 即时生效；旧 AGENTS、历史规则、renderer、validator 和测试的旧行为登记为 implementation debt / non-compliance，不重复阻塞。明确废弃整期 📰、提要前缀、本期详版、URL 上下空行、旧 Emoji / 排版和冲突 validator 约束。

用户重申新标题、摘要、CTA、空行、URL 空格、主标题短引文、网站 myAPA、DEMO 搜索隔离。ALL-01 只改治理文档和必要引用；Task 09 负责网站 / DEMO / myAPA，Task 10 负责微信实现，Task 11 负责端到端及发布前检查。

Task 09 和 Task 10 完成并验收前暂停新正式期次生成和发布，临时发布另行授权。原因：先完成治理，再迁移代码；不把历史实现当成新规范。不豁免新的实质 HARD 冲突。

影响：P-08、P-13、C-10 至 C-20、A-02 至 A-05；债务详见 tasks/implementation-debt.md。

## D-20260905-03：历史合并与文档入口迁移

依据 ALL-01 的审计授权和 D-20260905-02。content-policy、source-selection-policy 改为迁移入口；维护说明只保留实现职责；旧定时提示词明确未启用。保留未冲突的真实性、费用、构成、隐私、安全、导航要求；技术时间窗和暂行去重列 DEFAULT；最终白名单和时刻仍 PENDING。旧任务的一次性权限不升级为长期授权。

项目 myAPA 的明确缺失链接处理覆盖全局默认占位 / DOI PDF 兜底；治理路径仅作维护定位，不进入读者内容。上述为已授权迁移，无新业务授权。

当前 Task 09 / 10 未验收，A-02 继续有效。ALL-01 检查记录见 [审计](tasks/all-01-audit.md)。
