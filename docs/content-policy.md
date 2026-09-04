# 内容规则

## 数据源、短版与详版

每期以 `content/issues/` 中的 JSON 为唯一公开数据源。`core` 条目必须有 `wechat_summary` 与 `page_note`；`extended` 条目只需 `page_note`，且不能渲染到微信群文本。日常期次有 3--5 条 `core`、至多 5 条 `extended`、总计不超过 10 条；最近 14 天内不得重复 DOI、标题或工具。

网页详版由脚本生成到 `YYYYMMDD/`，公开 URL 使用 `https://lianxhcn.github.io/brief/YYYYMMDD/`。群消息只能链接当天详版，不能添加首页、连享会官网或课程入口。

## 事实与受众边界

`general`、`stata-causal`、`r-python-ml`、`finance` 四个版本可以调整读者提示，不能改变标题、引文、DOI、URL 或日期详版链接。工具只限 Stata、R、Python 生态中直接服务因果推断、机器学习或实证研究的内容。论文应有完整引文与 DOI；可用时加入官方复现链接。

## 会议信息增刊

`conference-bulletin` 只用于 2--3 条会议信息的独立增刊，生成一份群组共用文本。每条必须说明名称、主题或范围、截止日期、主办方或期刊与官方 URL；网页再提供 `page_note`。

## 排版与公开性

日常标题使用“连享会快讯 | YYYY.MM.DD”，会议信息增刊使用“会议信息 | YYYY.MM.DD”。DEMO 必须在同一行标题中标明。不得使用小白菊或字符边框。URL 独占一行，前后各有空行；禁止 Markdown 链接、HTML 和行内 URL。课程入口仅出现在网页 Callout。

公开文件不得含 `ops-local`、私有路径、Token、密码、Cookie 或 SSH 私钥。当前轮禁止远程写操作、部署与定时任务。
