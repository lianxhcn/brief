# 实现债务与后续验收

审计日期：2026-09-05。初始审计项如下；Task 09 本地处理结果见下方 2026-09-06 记录，其余仍 open / 未验收；依据 D-20260905-02，不阻塞 ALL-01，不代表实现合规，不授权立即开发或发布。

| ID | 归属 / 规则 | 本地证据 | 修复与验收 |
|---|---|---|---|
| I-09-01 | Task 09 / P-13 | _site/search.json 含 issues/20990102/index.html 与 DEMO；_quarto.yml 渲染 issues；旧校验仅覆盖公共列表 | 隔离 fixtures，正式首页、栏目、归档、搜索索引和结果无 DEMO，检查生产构建产物 |
| I-09-02 | Task 09 / C-19、C-20 | scripts/render_issue_pages.py:32 分列 DOI / 主页 / PDF，:52 直接输出 citation，未生成 myAPA / Scholar | 独立网站 formatter，完整题名、作者顺序、&、sentence case、卷期页、可靠链接和缺失省略；覆盖编码及缺失链接案例 |
| I-09-03 | Task 09 / U-01 至 U-10 | 现有导航与静态 COURSE_CALLOUT，KC 单入口，无完整发现链 | 网站结构、归档、移动端、订阅入口、配置驱动推广；blogs/44 主来源之一，不确定公开课不显示，不做完整邮件订阅 |
| I-10-01 | Task 10 / C-10 至 C-18 | render_wechat.py:38,65,66,82 的旧标题、条目、提要、尾部；:31 添加 URL 空行 | 新标题 / Emoji / 来源 / 摘要 / 主标题短引文 / URL 数量与空格 / 紧凑空行 / 唯一分割线 / CTA，一份 TXT |
| I-10-02 | Task 10 / C-10 至 C-18 | validate_issue.py:250,259,273,275,287 与 editorial_rules.py:10 的旧上限及格式；test_editorial_rules.py:27 断言旧标题 | formatter、validator、tests 同步迁移；正反例覆盖，不放宽检查掩盖问题，废弃旧行数字符限制 |
| I-10-03 | Task 10 / C-08、C-13 | 当前复用完整 citation，未实现主标题短引文格式；每日新推文检查闭环未完成 | 保留论文主标题，推文优先不被配额挤掉，无更新无占位；与 Task 11 采集证据衔接 |
| I-11-01 | Task 11 / A-01、A-03、A-08、A-11 | build_local_draft.py 消费已核验台账；deploy-pages.yml 仅推送 / 手动触发，没有完整逐期审批状态机 | 检索、核验、草稿、人工审核、授权发布闭环；失败、重复触发、断网、去重及审核证据；不自动操作微信 |
| I-11-02 | Task 11 / A-02、A-05、A-11 | 新暂停仅文档生效，旧 CI 不覆盖新规范 | 发布前检查 canonical 一致性、验收与逐期批准；不以旧测试 PASS 代替新验收 |

现有 publish/wechat/2026-09-05.txt 等历史输出保留，不为整洁重写生产历史，也不作为新格式模板。当前 DEMO 证据来自本地构建，未在本任务核查线上索引。

## 验收记录

Task 09 / 10 各项记录测试命令 / 证据文件、结果、人工复核日期与剩余问题；两项均完成并验收后按 A-02 登记解除依据。之前暂停新正式期次，临时发布另获授权。Task 11 未完成不能声称每日全自动化上线。

## Task 09 本地验收记录 (2026-09-06)

| ID | 状态 | 证据 |
|---|---|---|
| I-09-01 | resolved (local)，待用户验收 | 页面级 search/sitemap 排除；构建自动运行 validate_website.py；真实浏览器 DEMO 结果为零 |
| I-09-02 | resolved (local)，待用户验收 | website_citations.py；结构化兼容元数据与共享事实一致性检查；myAPA 单元测试 |
| I-09-03 | resolved (local)，待用户验收 | 四个首页入口、月度归档、配置推广、候选 parser；三种屏宽通过 |

完整记录见 [Task 09 结果](task-09-result.md) 和 [验收清单](task-09-acceptance.md)。
20 项单元测试和 18 项浏览器检查通过；两期真实数据及两期历史 fixture 的原校验通过。
Task 10 的 I-10-01 至 I-10-03、Task 11 的 I-11-01 至 I-11-02 保持 open。
完整订阅、公开课/招聘稳定识别、定时与端到端编排继续 pending；不属于本轮已完成能力。
用户人工验收日期：pending。A-02 暂停保持有效，未生成新正式期次，未提交或发布。

候选后续事项：共享 schema 未来可原生提供 bibliography，逐步替代网站兼容元数据；当前禁止两份事实漂移，formatter 已校验作者、题名、DOI 和 PDF 链接。PDF 的可访问性证据沿用 2026-09-05 已审核记录，不声称本轮重新精读或复现论文。

