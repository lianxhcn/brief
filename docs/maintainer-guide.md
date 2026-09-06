# 维护说明

本文件只描述维护入口与实现定位，不是第二套规则。任何操作前先读 [AGENTS](../AGENTS.md) 及全部 canonical docs。当前暂停新正式期次生成和发布，见 A-02。

## 1. 规则与实现定位

目录职责见 [architecture](architecture.md)，内容见 [content-rules](content-rules.md)，网站见 [ui-rules](ui-rules.md)，运行与审批见 [automation-rules](automation-rules.md)。

现有入口为 `scripts/render_issue_pages.py`、`scripts/render_wechat.py`、`scripts/build_catalog_pages.py`、`scripts/build_local_draft.py`。它们保留已知旧行为，不能直接作为新规范的示例。原维护命令可从 Git 基线 `b5c8a0dfe1e57adae3f01f9100a1e73847e57e6e:docs/maintainer-guide.md` 追溯，后续 Task 应在隔离测试目录验证，不盲目在生产目录重跑。

## 2. 检查与发布边界

文档任务检查 Git 状态、差异、链接和规则覆盖。业务任务先核对运行环境及输出目录，再实施范围内的最小测试。旧的编辑单测、期次校验、身份校验和导航校验仍可用于相应历史实现核对，但不证明新 canonical 合规；特别是旧公共列表检查不覆盖 DEMO 搜索索引。

`quarto render` 会执行 `scripts/build_legacy_redirects.py`，现有代码同时处理 published 和 demo，不能因能构建就视为允许发布。历史跳转处置和生产 / 测试隔离见 [债务清单](tasks/implementation-debt.md)。

运行配置 `config/site.json` 服从 P-02。任何提交、推送、部署和定时操作均按 A-04 单独授权；本次规则治理不触发它们。

## 3. Task 09 网站维护

网站 renderer 使用 `website_citations.py` 生成 myAPA。新 schema 可提供 `bibliography`；既有公开论文使用 `config/website-citations.json` 兼容映射。映射依据既有审核事实，保留完整标题与作者顺序；不可由中文导读标题猜测论文题名。缺少元数据时失败，禁止回退成伪造引文。PDF 只有带公开访问核验记录才显示，核验日期与版本不自动刷新。

课程显示由 `config/promotions.json` 和 `website_promotions.py` 统一生成。`approved_courses` 只展示标为 approved 且有 reviewed_date 的条目；人工复核应检查实际课程通知，不依据候选排序判断报名状态。没有确认条目时保留专题课程与综合入口。

手动候选发现：

```powershell
& $env:PYTHON_EXE scripts/discover_courses.py
```

该命令只写 `ops-local/promotion-candidates.json`，不修改公开配置。也可用 `--html` 传入已保存的来源页进行离线验证。失败返回非零，保留旧候选与公开配置。来源是 https://www.lianxh.cn/blogs/44.html；综合入口是 https://www.lianxh.cn/KC.html。未建立定时采集或自动批准。subscription 为 pending/disabled，未来方案仍需裁定。

本地检查 (先按环境说明核验解释器)：

```powershell
& $env:PYTHON_EXE -m unittest discover -s scripts -p 'test_*.py' -v
$env:QUARTO_PYTHON = $env:PYTHON_EXE
quarto render
& $env:PYTHON_EXE scripts/validate_navigation.py
& $env:PYTHON_EXE scripts/validate_site_identity.py
& $env:PYTHON_EXE scripts/check_responsive.py
```

Quarto 构建后自动执行旧日期跳转和 `validate_website.py`；后者只检查、不删改索引。DEMO 页使用 `search: false`、`sitemap: false` 和 noindex 元数据，保留可直接检查的测试页。不要手工清理搜索 JSON。浏览器检查使用本机已有 Python Playwright 与 Chromium，仅加载本地资源，检查三种屏宽，不生成截图。

重新生成既有详版时使用 `render_issue_pages.py --input <已有 JSON> --output-dir .`；列表用 `build_catalog_pages.py`。A-02 仍禁止生成新的正式期次。源码改动留作 working-tree diff，不把 `_site`、`ops-local`、日志或缓存纳入提交。

## 4. Task 09-R01 读者正文与推广布局

`config/website-content.json` 保存读者简介，`scripts/website_content.py` 核对原始条目指纹，供详版与栏目共用。内部 `page_note`、retrieved_date、来源和 QA 证据继续保留在原 JSON；禁止从微信摘要机械复制公开正文。原数据变化时先复核简介并更新对应指纹，不能关闭检查绕过审核。

栏目显示名集中在 website_content.py 的 SECTIONS，内部 key 不变；顶部导航需与该映射一致，由回归测试核对。正式详版采用 h1/h2/h3/h4 区分期次、分区、分类和条目，原条目锚点保持。

