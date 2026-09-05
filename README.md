# 连享会 · 快讯

[访问公开网站](https://lianxhcn.github.io/brief/)

连享会 · 快讯收录适合经管研究与课程学习的公开信息，包括连享会文章、近期论文、方法与工具，以及会议和征稿信息。每期网页详版与课程群短版都来自同一份经过核验的数据源。

## 怎样浏览

- [首页](https://lianxhcn.github.io/brief/) 按日期展示已公开的快讯。
- [栏目索引](https://lianxhcn.github.io/brief/topics/) 按推文、论文、新方法和会议征稿浏览。
- [往期](https://lianxhcn.github.io/brief/archive.html) 汇总所有已公开期次。
- 每期的完整内容位于 `/issues/YYYYMMDD/`；例如：[2026 年 9 月 5 日](https://lianxhcn.github.io/brief/issues/20260905/)。

## 内容原则

只收录可公开访问、能够核验来源的材料。论文链接指向 DOI 或官方页面；工具和会议信息链接指向维护方或主办方页面。页面会说明条目的来源与抓取日期。DEMO 仅供本地流程测试，不会出现在栏目、首页或往期页面。

## 仓库说明

这个仓库保存公开网站的源码与生成结果：

- `content/issues/` 是每期的结构化数据源。
- `issues/YYYYMMDD/` 是自动生成的日期详版。
- `topics/` 是从公开期次生成的栏目页。
- `publish/wechat/` 是相同数据源生成的课程群短版。

维护者可阅读[维护说明](docs/maintainer-guide.md)，了解内容校验、本地构建和发布步骤。
