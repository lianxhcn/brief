"""读者文案与内部 QA 分离；共享原始事实只读。"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = (
    ('lianxh-new', '新推文', 'lianxh.cn 最新推文。'),
    ('research-frontier', '新论文', '最新顶刊论文和工作论文。'),
    ('methods-tools', '新方法', '新发布的 Stata、R、Python 命令和 package。'),
    ('academic-updates', '会议征稿', '最新会议和征文信息。'),
)
DISPLAY_LABELS = {key: label for key, label, _ in SECTIONS}
CATEGORY_LABELS = dict(zip(
    ('lianxh_posts', 'papers', 'tools', 'research_resources', 'conference_calls'),
    ('新推文', '新论文', '新方法', '新方法', '会议征稿')))
INTERNAL_PHRASES = ('PUBLISHED', '核验日期', '短版依据', '本次仅核验',
                    '未安装或运行测试', '本次未复现', 'DESCRIPTION', '论文来源：')
EDITORIAL_PATTERNS = (
    r'本期不足\s*\d+\s*条',
    r'(?:补录|收录日期)[：:]',
    r'(?:本轮|本期|本次)(?:仅|只|已|完整|尚未|未|仅读)?(?:核验|核对|复核|读取|阅读|审阅|审读|检索|查询|安装|运行|实测|复现|下载|验证)',
    r'(?:本轮|本期|本次)(?:仅|只|已|完整|仅读)?(?:核|读)(?=官方|原文|正文|原摘要|摘要|\s*help|文档|手册|代码|证明)',
)


def reader_text_errors(text):
    """只拒绝明确的编务自述；研究主题中的开发、检验和局限不属此类。"""
    # Quarto 搜索可能连接两个相邻导航按钮；只恢复这个已确认的词边界。
    prose = text.replace('查看本期阅读原文', '查看本期 阅读原文')
    return ([phrase for phrase in INTERNAL_PHRASES if phrase in text]
            + [match.group(0) for pattern in EDITORIAL_PATTERNS
               for match in re.finditer(pattern, prose)])


def fingerprint(item):
    """事实变化时要求重审读者文案，防止旧简介悄悄覆盖新数据。"""
    data = json.dumps(item, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def public_summary(item):
    records = json.loads((ROOT / 'config/website-content.json').read_text(encoding='utf-8'))
    source_sha256 = fingerprint(item)
    record = records.get(item['id'])
    if isinstance(record, dict) and record.get('source_sha256') != source_sha256:
        versions = record.get('versions')
        record = versions.get(source_sha256) if isinstance(versions, dict) else None
    if not isinstance(record, dict) or record.get('source_sha256') != source_sha256:
        raise ValueError(f"{item['id']}: 读者简介缺失或原始数据已变化，请复核")
    summary = record.get('summary')
    if not isinstance(summary, str) or not summary.strip() or reader_text_errors(summary):
        raise ValueError(f"{item['id']}: 读者简介含内部核验文案或为空")
    return summary

def inline_code(text):
    """只解析反引号行内代码；其余字符一律转义，禁止原始 HTML 注入。"""
    import html
    import re
    parts = re.split(r'(`[^`\n]+`)', text)
    return ''.join('<code>' + html.escape(part[1:-1]) + '</code>'
                   if part.startswith('`') and part.endswith('`') and len(part) > 2
                   else html.escape(part) for part in parts)
