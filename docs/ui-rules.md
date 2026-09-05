# 网站与推广长期规则

canonical owner：浏览、移动端、订阅及推广。

## 1. 浏览职责

- U-01 [HARD]：首页负责最新正式期次入口，栏目负责主题发现，归档负责日期回溯，搜索负责正式内容检索。DEMO 隔离遵守 P-13。
- U-02 [HARD]：保留搜索和移动端可用性。窄屏使用可点击的标准折叠菜单，不缩字到难读，不强制横向滚动，不依赖 hover 或空格拼接。
- U-03 [HARD]：保留 Task 07 确认的导航语义：品牌链接首页，推文、论文、新方法、会议征稿、往期，以及官网、课程、搜索。栏目索引不重复占一级导航，软件 / 方法 / 领域是叠加元数据，不复活旧群组固定栏目。
- U-04 [HARD]：内部标识为 `lianxh-new`、`research-frontier`、`methods-tools`、`academic-updates`；software / methods / fields / tags 为可空列表。外站入口新窗口打开并用 `rel="noopener noreferrer"`；每页保留链接官网的 lianxh.cn 页脚。
- U-05 [DEFAULT]：延续品牌、响应式 Quarto 和稳定条目锚点；资产兼容 /brief/ 子路径，不硬编码根路径 /assets/。具体布局由 Task 09 在规则内设计，历史像素值不升格为 HARD。

## 2. 课程与推广

- U-06 [HARD]：课程、公开课、助教招聘由网站承担，不进微信正文。长期采用“公开来源 → 自动发现 → 结构化配置 → UI renderer”，不靠每次开课手改 HTML。
- U-07 [HARD]：`https://www.lianxh.cn/blogs/44.html` 为课程自动发现主来源之一，优先识别当前课程 / 新课；`https://www.lianxh.cn/KC.html` 可作综合入口，不是唯一数据源。
- U-08 [HARD]：公开课 / 助教招聘抓取不确定时不强行展示；稳定自动识别方案为 [PENDING]。实现归 Task 09，ALL-01 不实现悬浮窗或采集。
- U-09 [DEPRECATED]：固定 KC HTML Callout 作为长期唯一课程数据方案。现有入口本次保留，不认定配置驱动已完成。

## 3. 订阅

U-10 [HARD]：暂缓完整邮件订阅。Task 09 可预留入口或扩展位置，不自行引入账户、邮件数据库、第三方邮件平台或隐私数据收集。完整邮件订阅启用时点与方案为 [PENDING]。
