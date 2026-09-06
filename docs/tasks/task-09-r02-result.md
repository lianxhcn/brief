# Task 09-R02 执行结果

TASK 09-R02 RESULT: PASS

2026-09-06。本轮重新读取 AGENTS、六份 canonical rules、任务入口与债务、Task 09 / R01 结果、R02 三件套，并查看 review-latest-01.png。main 与 remote 符合要求，保留已有 Task 09 + R01 合法工作树；没有新的 HARD 冲突。

## 1. 修改文件

以下为相对 R02 开始时工作树的增量；本地日志和构建缓存不列入源码变更。

- `_quarto.yml`
- `archive.qmd`
- `config/promotions.json`
- `docs/decision-log.md`
- `docs/maintainer-guide.md`
- `docs/tasks/README.md`
- `docs/tasks/implementation-debt.md`
- `docs/tasks/task-09-r01-result.md`
- `docs/tasks/task-09-r02-acceptance.md`
- `docs/tasks/task-09-r02-result.md`
- `figs/raw/brief-aic-fig01-course-poster-20260906-183956.svg`
- `figs/uploaded-images.md`
- `index.qmd`
- `issues/20260904/index.qmd`
- `issues/20260905/index.qmd`
- `scripts/build_catalog_pages.py`
- `scripts/check_responsive.py`
- `scripts/test_website_final_review.py`
- `scripts/test_website_review.py`
- `scripts/website_promotions.py`
- `styles.css`
- `topics/academic-updates.qmd`
- `topics/index.qmd`
- `topics/lianxh-new.qmd`
- `topics/methods-tools.qmd`
- `topics/research-frontier.qmd`

## 2. 延伸信息分隔

CSS 实现 28px 上方留白、1px #dce3e8 浅灰线、线后 28px 间距；未插入 Markdown 分隔文本。稳定锚点和 TOC 保留，为固定导航预留 100px scroll margin。

## 3. Sidebar width

1440px 实测课程卡片 320px，正文约 800px。Quarto margin grid 为 380px，扣除内边距后容纳卡片。1280px 以下单栏，课程回到页尾折叠。增高卡片至 500px 的几何回归确认正文首块位置不变；这不是 500 条规模测试。无目录栏目负层级问题已修复，真实点击通过。

## 4. Terminology

首页使用“微信群版 / 网页版”，归档使用“网页版”；公开正文三屏宽检查无“公开详版 / 微信短版 / 查看日期详版”。历史治理文档与微信业务措辞未强行替换。

## 5. Topic cleanup

四栏目保留主标题和卡片，移除重复简介、“条目”标题及“查看栏目索引”。新推文只保留一个 lianxh.cn 最新推文外链；详情按钮保留原日期 URL 和条目锚点。标签元数据未修改。

## 6. Homepage promotion

首页取消课程右栏，底部显示可点击课程海报，原品牌 banner 保留，无轮播。官网当前正文没有独立课程海报，本轮按已核实实体排版 SVG，未添加宣传承诺。已实际查看浏览器渲染。

