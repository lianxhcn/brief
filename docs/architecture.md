# 长期架构

canonical owner：数据流、模块与目录职责。

## 1. 数据流

```text
外部来源
    ↓
discovery / collection
    ↓
verification / normalization
    ↓
structured daily records
       ↙             ↘
website renderer    WeChat renderer
       ↓             ↓
GitHub Pages        YYYY-MM-DD.txt
```

- R-01 [HARD]：两端共享结构化事实，采用不同 renderer / formatter。禁止长期将网站截断成微信或将微信扩写成网站。事实、作者、日期、DOI、链接须一致；摘要和完整说明分别维护。
- R-02 [HARD]：保留 core / extended。core 同时进入两端，extended 只进网站。微信承担浏览、发现与导流，网站保存完整资料。

## 2. 目录职责

| 目录 | 职责 |
|---|---|
| `content/issues/` | 经审核的公开结构化期次；现存历史 DEMO 属隔离债务 |
| `issues/YYYYMMDD/` | 日期详版源码 |
| `publish/wechat/YYYY-MM-DD.txt` | 各课程群共用的一份短版 |
| `topics/` | 从结构化数据构建的栏目 |
| `config/site.json` | 运行时身份配置，服从 P-02 |
| `config/source-registry.yml` | 当前来源入口，不能当作最终白名单 |
| `scripts/` | 生成、格式化与校验实现 |
| `ops-local/` | 私有候选、核验、去重、草稿与预览；永不提交 |
| `_site/`、`.quarto/` | 构建与缓存，不作为开发真源 |
| `docs/tasks/` | 审计、债务及后续验收 |

R-03 [HARD]：两端及索引由统一数据生成，不手工维护矛盾副本。测试 fixtures 可保留，但不能进入生产，隔离服从 P-13。

R-04 [DEFAULT]：延续 Quarto + Python 标准库方案。`editorial_version: 2` 是当前实现标记，不表示新规范合规。后续 schema / formatter 迁移写明兼容与验证方案。

## 3. 当前实现状态

2026-09-05 本地源码显示已有两个 renderer、栏目生成器、台账草稿构建器及 Pages 工作流；台账构建器尚不是完整自动采集器。该状态不是线上运行保证。已知差异见 [实现债务](tasks/implementation-debt.md)。

R-05 [HARD]：公开历史集合的可发布事实保存在 `content/history/`，采用稳定成果 ID 与来源日期，可由版本控制文件重新生成；私有候选、观察和审核材料仍留在 ops-local。日常、历史、栏目共用事实和引文解析器；栏目按成果身份去重。历史补录保留来源日期、补录日期，不产生虚假的逐日快讯或微信群发送事件。已发布短版及其事实快照保存在独立 releases 证据目录，网页修订不能静默重写旧短版。

当前本地构建入口：`scripts/build_website.py` 统一验证并生成日常、历史及栏目；`--check` 检查过期文件。日常网页使用 `website_version: 3`；原短版按 `release_snapshot` 绑定证据，两个版本分开验收。Quarto pre-render 与 CI 共用此入口。

2026-09-08 分页补充：栏目由同一目录生成器按每页 10 条输出独立 QMD/HTML；往期按 U-15 每页一个完整年份，以年/月两级折叠展示。第一页保持原 URL，后续页采用同目录 `{栏目}-2.html` / `archive-2.html`；排序、去重和公开数据过滤在分页之前完成。主构建与单独目录构建共用输出清单，构建检查识别遗留分页文件。搜索覆盖完整正式内容，与当前分页无关。

公开期次名称由 site_config.issue_title(date) 统一生成。标签链接由 website_tags 统一编码，复用 Quarto 的 q 与 show-results 参数打开全站搜索，不维护第二套搜索索引。
