# 阅读样式本地验收 (2026-09-08)

本轮五项反馈已实现，本地预览待用户检查；未推送。

- 首页最新期次行高从线上实测 25.5px 改为 31.875px，增加 25%。
- 两个主分区标题为 #2E7D32；分类标题采用统一细绿色竖线，不增加 Emoji。
- ssc install xtbfkbreak 与 ssc install lwdid 在日常、历史、栏目摘要中使用行内代码；安全 formatter 只解析反引号并转义 HTML。原始事实及微信纯文本不改。
- 日常和历史页首不再展示 revision_note 及开发过程说明；字段仍保留，真实来源日期不删除。
- 131 tests、完整 Quarto 渲染、生成一致性及公共搜索链接校验通过。浏览器实测行高和 RGB(46,125,50) 正确，代码元素和分类细色条存在，页首开发说明消失。

规则记录在 U-17/U-18、D-20260908-08。相关文件为 styles.css、website_content.py、render_issue_pages.py、public_history.py、build_catalog_pages.py、config/website-content.json、test_readability.py 与生成页面。
