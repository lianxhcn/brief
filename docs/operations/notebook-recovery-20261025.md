# 笔记本恢复与日常运行入口

依据 D-20261025-01，当前工作副本为 `D:\github_lianxh\brief`。旧机器 G 盘路径与外部交接包仅为历史来源；不得在本目录再嵌套 brief。

## 运行环境

本机 Quarto 为 1.7.33。Python 使用 Codex bundled runtime 的 3.12.14；PATH 中 WindowsApps/python.exe 是应用别名，不能直接作为已验证的解释器。通过 `load_workspace_dependencies` 解析当前 Python 路径；本次私有配置在 `ops-local/environment.ps1`，每次 PowerShell 会话点入后使用 `$env:PYTHON_EXE`。配置同时设置 QUARTO_PYTHON、UTF-8 和工作区中的外部测试临时目录，不提交个人环境配置。隔离测试禁止输出到生产仓库内部，因此 TEMP/TMP 与 TASK11_TEST_ROOT 必须位于仓库之外。

## 每日接续

1. 按 AGENTS 阅读当前规则，明确北京时间目标日期，检查 Git 状态和远程最新期次，先识别已发布、活动运行及中断阶段。
2. 读取 `ops-local/editorial/state.json`，执行 `scripts/editorial_desk.py plan --date YYYY-MM-DD`。其 build 仍为 shadow，不能跳过既有来源审核或直接切换为生产闸门。
3. 复用有日期且仍有效的逐来源检查；补查过期来源，保存实际原始证据、候选和处置。旧机未迁移的候选不得声称已恢复。公开历史检查摘要只能按原日期复用，不伪造今天的原始快照。
4. 依 C-08/C-09/C-21/C-23/C-24 核验、去重和选稿，保留未采用候选。软件需覆盖 Stata/R/Python 的发现，课程发现及 `check_course_handoff.py` 须有当日结果。网站与短版分别撰写，并维护带事实指纹的 `config/website-content.json`。
5. 先在 `ops-local/runs/YYYY-MM-DD/` 保存草稿、预览及审核。通过后生成正式 JSON、TXT 和网站源；运行 `build_website.py`、当期 `validate_issue.py`、Quarto 构建、单测、身份与导航检查，目视桌面及窄屏当期页面。
6. 仅提交明确审核的文件；ops-local、_site、缓存、日志及共享目录配置均不提交。不能使用裸 `git add .`，不能用旧日期已成功部署作为当期证据。
7. 本机 Git HTTPS 尚无非交互凭据；可使用已连接的 GitHub 插件以当前 main 为父提交创建审核过的 tree/commit，再以期望旧 SHA 更新 main（不 force）。核对最新远程，出现并发变更先整合，不覆盖。
8. 等待对应提交的 Pages 成功，检查线上首页当日链接、当期正文和搜索索引；完成后保存私有 publication.json，并将同一心跳切回每日北京时间 07:15。未完成按 A-17/A-19 接续，每 15 分钟检查时不能并发启动另一轮或重复昂贵检索。
9. `scripts/copy_wechat.py` 读取私有 `ops-local/wechat-delivery.json`，逐字节核验共享 TXT。共享异常单独报告，不自动发送微信，也不因该异常反复审核已经上线的网站。

## 本次恢复边界

公开历史已用于重建 570 个候选身份和 575 个发布事件；它们是历史导入，不是重新联网核验，也不证明微信群送达。旧机未发布候选与原始证据缺失，后续逐轮重建；连续编辑的两轮真实试运行仍未在本机验收。

本地定时任务需要电脑开机并保持 Codex 桌面应用运行。每日 07:15 是开始采编的时间，不承诺精确上线分钟；关机期间无法运行。旧机恢复后须先检查其调度，避免两机重复运行。
