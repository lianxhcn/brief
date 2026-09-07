# 连享会 · 快讯：任务入口

本文件是所有 Codex 任务的启动入口。canonical docs 是正式执行依据；聊天形成的裁定须落盘，不能只留在对话中。

## 1. 项目与必读顺序

项目：连享会 · 快讯。开发仓库：`G:\codex_project\github_lianxh\lianxh-group-briefs`。文档目录：`G:\codex_project\lianxh-group-briefs-docs`。公开仓库：[lianxhcn/brief](https://github.com/lianxhcn/brief)。生产站点：[连享会 · 快讯](https://lianxhcn.github.io/brief/)。

[HARD] 每次开始 Task 前必须完整执行：

1. **Step 1**: 阅读本文件。
2. **Step 2**: 依次阅读 [project-rules](docs/project-rules.md)、[architecture](docs/architecture.md)、[content-rules](docs/content-rules.md)、[ui-rules](docs/ui-rules.md)、[automation-rules](docs/automation-rules.md)、[decision-log](docs/decision-log.md)。
3. **Step 3**: 阅读当前任务书及 [任务入口](docs/tasks/README.md)、相关实现债务。
4. **Step 4**: 核对目录、branch、remote、`git status --short` 和变更范围，识别冲突。
5. **Step 5**: 无未裁定冲突后执行，再验证并报告。不得先执行再补读规则。

## 2. 状态与冲突

[HARD] 用户已确认，必须执行。[DEFAULT] 当前推荐，可在不违反 HARD 时调整，但必须说明。[PENDING] 尚未确认，不得强制实施。[DEPRECATED] 仅供追踪，不得指导生产。

[HARD] 当前 Task、临时要求或实现与 HARD 有新的实质冲突时，停止冲突部分，列出规则 ID、文件位置、各方案影响和建议，等待裁定；确认后先更新对应 canonical rule 和 decision log，再执行。Task 不得静默覆盖规则。

D-20260905-02 已裁定的旧实现差异按 implementation debt 管理，不重复请求确认，详见 [债务清单](docs/tasks/implementation-debt.md)。新发现的实质 HARD 冲突仍须停止。

## 3. 当前发布闸门

[HARD] Task 09 和 Task 10 完成并验收前，暂停生成和发布新的正式期次；临时发布另获明确授权。ALL-01 PASS 或旧测试 PASS 均不能解除暂停。正式条款为 A-02。当前 Task 09 / 10 均已验收，但 D-20260907-02 明确要求继续冻结；须经用户后续明确裁定才可解除，验收不自动解冻。Task 11 首轮隔离结果待人工审核，I-11-01/02 仍 open；A-02 继续冻结。

## 4. 安全、Git 与测试

[HARD] 不覆盖未知未提交工作，不删除用户文件，不 destructive reset，不 force-push，不无范围清理；不把镜像当开发仓库，不为整洁重写生产历史。不读取或写入凭据，不公开私有运行资料。

[HARD] 暂存、提交、推送、远程写入、部署、定时任务需当前任务明确授权。授权后仍须列明路径，不使用裸 `git add .`。ALL-01 不含上述授权。

[HARD] 验证匹配改动：文档任务检查本地链接、规则状态、覆盖范围、`git diff --check`；业务任务先最小测试，再按任务范围验证。报告区分治理通过和实现合规。代码运行前按环境说明检查环境变量，不猜测解释器路径。

[DEFAULT] Git ownership 提示可用命令级 `-c safe.directory=G:/codex_project/github_lianxh/lianxh-group-briefs`，不修改全局配置。

当前顺序：ALL-01 → 09 → 10 → 11。旧交接包、result、旧政策入口、代码注释与测试仅是历史或实现证据，不能成为第二套规则。
