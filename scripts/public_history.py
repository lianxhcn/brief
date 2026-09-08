"""公开历史事实解析；复用期次条目，避免同一论文维护两份引文。"""
from pathlib import Path
import json
from datetime import date
from trial_selection import identities
from render_issue_pages import render_item
from website_content import public_summary
from website_citations import bibliography_metadata, arxiv_pdf

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'lianxh_posts':'新推文', 'papers':'新论文', 'tools':'新命令与软件', 'conference_calls':'会议征稿'}

def collections():
    return [(p.stem, json.loads(p.read_text(encoding='utf-8')))
            for p in sorted((ROOT/'content/history').glob('*.json'))]

def resolve(row):
    if 'payload' in row: return row['payload']
    path = (ROOT/row['source_file']).resolve()
    if not path.is_relative_to((ROOT/'content/issues').resolve()): raise ValueError('历史引用越界')
    issue = json.loads(path.read_text(encoding='utf-8'))
    matches = [i for i in issue.get(row['category'], []) if i['id'] == row['item_id']]
    if len(matches) != 1: raise ValueError('历史引用缺失或不唯一：'+row['item_id'])
    return matches[0]

def validate_collection(data):
    errors, seen = [], set()
    for row in data['entries']:
        item=resolve(row); keys=identities(item)
        if keys & seen: errors.append(item['id']+': 历史集合成果重复')
        seen.update(keys)
        try:
            day=date.fromisoformat(row['source_date'])
            if not data['range_start'] <= day.isoformat() <= data['range_end']: errors.append(item['id']+': 来源日期越界')
            if date.fromisoformat(row['added_date']) < day: errors.append(item['id']+': 补录早于来源')
        except (ValueError,KeyError): errors.append(item['id']+': 来源或补录日期不明')
        if row['category'] not in LABELS: errors.append('未知历史类别')
        try:
            public_summary(item)
            if row['category']=='papers':
                m=bibliography_metadata(item)
                if arxiv_pdf(m) and item.get('pdf_url') != arxiv_pdf(m): errors.append(item['id']+': arXiv PDF 缺失')
        except ValueError as exc: errors.append(str(exc))
        if row['category']=='lianxh_posts' and not 2<=len(item.get('catalog',{}).get('tags',[]))<=3:errors.append(item['id']+': 标签数量错误')
        if row['category']=='conference_calls':
            from website_rules import conference_errors
            errors += conference_errors(item,data['revised_date'])
    return errors

def render_collection(data):
    lines=['---','title: "历史精选：'+data['range_start']+' 至 '+data['range_end']+'"','toc-depth: 2','---','',data['revision_note'],'',
           '推文日期采用原站显示日期；论文采用提交日期，软件采用登记的修订日期。补录不代表曾在该日发送群消息。','', '## 分类入口','']
    for key,label in LABELS.items():
        n=sum(r['category']==key for r in data['entries'])
        lines.append(f'- [{label} ({n} 条)](#{key})')
    lines += ['', '合计 '+str(len(data['entries']))+' 条。同一成果在栏目索引中仅计一次。','']
    for key,label in LABELS.items():
        lines += [f'## {label} {{#{key}}}', '']
        for row in data['entries']:
            if row['category'] != key:continue
            item=resolve(row)
            lines += ['来源日期：'+row['source_date']+'；收录日期：'+row['added_date'],'']
            lines += render_item(item,key,True,heading_level=3,show_dates=False)
    from website_promotions import render_promotion
    lines += [render_promotion(),'']
    return '\n'.join(lines)