## Task 09-R01 人工批注修正 (2026-09-06)

用户在 Task 09 自动检查后提出 6 张截图批注。I-09-03 的呈现问题已按 R01 本地修正：公开状态与 QA 文案移除、栏目命名统一、目录标题调整、正文层级和独立右栏推广改善、归档日期统一。
I-09-01 搜索隔离和 I-09-02 myAPA 保持通过。状态：resolved(local)，最终人工验收仍 pending；[R01 结果](task-09-r01-result.md) 和 [R01 清单](task-09-r01-acceptance.md) 为最新网站验收证据。
底层期次与微信产物哈希未变；网站简介使用原始条目指纹绑定，数据变化后要求重新审核。完整订阅、Task 10/11 及发布暂停状态不变。

## Task 09-R02 最终页面收口 (2026-09-06)

I-09-01/02/03 保持 resolved(local)，最新实现与验收证据见 [R02 结果](task-09-r02-result.md) 和 [清单](task-09-r02-acceptance.md)。R01 是历史快照。邮件订阅 / RSS 为 PENDING / FUTURE，myAPA 已实现且回归通过。Task 10/11、选文及会议等规则均未处理。最终用户验收 pending，生产冻结保持。

## Task 09-R03 最终收口记录 (2026-09-06)

I-09-01/02/03 保持 resolved(local)，待最终用户验收。最新证据为 [R03 结果](task-09-r03-result.md) 和 [验收清单](task-09-r03-acceptance.md)。窄屏目录、SVG 可替换资产裁定和页面层级封板已落实；不扩大 Task 09 范围。

搜索本地索引及 DEMO 隔离通过；真实 Pages 交互为 post-deploy verification pending，不阻塞本地 Task 09。待 A-02 条件和统一发布授权满足后，按 [清单](task-09-post-deploy-search-checklist.md) 人工检查并登记日期。Task 10/11 保持原未验收状态；本轮没有执行其实现工作，冻结不解除。

## 2026-09-06 单次手机验收发布补充

R03 完成后，用户新增一次推送及 GitHub Pages 发布授权，按 A-02 临时例外执行，见 [D-20260906-05](../decision-log.md)。本次发布后可检查真实搜索与手机页面；此前“待 Task 09/10 验收后统一发布”的描述仍适用于一般恢复流程。此次例外不解除一般暂停，不更改 Task 10/11 状态，用户最终人工验收仍 pending。
## Task 09 用户最终验收 (2026-09-06)

用户对线上版本 f99c579 确认“网页端已经核查，没有问题”。I-09-01、I-09-02、I-09-03 更新为 resolved / user accepted，Task 09 网站侧关闭。当前状态以本记录及 [D-20260906-06](../decision-log.md) 为准；此前 pending 状态为历史快照。

保留已明确排除的未来事项：邮件订阅/RSS、公开课/招聘稳定识别等，不计为本次已实现。Task 10 的 I-10-01 至 I-10-03、Task 11 的 I-11-01 至 I-11-02 仍 open；A-02 不解除。用户未提供逐项搜索明细，证据颗粒度见 [发布后搜索清单](task-09-post-deploy-search-checklist.md)，不据此重新阻塞已确认的网站验收。


## Task 10 本地验收记录 (2026-09-07)

用户按 D-20260907-01 裁定 C-10 条件来源和防重复，解除本任务首次 BLOCKED；C-09 会议地域与动态配额规则同时落盘。未发现新的实质 HARD 冲突。

| ID | 当前状态 | 证据及边界 |
|---|---|---|
| I-10-01 | resolved / user accepted | 分类标题、结构化短引文、URL 空格和数量、紧凑条目、唯一 CTA；真实输入隔离预览通过 |
| I-10-02 | resolved / user accepted | 当前 v2 独立校验；24 种格式变异及额外边界反例；旧限制仅用于双指纹绑定的历史兼容 |
| I-10-03 | resolved / user accepted | 已有 core 新推文优先；3–5 条动态构成；会议可为 0；短引文主标题保留 |

证据见 [Task 10 报告](task-10-result.md)：52 项单元测试、网站构建、29 项本地浏览器检查和 4 份历史期次校验通过。网站 myAPA 字节级回归通过，validate_page 保持，正式事实与历史 TXT 未改。

2026-09-07 用户已明确完成人工验收并确认 PASS，Task 10 为 accepted，以上三项更新为 user accepted，依据 [D-20260907-02](../decision-log.md)。新推文 discovery、是否已推送、地域 / 重要性选稿、最终白名单和端到端发布前编排仍归 Task 11；I-11-01/02 保持 open。用户明确要求 A-02 暂不解除。Task 09 的 user accepted 记录不变，本次仅授权 Task 10 本地 checkpoint，不 push / publish。
