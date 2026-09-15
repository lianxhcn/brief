# 连续编辑机制本地实施记录

日期：2026-09-15。依据：D-20260915-01。状态：基础实现与历史迁移完成，生产切换处于 shadow，连续两轮真实增量验收待完成。

## 完成内容

- 正式要求写回 content-rules C-24、architecture R-07、automation-rules A-21，由 decision-log 记录授权；任务索引增加当前状态导引。
- source-registry 扩展 editorial_sources，区分来源身份、优先级、入口类型、频率和待核验状态。没有把入口登记当作已经完成覆盖。
- 新增 scripts/editorial_desk.py：migrate、plan、fetch、record、ingest、decide、audit、build。运行事件保存在 ops-local/editorial/events，state.json 可重建。命令用操作系统文件锁避免并发写入；JSON原子替换。
- 迁移真实期次、来源检查及缓存候选。旧日期、失败和未知送达保留；元数据候选仅为待核验。已发布成果不因再次导入候选变回待选。
- 旧 build_local_draft CLI 保留明确退役提示，去掉与现行授权冲突的冻结说明；既有函数继续兼容，不删除质量闸门。
- 同一 automation 已增加 plan 和记录接续要求，保留每日07:15及成功后次日再启；完整 build 替换须待两轮真实验收。

## 实际入口试读

CRAN按日期列表、PyPI更新RSS、厦门大学会议列表均已取得原始快照。CRAN发现 autoCovariateSelection、badp、resultcheck、ria.test、SteadyStateBVAR 五个更新线索，已导入待核验池。更新日期不等于软件首次发布，尚未确认版本实质变化或发布推荐资格。

PyPI RSS只提供100条近期记录，不能据此认定完整Python覆盖；还需建立定向维护项目入口。厦门大学目录混有旧年会议与培训，必须按届次、活动性质和有效日期继续筛选。现有河北高校首页入口也仅为待验证发现线索，尚不能称为稳定会议采集器。

以上仅为入口试读，不计作连续两轮真实编辑生产。rollout.json 明确保存 shadow 与待验收条件。

## 使用方式

在项目根目录使用已配置 Python：

```powershell
& $env:PYTHON_EXE scripts/editorial_desk.py plan --date 2026-09-16
& $env:PYTHON_EXE scripts/editorial_desk.py fetch --date 2026-09-16 --source software:r-cran
& $env:PYTHON_EXE scripts/editorial_desk.py ingest --input ops-local/new-candidate.json
& $env:PYTHON_EXE scripts/editorial_desk.py record --input ops-local/source-check.json
& $env:PYTHON_EXE scripts/editorial_desk.py decide --input ops-local/candidate-review.json
& $env:PYTHON_EXE scripts/editorial_desk.py audit --date 2026-09-16 --input ops-local/issue.json --review ops-local/review.json
& $env:PYTHON_EXE scripts/editorial_desk.py build --date 2026-09-16 --input ops-local/issue.json --review ops-local/review.json
```

fetch只保存证据，不自动记成功覆盖。record要求source_id、at、status、complete、window_start/end、candidate_ids、reason、evidence_path；complete=false不推进终点。ingest要求category、payload、source_id、at、evidence_path。decide要求key、at、status、reason、reviewed_by；ready必须提供完整且通过条目校验的payload。

review包含date、reviewed_by、priority_comparison列表，每项为真实候选key、decision(select/defer/exclude)、reason；全论文期次另填all_papers_reason。audit核验覆盖、候选状态、payload一致性及已发记录。当前保守拒绝已有成果再发，重要更新例外仍需人工按既有规则核验，不静默绕过。

build只生成私有草稿及短版，不自行推送。通过后继续既有整站构建、验收、限定提交、部署和线上核验；发布成功执行migrate更新事实台账。source_id、候选key及到期任务见当日editorial-plan.json，不手工猜测。

## 验收与限制

本地回归包含原有测试及跨日专项：幂等、失败保留终点、分页未完不推进、证据缺失拒绝、未来日期拒绝、跨日有效期、发表状态保护、软件生态区分、arXiv版本身份、会议改期、过期候选、视图重建和命令排他锁。网站生成一致性继续通过。

首次全套测试缺少既有 TASK11_TEST_ROOT 环境变量而报错，补齐测试环境后通过，未削弱测试。

尚待连续两轮真实增量生产验证；不宣称已实现全网自动发现、全文核验或学术质量自动判定。C-08历史债务不关闭。当前候选跨版本的模糊匹配仍需人工确认，软件更新例外未自动放行。

以上为连续编辑机制初始实施阶段的记录，当时未重发或推送。后续用户已依 D-20260915-04 授权修订并发布9月15日期次，见 daily-revision-20260915.md；原共享TXT保留，修订稿另存。Task12平台文件和图片继续保留在工作区，私有迁移资料不进入公开仓库。