海报来源事实：[官网课程概览](https://www.lianxh.cn/aic.html)，retrieved_date=2026-09-06，明确为 2026-10-17、2026-10-24、2026-10-31；[详情页](https://www.lianxh.cn/details/1900.html) 正文一致。公开原始 HTML 存于本地 logs/task09-r02。

通过本机 PicGo 上传：[课程海报](https://fig-lianxh.oss-cn-shenzhen.aliyuncs.com/brief-aic-fig01-course-poster-20260906-183956.svg)。本地 SVG 在 figs/raw；[上传清单](../../figs/uploaded-images.md) 已生成，config.poster 与首页末尾 img 使用图床 URL，公开正文无本地图片路径。只上传该公开课程海报，未上传用户批注截图。

## 7. Other-page promotion

两期正式网页版、四栏目、栏目索引和归档共用 render_promotion。Quarto 搜索为遮罩，不额外放课程栏；原页面保留组件，搜索不被遮挡。

## 8. Course entity dedupe

aic.html 与 details/1900.html 归入 aic-2026，同 id 合并。事实冲突时隐藏并保持配置待复核，不能凭相似标题猜测同一课程。

## 9. Course link priority

从已确认可用链接中优先 details；详情已确认不可用时回退安全 aic 链接。抓取失败不自动改可用性；不安全协议或无可靠链接不展示。

## 10. Multi-course ordering

最多 3 门，按下一次尚未过去的授课日期升序，同日按 id 稳定排序。测试覆盖已开课但还有后续场次的课程；日期序列保留全部日期，包括最后一日。当前只有 1 门已审核有效课程，未为凑数新增课程。

## 11. Expiry behavior

保存完整 ISO 日期，start/end 必须匹配首末场次。以中国日期判断，结束日当天保留，下一日隐藏；缺日期、异常日期、无年份、无审核来源或冲突不宣称有效。首页与侧栏共用 active_courses，静态缓存加载及重新显示时也会隐藏过期课程。浏览器日期依赖设备时钟；无 JavaScript 的旧缓存需重新构建。

## 12. Fetch-failure behavior

手动候选发现返回 FAILURE，既有候选和公开配置不清空、不覆盖。测试模拟断网并逐字节核对稳定配置，随后按已存日期确认过期课程仍被隐藏。未新增定时抓取或自动营销状态。

## 13. Subscription / RSS / myAPA

邮件订阅：PENDING / FUTURE。RSS：PENDING / FUTURE。myAPA：已实现并保持回归 PASS。无邮箱收集、第三方服务或新订阅系统。

## 14. Tests

35 单元测试 PASS (原有 26 + R02 9)；32 浏览器检查 PASS。身份、导航、公共正文卫生、内部链接以及四份现有正式 / DEMO 期次校验 PASS。早期测试定位发现并修复侧栏宽度、负层级及中屏溢出；测试选择器兼容 Quarto 自动锚点与 URL 尾斜线。首次单期命令误用 09-04 文件名及 issues-dir 参数后已纠正，并重跑四期通过。

## 15. Build

quarto render PASS：11 页、4 个旧日期跳转；post-render validate_website PASS。只重生成已有两期网站页面，未生成新正式期次，未修改构建索引掩盖问题。

## 16. Responsive

1440 / 768 / 375 × 首页、两期、归档、四栏目、索引共 27 页面检查；3 项搜索与 2 项静态缓存到期检查，共 32。无横向溢出，窄屏菜单和课程折叠可点击；桌面卡片宽度、正文宽度、分隔线、层级与外链安全属性通过。实际查看桌面新推文、论文栏目、首页海报，以及中屏首页与手机期次末尾。

## 17. DEMO

公共首页 / 栏目 / 归档 / 搜索无 DEMO；三个屏宽 binsreg 有结果，DEMO 为零；直接测试 fixture 保留隔离元数据。myAPA、日期 URL 和 archive 标签保持。

## 18. 微信代码

本轮未改任何微信业务、共享 validate_issue.py、原始内容 JSON、微信输出、筛选或采集规则。保护范围哈希全部一致，详见本地 logs/task09-r02/scope-check.json。未处理用户明确排除的期刊、论文、会议、标签或规模测试事项。

## 19. Git / publish state

main；HEAD 0813a61e4140da12664c0b8ae5f60b902fa873fd；origin=https://github.com/lianxhcn/brief.git。未 stage / commit / push / publish / tag / PR / schedule。localhost:8789 仅本地预览。A-02 冻结继续，最终人工验收 pending。

## 20. Diff stat

下列是包含 Task 09 + R01 的累计 tracked diff，不含新文件；第 1 节和本地 incremental-files.json 是本轮增量。

```text
 _quarto.yml                       |  47 +++++++++++-
 archive.qmd                       |  10 ++-
 docs/decision-log.md              |  20 ++++++
 docs/maintainer-guide.md          |  55 +++++++++++++++
 docs/tasks/README.md              |   2 +-
 docs/tasks/implementation-debt.md |  28 +++++++-
 index.qmd                         |  25 ++++---
 issues/20260904/index.qmd         |  56 ++++++---------
 issues/20260905/index.qmd         |  86 +++++++++++-----------
 issues/20990101/index.qmd         |   3 +
 issues/20990102/index.qmd         |   3 +
 scripts/build_catalog_pages.py    |  54 +++++++-------
 scripts/render_issue_pages.py     | 145 +++++++++++++++-----------------------
 scripts/validate_issue.py         |  34 +++++----
 scripts/validate_navigation.py    |   2 +-
 scripts/validate_site_identity.py |   5 +-
 styles.css                        |  60 ++++++++++++++++
 topics/academic-updates.qmd       |  18 +++--
 topics/index.qmd                  |  16 +++--
 topics/lianxh-new.qmd             |  12 ++--
 topics/methods-tools.qmd          |  14 ++--
 topics/research-frontier.qmd      |  20 +++---
 22 files changed, 453 insertions(+), 262 deletions(-)

```

## 21. Diff check

git diff --check PASS；新文档相对链接和本轮保护范围另行核验。所有修改保留工作树供审阅。

## 22. 建议最终人工核查页面

- [首页](http://127.0.0.1:8789/)：底部海报、品牌 banner、网页版 / 微信群版说明。
- [9 月 5 日网页版](http://127.0.0.1:8789/issues/20260905/)：延伸信息分隔、myAPA、目录和右栏。
- [9 月 4 日网页版](http://127.0.0.1:8789/issues/20260904/)：会议截止日期与移动端长链接。
- [新推文](http://127.0.0.1:8789/topics/lianxh-new.html)：一个官网链接、详情按钮、无冗余标题。
- [新论文](http://127.0.0.1:8789/topics/research-frontier.html)、[新方法](http://127.0.0.1:8789/topics/methods-tools.html)、[会议征稿](http://127.0.0.1:8789/topics/academic-updates.html)：统一课程组件与卡片。
- [往期](http://127.0.0.1:8789/archive.html)：日期入口、课程栏。
- 从首页及非首页打开顶部搜索：binsreg 有结果、DEMO 无结果；再用 768 / 375 宽度检查菜单和课程折叠。

READY FOR FINAL TASK 09 USER REVIEW

R03 为最新本地验收口径，见 [R03 结果](task-09-r03-result.md)。本报告为历史快照；真实搜索交互转入发布后验收，不构成本地收口阻塞。
