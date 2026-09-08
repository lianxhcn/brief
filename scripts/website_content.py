"""读者文案与内部 QA 分离；共享原始事实只读。"""
import hashlib
import json
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


def fingerprint(item):
    """事实变化时要求重审读者文案，防止旧简介悄悄覆盖新数据。"""
    data = json.dumps(item, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def public_summary(item):
    records = json.loads((ROOT / 'config/website-content.json').read_text(encoding='utf-8'))
    record = records.get(item['id'])
    if not record or record.get('source_sha256') != fingerprint(item):
        raise ValueError(f"{item['id']}: 读者简介缺失或原始数据已变化，请复核")
    summary = record['summary']
    if not isinstance(summary, str) or not summary.strip() or any(t in summary for t in INTERNAL_PHRASES):
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
