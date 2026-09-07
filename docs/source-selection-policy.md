# 来源规则迁移入口

[DEPRECATED] 本文件原有筛选说明已合并到 [content-rules.md](content-rules.md) 的 C-01 至 C-09，不再独立定义来源规则。

`config/source-registry.yml` 保留为当前实现的入口表；来源范围与筛选政策已按 D-20260907-03 同步到 C-01 至 C-09；具体抓取入口、注册表覆盖和采集稳定性、软件最终去重 key 仍待技术验证，不将当前入口表视为已完整覆盖政策。历史依据可从 Git 基线 `b5c8a0dfe1e57adae3f01f9100a1e73847e57e6e:docs/source-selection-policy.md` 追溯。开始任务先读 [AGENTS.md](../AGENTS.md)。
