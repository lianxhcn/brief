# Task 09-R01 验收清单

2026-09-06 本地检查通过；最终 Task 09 用户验收 pending。

## A. Public issue chrome

证据：正式源码与构建正文卫生检查、浏览器 DOM：无状态块、重复日期；toc-title=本页目录。

- [x] PASS：正式 issue 无 `状态` 区块
- [x] PASS：正式 issue 无 `PUBLISHED`
- [x] PASS：日期不与主标题重复展示
- [x] PASS：TOC 不含 `状态`
- [x] PASS：TOC 标题为 `本页目录`

## B. Promotion

证据：30 项浏览器检查含独立右栏、500px 增高不改变主正文、TOC 不重叠；桌面与手机实际画面复核。

- [x] PASS：sidebar 不撑开 main content
- [x] PASS：无大块异常空白
- [x] PASS：desktop sticky 不遮挡正文
- [x] PASS：mobile 不使用遮挡式浮窗
- [x] PASS：卡片标题简洁
- [x] PASS：课程标题可点击
- [x] PASS：每项只保留课程名称 / 简称 + 日期
- [x] PASS：默认展示项数适度

## C. Labels

证据：SECTIONS 单一映射、nav/card 单元测试，四个 topic pages 浏览器检查，内部 key 未改。

- [x] PASS：顶部 `新推文`
- [x] PASS：顶部 `新论文`
- [x] PASS：顶部 `新方法`
- [x] PASS：顶部 `会议征稿`
- [x] PASS：首页四卡名称一致
- [x] PASS：topic / issue 可见栏目名无明显冲突
- [x] PASS：内部 category key 未改

## D. Homepage descriptions

证据：首页使用用户指定四条简介；实际页面与自动测试已核对。

- [x] PASS：新推文：`lianxh.cn 最新推文`
- [x] PASS：新论文：`最新顶刊论文和工作论文`
- [x] PASS：新方法：`新发布的 Stata、R、Python 命令和 package`
- [x] PASS：会议征稿：`最新会议和征文信息`

## E. Hierarchy

证据：h1/h2/h3/h4；克制边线、0.65rem/0.25rem inset；375px 画面及无溢出检查。

- [x] PASS：issue title 与 section title 明显区分
- [x] PASS：section / category / item title 明显区分
- [x] PASS：item body 层级清楚
- [x] PASS：mobile 不因缩进损失过多宽度
- [x] PASS：无大量卡片 / 重边框

## F. Paper public content

证据：原 myAPA 测试继续通过；三篇论文 reader summary，内部过程留在源 JSON。

- [x] PASS：保留 myAPA
- [x] PASS：中文介绍简洁
- [x] PASS：无 `核验日期`
- [x] PASS：无 `短版依据`
- [x] PASS：无重复 Accepted Manuscript / forthcoming 说明
- [x] PASS：myAPA 有 Link/PDF/Google 时不重复“论文来源”

## G. Software public content

证据：binsreg/DoubleML 简介保留用途版本，移除生产过程；CRAN/官方文档链接保留。

- [x] PASS：不重复生态 / 名称
- [x] PASS：无 DESCRIPTION / CRAN 内部核验过程
- [x] PASS：无 `本次仅核验`
- [x] PASS：无 `未安装或运行测试`
- [x] PASS：无 `核验日期`
- [x] PASS：保留普通读者有价值的功能与版本信息
- [x] PASS：保留权威资源链接

## H. Archive

证据：archive 单元测试断言两条统一标签；浏览器与内部链接检查。

- [x] PASS：两期标签一致
- [x] PASS：日期不重复
- [x] PASS：URL 正确
- [x] PASS：DEMO 不出现

## I. QA metadata

证据：12 个保护文件哈希一致；所有微信校验函数 AST 一致，唯一变化函数为网站 validate_page。

- [x] PASS：底层 verification / evidence 未丢失
- [x] PASS：validator 所需字段仍存在
- [x] PASS：public renderer 与 QA metadata 解耦

## J. Regression

证据：26 单元测试、30 浏览器检查、11 页构建、公共索引及历史校验通过；diff --check。

- [x] PASS：unit tests PASS
- [x] PASS：browser checks PASS
- [x] PASS：build PASS
- [x] PASS：responsive PASS
- [x] PASS：DEMO isolation PASS
- [x] PASS：myAPA PASS
- [x] PASS：git diff --check PASS

## K. Scope

证据：HEAD 保持原治理提交，未 stage/commit/push/publish；无定时任务；微信业务未改。

- [x] PASS：未修改微信业务
- [x] PASS：未创建定时任务
- [x] PASS：未 commit
- [x] PASS：未 push
- [x] PASS：未 publish
