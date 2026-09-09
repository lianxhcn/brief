"""C-23 论文来源与双端选稿验收；只验记录，不代替来源核实。"""
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

POLICY = json.loads((Path(__file__).resolve().parents[1] / 'config/paper-policy.json').read_text(encoding='utf-8-sig'))

def norm(value):
    return str(value).casefold().removeprefix('the ').strip()

TOP = {norm(name) for names in POLICY['top_journal_groups'].values() for name in names}

def url(value):
    parsed = urlparse(value if isinstance(value, str) else '')
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc)

def coverage(rows, expected, today, max_age, label):
    errors = []
    if not isinstance(rows, list):
        return [f'{label}: 缺少逐来源检索记录。']
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append(f'{label}: 非法记录。')
            continue
        source = norm(row.get('source', ''))
        if source in seen:
            errors.append(f'{label}: 来源重复 {source}。')
        seen.add(source)
        effective = row.get('fallback', {}) if row.get('status') == 'access-failed' else row
        if not isinstance(effective, dict):
            effective = {}
        valid = effective.get('status') in ('found', 'no-eligible')
        valid = valid and url(row.get('evidence_url')) and bool(row.get('reason'))
        valid = valid and url(effective.get('evidence_url')) and bool(effective.get('reason'))
        ids = effective.get('candidate_ids')
        valid = valid and isinstance(ids, list) and (bool(ids) == (effective.get('status') == 'found'))
        try:
            checked = date.fromisoformat(effective.get('checked_at', ''))
            start = date.fromisoformat(effective.get('window_start', ''))
            end = date.fromisoformat(effective.get('window_end', ''))
            valid = valid and 0 <= (today - checked).days <= max_age
            valid = valid and end == checked and (end - start).days >= 14
        except (ValueError, TypeError):
            valid = False
        if not valid:
            errors.append(f'{label}: {source} 检索缺失、过期或失败，不能视为无合格内容。')
    for source in sorted(expected - seen):
        errors.append(f'{label}: 未记录 {source}。')
    return errors

def paper_policy_errors(issue):
    if issue.get('issue_type') != 'daily' or issue.get('status') == 'demo':
        return []
    if str(issue.get('date', '')) < POLICY['effective_date'] and issue.get('paper_policy_version') != 1:
        return []
    try:
        today = date.fromisoformat(issue.get('revision_date') or issue.get('date', ''))
    except (ValueError, TypeError):
        return ['C-23: 缺少有效期次日期。']
    review = issue.get('paper_review')
    if not isinstance(review, dict):
        return ['C-23: 缺少 paper_review，不能以 arXiv 单一检索代替来源覆盖。']
    errors = coverage(review.get('journal_checks'), TOP, today, POLICY['journal_check_max_age_days'], 'Top Journal')
    errors += coverage(review.get('working_paper_checks'), {norm(s) for s in POLICY['working_paper_sources']}, today, POLICY['working_paper_check_max_age_days'], 'Working paper')
    papers = issue.get('papers', [])
    core = [p for p in papers if p.get('priority') == 'core']
    formal = lambda p: p.get('publication_status') in ('published', 'forthcoming')
    top_count = sum(formal(p) and norm(p.get('journal', '')) in TOP for p in core)
    wp_count = sum(p.get('publication_status') == 'working-paper' for p in core)
    if core and (top_count * 2 <= len(core) or wp_count > 1):
        ex = review.get('composition_exception', {})
        if not isinstance(ex, dict):
            ex = {}
        ids = ex.get('selected_paper_ids')
        compared = ex.get('compared_candidate_ids')
        valid = ex.get('code') in ('no-eligible', 'deduplicated-shortage', 'exceptional-working-paper')
        valid = valid and bool(ex.get('reason')) and bool(ex.get('reviewed_by'))
        valid = valid and isinstance(compared, list) and isinstance(ids, list)
        valid = valid and sorted(ids) == sorted(p.get('id', '') for p in core)
        if ex.get('code') == 'exceptional-working-paper' and not compared:
            valid = False
        if not valid:
            errors.append('C-23: 重点论文须 Top Journal 严格过半、工作论文最多 1 篇；偏离须完整 composition_exception。')
    # 延伸阅读只以论文计数；不足目标时要求可追踪的替代记录。
    extended = [p for p in papers if p.get('priority') == 'extended']
    extended_top = sum(formal(p) and norm(p.get('journal', '')) in TOP for p in extended)
    if extended_top < (len(extended) + 1) // 2:
        ex = review.get('extended_composition_exception', {})
        if not isinstance(ex, dict):
            ex = {}
        replacements = ex.get('replacement_paper_ids')
        eligible_ids = {p.get('id') for p in extended if p.get('publication_status') == 'working-paper'}
        valid = bool(ex.get('reason')) and bool(ex.get('reviewed_by'))
        valid = valid and isinstance(ex.get('compared_candidate_ids'), list)
        valid = valid and isinstance(replacements, list) and bool(replacements)
        valid = valid and all(isinstance(i, str) and i in eligible_ids for i in replacements)
        valid = valid and len(set(replacements)) >= (len(extended) + 1) // 2 - extended_top
        if not valid:
            errors.append('C-23: 延伸阅读论文的顶刊目标为半数向上取整；不足须记录真实检索及高质量工作论文替代理由。')
    sources = []
    for paper in papers:
        if formal(paper) and not url(paper.get('publication_evidence_url')):
            errors.append(f"C-23: {paper.get('id')} 缺少正式发表或录用证据。")
        if paper.get('publication_status') == 'working-paper':
            source = norm(paper.get('working_paper_source', ''))
            if not source:
                errors.append(f"C-23: {paper.get('id')} 缺少 working_paper_source。")
            sources.append(source)
    if len(sources) >= 4 and max(sources.count(s) for s in sources) * 2 > len(sources):
        balance = review.get('source_balance_review', {})
        if not isinstance(balance, dict):
            balance = {}
        compared = balance.get('compared_sources', [])
        if not (balance.get('reason') and balance.get('reviewed_by') and isinstance(compared, list) and len({norm(s) for s in compared}) >= 2):
            errors.append('C-23: 工作论文单平台集中，缺少至少两来源比较与复核理由。')
    return errors
