# Task 09 验收清单

历史自动验收快照。后续用户批注与最新网站状态见 [Task 09-R01 结果](task-09-r01-result.md)，本记录不表示最终人工验收。

2026-09-06：本地验收 PASS；用户人工验收 pending。各项 PASS 仅指本轮实现和自动验证，不解除发布暂停。

## A. Preflight

证据：入口与六份 canonical docs 已读取；main，初始 git status --short 为空，HEAD 为 0813a61e4140da12664c0b8ae5f60b902fa873fd。

- [x] PASS：当前目录正确
- [x] PASS：branch = main
- [x] PASS：工作树开始时干净
- [x] PASS：能确认 governance commit `0813a61e...`
- [x] PASS：已读取 AGENTS 和全部 canonical rules

## B. DEMO 隔离

证据：test_website.py、validate_website.py (post-render) 和三屏宽真实搜索。

- [x] PASS：DEMO 不在首页
- [x] PASS：DEMO 不在 archive
- [x] PASS：DEMO 不在 topics
- [x] PASS：DEMO 不在 search index
- [x] PASS：DEMO 不在其他生产公共索引
- [x] PASS：已有自动回归测试

## C. myAPA

证据：website_citations.py、test_website.py、test_website_boundaries.py；既有三篇论文输出。PDF 核验日期沿用 2026-09-05 证据。

- [x] PASS：网站详版论文使用 myAPA
- [x] PASS：完整标题保留
- [x] PASS：authors / year / source 正确
- [x] PASS：DOI → Link
- [x] PASS：PDF 仅在可靠可访问时显示
- [x] PASS：Google URL 编码正确
- [x] PASS：forthcoming 兼容
- [x] PASS：working paper 兼容
- [x] PASS：缺 volume / pages 兼容
- [x] PASS：多作者兼容
- [x] PASS：formatter 有单元测试

## D. URL 与路由

证据：四期原 validate_issue 校验及 build_legacy_redirects.py，config/site.json 未修改。

- [x] PASS：`/brief/` 保持
- [x] PASS：`/brief/issues/YYYYMMDD/` 保持
- [x] PASS：legacy redirect 保持
- [x] PASS：未恢复根目录日期源码
- [x] PASS：现有 2026-09-04 / 2026-09-05 可以构建

## E. 首页 / 导航

证据：首页最新单期、四个快捷入口；原导航与内部 key 保持；三屏宽菜单点击。

- [x] PASS：首页信息简洁
- [x] PASS：最新期次容易进入
- [x] PASS：保留搜索
- [x] PASS：连享新文可访问
- [x] PASS：论文前沿可访问
- [x] PASS：方法工具可访问
- [x] PASS：学术动态可访问
- [x] PASS：display label 没有破坏内部 category / 历史 URL

## F. Archive

证据：archive_page 按月分组；排序及长期增长单元测试；375 像素实测。

- [x] PASS：最新日期在前
- [x] PASS：DEMO 不出现
- [x] PASS：可直达 issue
- [x] PASS：长期扩展不依赖无限长首页
- [x] PASS：手机端可读

## G. Search

证据：validate_website.py 检查索引文本；三屏宽 binsreg 有结果、DEMO 无结果。

- [x] PASS：搜索入口可发现
- [x] PASS：正式条目可搜到
- [x] PASS：DEMO 搜不到
- [x] PASS：结果文字干净
- [x] PASS：手机端无溢出
- [x] PASS：未引入外部 SaaS / credential

## H. Subscription boundary

证据：promotions.json subscription=pending/disabled；无订阅 UI、表单或外部服务。

- [x] PASS：没有假订阅按钮
- [x] PASS：没有邮箱收集
- [x] PASS：没有账号系统
- [x] PASS：没有第三方 newsletter
- [x] PASS：如存在 UI，符合 canonical ui-rules
- [x] PASS：未确定技术方案的部分保持 pending

## I. Promotion

证据：配置 renderer、公开来源离线解析成功 (10 条候选)、失败保持测试；浏览器课程折叠与展开。

- [x] PASS：推广配置驱动
- [x] PASS：`blogs/44.html` 用于课程候选来源
- [x] PASS：`KC.html` 保留综合课程入口职责
- [x] PASS：没有把近期条目自动宣称为“正在报名”
- [x] PASS：parser 失败有安全降级
- [x] PASS：公开课 / 助教招聘不强行展示
- [x] PASS：桌面端不遮挡正文
- [x] PASS：移动端不机械复制桌面浮窗
- [x] PASS：无横向溢出
- [x] PASS：未创建定时任务

## J. 微信边界

证据：content/issues、publish/wechat、微信脚本与 validator 的 git diff 均为空。

- [x] PASS：未修改微信短版业务格式
- [x] PASS：未发布新的 `publish/wechat` 正式期次
- [x] PASS：未处理 Task 10 专属规则

## K. Tests / Build

证据：20 单元测试；Quarto 11 页构建；网站/身份/导航/历史校验；18 浏览器检查；diff --check。

- [x] PASS：unit tests PASS
- [x] PASS：existing tests PASS
- [x] PASS：build PASS
- [x] PASS：link / public index checks PASS
- [x] PASS：responsive checks PASS
- [x] PASS：`git diff --check` PASS

## L. Git / Release

证据：HEAD 与初始一致、暂存 diff 为空；未使用提交、推送、发布或定时工具；产物 ignored。

- [x] PASS：未 commit
- [x] PASS：未 push
- [x] PASS：未发布
- [x] PASS：未创建 tag / release / PR / branch
- [x] PASS：Task 09 diff 可单独审阅
- [x] PASS：`_site` 等产物未进入 Git diff

## M. 文档

证据：implementation-debt.md 记录 I-09 resolved(local)，用户验收 pending；I-10/I-11 保持 open。

- [x] PASS：implementation debt 已更新
- [x] PASS：Task 09 已解决项有状态
- [x] PASS：Task 10 / Task 11 未解决项未误标 completed
- [x] PASS：新发现问题已记录而非越界处理
