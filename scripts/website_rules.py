"""网页内容闸门；与只含重点的微信群格式校验分开。"""
from datetime import date
import hashlib
from pathlib import Path
from website_citations import bibliography_metadata, arxiv_pdf
from trial_selection import identities

CATEGORIES = ('lianxh_posts', 'papers', 'tools', 'research_resources', 'conference_calls')
DISCOVERY = ('posts', 'papers', 'software', 'conferences')

def conference_errors(item, as_of, history=()):
    errors = []
    for key in ('event_id', 'organizer_or_journal', 'topic', 'official_url',
                'event_date', 'location', 'fee_note', 'deadline_kind', 'status'):
        if not item.get(key): errors.append('会议缺少 ' + key)
    if item.get('deadline_kind') not in {'submission', 'registration'}:
        errors.append('会议须区分投稿和报名截止')
    if item.get('status') not in {'open', 'closed', 'postponed', 'cancelled'}:
        errors.append('会议状态无效')
    try:
        deadline = date.fromisoformat(item['deadline'])
        event = date.fromisoformat(item['event_date'])
        today = date.fromisoformat(as_of[:10])
        if deadline > event: errors.append('截止日晚于会议开始日')
        if item.get('status') == 'open' and (deadline < today or event < today):
            errors.append('已过期会议不得作为可行动征稿')
    except (KeyError, ValueError, TypeError): errors.append('会议日期无效')
    if item.get('status') in {'postponed', 'cancelled'} and not item.get('announcement_url'):
        errors.append('延期或取消缺官方公告')
    if item.get('reminder'):
        previous = [r for r in history if r.get('event_id') == item.get('event_id')
                    and any(e.get('kind') in {'website', 'wechat_short'} and e.get('evidence') for e in r.get('events', []))]
        if not previous or any(r.get('reminder') for r in previous):
            errors.append('提醒须有首发记录且每届最多一次')
        if not item.get('previous_id') or item['previous_id'] not in {r.get('id') for r in previous}:
            errors.append('提醒缺少前次条目关联')
    return errors

def discovery_errors(records):
    errors = []
    for kind in DISCOVERY:
        rows = [r for r in records if r.get('category') == kind]
        if not rows: errors.append('缺少分类检索记录：' + kind)
        for r in rows:
            for key in ('source_url', 'query', 'checked_at', 'window_start', 'window_end', 'reason'):
                if not r.get(key): errors.append(kind + ': 检索记录缺少 ' + key)
            status = r.get('status')
            if status not in {'found', 'no-eligible', 'access-failed', 'not-searched'}:
                errors.append(kind + ': 检索状态无效')
            if status == 'not-searched': errors.append(kind + ': 尚未检索不能通过发布验收')
            n, eligible, adopted = (r.get(k) for k in ('candidate_count', 'eligible_count', 'adopted_count'))
            if not all(isinstance(x, int) and x >= 0 for x in (n, eligible, adopted)) or not 0 <= adopted <= eligible <= n:
                errors.append(kind + ': 检索数量不一致')
            elif (status == 'found' and eligible == 0) or (status == 'no-eligible' and eligible != 0) or (status in {'access-failed', 'not-searched'} and adopted):
                errors.append(kind + ': 状态与数量不一致')
            try:
                if not r['window_start'] <= r['window_end'] <= r['checked_at'][:10]:
                    errors.append(kind + ': 检索窗口错误')
                for k in ('window_start','window_end'): date.fromisoformat(r[k])
                date.fromisoformat(r['checked_at'][:10])
            except (KeyError, ValueError, TypeError): errors.append(kind + ': 检索日期无效')
    return errors

def check_website(issue, root=None):
    if issue.get('issue_type') != 'daily': return []
    history = []
    if root:
        import json
        for p in (Path(root)/'content/issues').glob('*.json'):
            old=json.loads(p.read_text(encoding='utf-8'))
            if old.get('status')=='published' and old.get('date','') < issue['date']:
                history.extend(dict(i,events=[dict(kind='website',date=old['date'],evidence=str(p))]) for i in old.get('conference_calls',[]))
    items = [(c, i) for c in CATEGORIES for i in issue.get(c, [])]
    core = sum(i.get('priority') == 'core' for c, i in items)
    extended = sum(i.get('priority') == 'extended' for c, i in items)
    errors = discovery_errors(issue.get('discovery', []))
    if not 3 <= core <= 5: errors.append('网页重点须为 3–5 条')
    if extended > 10 or len(items) > 15: errors.append('网页延伸最多 10 条，合计最多 15 条')
    if extended < 5 or len(items) < 10:
        short = issue.get('short_issue', {})
        if not (short.get('reason') and short.get('draft_path') and short.get('draft_sha256')
                and short.get('searched_sufficiently') is True and short.get('actual_count') == len(items)):
            errors.append('不足 10 条须保留草稿、数量和充分检索原因')
        if any(not any(r.get('category') == c and r.get('status') in {'found','no-eligible'} for r in issue.get('discovery', [])) for c in DISCOVERY):
            errors.append('不足条数例外尚未完成四类检索')
        if root and short.get('draft_path'):
            p = (Path(root) / short['draft_path']).resolve()
            if not p.is_relative_to(Path(root).resolve()) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != short.get('draft_sha256'):
                errors.append('保留草稿路径或指纹不一致')
    seen = set()
    for category, item in items:
        if item.get('added_date'):
            for field in ('source_url','retrieved_date','published_date'):
                if not item.get(field): errors.append(item['id'] + ': 补录缺少 ' + field)
            try:
                source_day=date.fromisoformat(item.get('release_date') if category=='tools' else item['published_date'])
                if source_day > date.fromisoformat(issue['date']): errors.append(item['id'] + ': 来源晚于期次，不得倒填')
                age=(date.fromisoformat(issue['date'])-source_day).days
                limit=62 if category=='tools' and item.get('ecosystem')=='Stata' and issue['date']=='2026-09-08' else 30
                if category in {'papers','tools'} and (age > limit or (age>14 and not item.get('omission_reason'))): errors.append(item['id']+': 时效或遗漏理由不合格')
            except (KeyError,ValueError,TypeError): errors.append(item['id']+': 补录来源日期无效')
        keys = identities(item)
        if keys & seen: errors.append(item['id'] + ': 同期成果重复')
        seen.update(keys)
        if category == 'lianxh_posts' and not 2 <= len(set(item.get('catalog', {}).get('tags', []))) <= 3:
            errors.append(item['id'] + ': 推文须有 2–3 个标签')
        if category == 'papers':
            try:
                m = bibliography_metadata(item)
                if arxiv_pdf(m) != arxiv_pdf(item): errors.append(item['id'] + ': arXiv 共享编号不一致')
                expected = arxiv_pdf(m) or arxiv_pdf(item)
                if expected and item.get('pdf_url') != expected:
                    errors.append(item['id'] + ': arXiv PDF 缺失或编号不一致')
            except ValueError as exc: errors.append(item['id'] + ': ' + str(exc))
        if category == 'conference_calls':
            errors += conference_errors(item, issue.get('revised_date', issue['date']), history)
            if item.get('status')=='closed': errors.append(item['id']+': 已结束征稿不进入日常可行动信息')
    return errors