课程卡片只展示 approved 条目的名称链接及 MM/DD 日期，最多 3 项；没有可靠日期则隐藏卡片，导航课程入口继续可用。课程日期依据官网通知人工核实，不能把候选发布日期当开课日期。当前公开卡片只含 AI-Agent 数据分析专题 10/17、10/24、10/31，证据与核验日期留在配置。订阅及公开课/招聘仍 pending。

推广源使用普通 div，避免 Quarto 自动转换 aside 导致主文档空白；宽屏把卡片移到独立 margin sidebar，窄屏回到页尾折叠区，不改变正文排版。浏览器测试会把卡片增高 500 像素，检查正文位置稳定和 TOC 不重叠。

`validate_issue.py` 本轮只更新网站 validate_page，微信校验函数保持原样。`test_website_review.py` 检查公开文案、日期、栏目和 QA 保留；post-render 的 validate_website 同时检查可见正文与搜索摘要。最新检查命令沿用上一节，日志位于 logs/task09-r01。

## Task 09-R02 课程维护 (2026-09-06)

当前网站结果见 [R02 报告](tasks/task-09-r02-result.md)。邮件订阅与 RSS 均为 PENDING / FUTURE；myAPA 保持已实现。Task 10/11 未开始，A-02 发布暂停不变。

`config/promotions.json` 是首页与侧栏唯一课程实体来源。id 合并已确认别名；links 保存可用性，详情页优先，确认不可用时才回退。一次抓取失败不改变链接或营销状态。人工审核需核实年份、完整 dates、course_start_date、course_end_date、来源和证据；end 必须等于最后一次授课日期。日期缺失、异常或同实体事实冲突会隐藏课程，配置原样保留供复核。

按中国日期筛选未结束课程，按下一次授课日期升序最多显示 3 门。组件每次生成时筛选，已构建的缓存页面也会在加载、重新显示或切回标签页时隐藏过期课程。浏览器时钟须正确；禁用 JavaScript 的旧静态页面需重新构建才能刷新。不存在定时抓取、任务计划或自动发布。

候选发现仍手动运行 `scripts/discover_courses.py`，只写本地候选；失败返回非零并保留稳定配置。候选来源文章日期不可当作开课日期。更新后按维护流程重生成现有网站页面并本地构建，不能绕过正式期次发布暂停。

首页海报采用 SVG 排版已确认课程名与日期，不是官网原版海报。更改课程事实时必须同步审核海报、使用新的唯一文件名并经本机 PicGo 上传，更新同一实体 poster；禁止复用旧海报覆盖图床对象。图片清单见 [上传记录](../figs/uploaded-images.md)。未改品牌封面。

桌面课程卡片为 320px，1280px 以下为单栏页尾折叠。Quarto 搜索为遮罩式结果，不适合再塞侧栏；其下原页面课程组件保留，结果遮罩不受干扰。

## Task 09-R03 最终收口 (当前口径)

R03 依据用户最终确认，仅增加窄屏正文折叠目录。>=1280px 保留原 Quarto 右侧目录；<1280px 将同一个 TOC 节点移至标题后、正文前的 details。首页品牌封面承担可见标题位置，目录置于封面之后。无实际 TOC 的栏目页不造空目录。默认折叠，可用鼠标、Enter、Space 操作；链接跳转后收起目录并聚焦目标标题。未复制锚点或维护另一份目录数据。

当前 SVG 是可替换 promotion asset，不是长期固定的品牌视觉规范。用户采用方案 C，认可其作为当前可用课程推广资产；以后取得正式海报，只替换 promotion asset，不重新打开首页 promotion architecture。本轮未重绘海报、修改课程数据模型或新增轮播。

栏目和期次当前信息密度及层级已获用户整体认可，本轮不作结构性扩展。“延伸信息”沿用 R02 的 28px 上方留白、1px 浅灰线和 28px 线后间距。

搜索验收分层：Task 09 本地只检查 search.json 生成、正式内容入索引、DEMO 排除、构建及脚本资产正常。本地交互不是完整线上验收，也不作为本地 BLOCKED 依据。旧 R01/R02 交互记录保留为历史局部证据，不能替代正式 Pages 验收。Task 09/10 均验收、A-02 解除条件满足且获得统一发布授权后，按 [发布后搜索清单](tasks/task-09-post-deploy-search-checklist.md) 检查真实交互；禁止为搜索测试提前发布。

R03 本地通过后仍需用户最终验收与单独 Git 授权，不自动 commit。本轮未处理 Task 10/11、选文、高级搜索、标签、邮件或 RSS。完整结果见 [R03 报告](tasks/task-09-r03-result.md)。
