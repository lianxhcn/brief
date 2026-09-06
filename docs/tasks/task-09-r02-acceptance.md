# Task 09-R02 验收清单

## A. Section polish
- [x] 延伸信息上方 24–32 px 留白
- [x] 1 px 浅灰分隔线
- [x] mobile 层级正常

## B. Terminology
- [x] 无“公开详版”
- [x] 无“微信短版”
- [x] reader-facing 使用“网页版 / 微信群版”

## C. Topic pages
- [x] 新推文页无重复说明
- [x] 无“条目”
- [x] `lianxh.cn 最新推文` 可点击
- [x] `查看日期详版` 改为 `详情`
- [x] 无“查看栏目索引”
- [x] 其他 topic 同类冗余统一

## D. Promotion layout
- [x] 首页无右侧课程栏
- [x] 首页底部有课程海报
- [x] 其他正式页面有统一课程组件
- [x] desktop sidebar 约 300–340 px
- [x] sidebar 不撑开 main
- [x] mobile 不遮挡

## E. Course logic
- [x] 同一课程不同 URL 去重
- [x] `details/...` 优先
- [x] 同期最多 2–3 门
- [x] 按最近一次开课日期由近到远
- [x] 保存完整日期
- [x] 最后授课日期已过则隐藏
- [x] 日期异常不自动新增 / 更新
- [x] 抓取失败保留稳定配置
- [x] 抓取失败不使明确过期课程继续展示

## F. Shared data
- [x] 首页海报和 sidebar 共享 course entity / promotion config
- [x] 不重复维护课程事实

## G. Deferred features
- [x] 邮件订阅仍 pending
- [x] RSS 仍 pending
- [x] myAPA 保持

## H. Regression
- [x] build PASS
- [x] browser checks PASS
- [x] responsive PASS
- [x] DEMO isolation PASS
- [x] myAPA PASS
- [x] archive PASS
- [x] search PASS
- [x] 微信业务未改变
- [x] git diff --check PASS

## I. Scope
- [x] 未处理期刊白名单
- [x] 未处理论文筛选
- [x] 未处理会议评级
- [x] 未处理高级搜索 / 标签
- [x] 未做 500 条规模测试
- [x] 未 commit
- [x] 未 push
- [x] 未 publish

TASK 09-R02 RESULT: PASS

上述为本地自动验收，最终用户验收 pending。35 项单元测试；32 项浏览器检查覆盖 9 页 × 3 屏宽、3 项搜索、2 项缓存到期隐藏。逐项实现、证据和人工复核入口见 [完整报告](task-09-r02-result.md)。邮件订阅和 RSS 均为 PENDING / FUTURE。微信与原始事实保护文件哈希不变。
