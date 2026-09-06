# Task 09-R03 验收清单

## 当前状态：用户人工验收通过 (2026-09-06)

用户在单次 Pages 发布后确认：“网页端已经核查，没有问题”。据此，Task 09 (含 R01/R02/R03) 网站侧人工验收通过，验收版本为 `f99c57919225f4b15d4175a28cd70e0228b0e0ae`，站点为 [连享会 · 快讯](https://lianxhcn.github.io/brief/)。此前“待用户验收”“未发布”等文字保留为相应阶段的历史快照。

用户未提供设备型号、浏览器版本或逐项操作记录，不补造这些明细。Task 10/11 仍未验收，A-02 新正式期次暂停保持。本次仅更新本地验收文档，不再次提交、推送或发布。

## A. TOC

- [x] >=1280 px 保留右侧 `本页目录`
- [x] <1280 px 隐藏右侧目录
- [x] <1280 px 正文内出现折叠 `本页目录`
- [x] 默认折叠
- [x] 可展开 / 收起
- [x] 不使用悬浮目录按钮
- [x] 目录项来自真实页面 anchors
- [x] 点击可跳转
- [x] 顶部导航不遮挡目标标题
- [x] keyboard 可操作
- [x] `aria-expanded` 正确

## B. 延伸信息

- [x] 上方 24–32 px 留白
- [x] 1 px 浅灰分隔线
- [x] 不显示 Markdown `---`
- [x] mobile 正常

## C. 首页海报

- [x] 当前 SVG 保留为临时可用 asset
- [x] 文档明确其不是长期品牌视觉规范
- [x] 后续可只替换 asset
- [x] 未新增轮播 / carousel

## D. 页面结构

- [x] 栏目页不做结构性改版
- [x] 期次页不做结构性改版
- [x] 未新增复杂卡片 / 说明区

## E. Search

- [x] 本地 search index 正常生成
- [x] 正式内容进入索引
- [x] DEMO 不进入索引
- [x] build 无搜索相关错误
- [x] 已建立 post-deploy search checklist
- [x] 本地无法完整交互不作为 BLOCKED

## F. Regression

- [x] unit tests PASS
- [x] browser checks PASS
- [x] build PASS
- [x] responsive PASS
- [x] myAPA PASS
- [x] promotion PASS
- [x] DEMO isolation PASS
- [x] 微信业务未改变
- [x] `git diff --check` PASS

## G. Scope

- [x] 未处理高级搜索
- [x] 未处理标签体系
- [x] 未处理内容筛选
- [x] 未处理 Task 10
- [x] 未处理 Task 11
- [x] 未 commit
- [x] 未 push
- [x] 未 publish

TASK 09-R03 RESULT: PASS

本地自动验收：37 单元测试、31 目录检查、29 响应式 / 推广检查及本地构建 PASS。无实际 TOC 的栏目不生成空菜单。真实搜索交互为 post-deploy pending，最终用户验收仍 pending。证据见 [完整结果](task-09-r03-result.md)。
