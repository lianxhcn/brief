"""首轮隔离候选的证据门槛；只读输入，不代替用户审核。"""
from datetime import date, datetime, timedelta, timezone
import re
from urllib.parse import urlsplit

CST = timezone(timedelta(hours=8), 'Asia/Shanghai')
IMPORTANT = {'correction', 'retraction', 'results-fix', 'postponement', 'cancellation'}
SUBSTANTIVE = {'method', 'data', 'findings', 'feature', 'replication'}

def evaluation(value):
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        raise ValueError('as-of 必须带时区')
    return moment.astimezone(CST)

def exact_date(value):
    # 年月不补日；发现日不参与时效计算。
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('日期须明确到日')
    return date.fromisoformat(value)

def url(value):
    if not isinstance(value, str): return False
    parsed = urlsplit(value)
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc) and not re.search(r'\s', value)

def identities(item):
    """项目身份与 release event 分开；别名只能由核验记录显式提供。"""
    keys = {x.casefold() for x in item.get('identity_aliases', [])}
    for field in ('work_id', 'project_id', 'event_id'):
        if item.get(field): keys.add(item[field].casefold())
    if item.get('doi_url'): keys.add(item['doi_url'].casefold().rstrip('/'))
    if item.get('arxiv_id'): keys.add('arxiv:' + re.sub(r'v\d+$', '', item['arxiv_id']))
    for field in ('url','homepage_url','official_url'):
        if item.get(field): keys.add(item[field].casefold().rstrip('/'))
    if item.get('ecosystem') and item.get('name'):
        keys.add('software:' + item['ecosystem'].casefold() + ':' + item['name'].casefold())
    elif item.get('title'):
        keys.add('title:' + re.sub(r'\W+', '', item['title'].casefold()))
    return keys

def history_matches(item, history):
    keys = identities(item)
    return [record for record in history if keys & identities(record)]

def publication_events(record, category):
    """核验事件只供复用证据；网站与短版分别记录，送达未知不作推断。"""
    kinds = {'wechat_short'} if category == 'lianxh_posts' else {'website', 'wechat_short'}
    return [event for event in record.get('events', [])
            if event.get('kind') in kinds and event.get('evidence')]

def assess(item, category, history, as_of):
    """日期差 0..14 日优先；15..30 日需遗漏理由。沿用旧 <=14 去重边界。"""
    errors = []
    review = item.get('review', {})
    today = evaluation(as_of).date()
    for field in ('source_id','version_read','date_basis','evidence_locator','identity_evidence'):
        if not isinstance(review.get(field), str) or not review[field].strip():
            errors.append('核验缺少 ' + field)
    if not url(review.get('source_url')): errors.append('缺少原始来源 URL')
    if review.get('evidence_level') not in {'abstract','full-text','official-page','release-notes'}:
        errors.append('证据层级未核验')
    if review.get('version_matches') is not True: errors.append('阅读版本对应未确认')
    if review.get('identity_status') != 'resolved': errors.append('成果身份未确认')
    if review.get('human_review') != 'pending': errors.append('不得代填用户审核')
    if review.get('detailed_claims') and (review.get('evidence_level') != 'full-text' or not review.get('claim_locators')):
        errors.append('数字、因果或优劣判断缺正文定位')
    if item.get('pdf_url'):
        pdf = item.get('bibliography', {}).get('pdf', {})
        if pdf.get('url') != item['pdf_url'] or pdf.get('public_access') is not True or not pdf.get('version') or not url(pdf.get('source_url')) or not pdf.get('retrieved_date') or urlsplit(item['pdf_url']).netloc == 'doi.org':
            errors.append('PDF 版本或公开访问证据缺失')
    related = history_matches(item, history)
    if any('events' not in record for record in related):
        errors.append('匹配历史缺事件语义，须先核验用途')
    matches = [record for record in related if publication_events(record, category)]
    change = review.get('change_type', 'none')
    exception = change in IMPORTANT
    previous_ids = {x.get('id') for x in matches}
    if exception:
        if not matches or review.get('previous_id') not in previous_ids or not url(review.get('announcement_url')) or not review.get('impact') or not review.get('change_evidence'):
            errors.append('重要变更缺前次成果关联、原始公告或具体影响')
    if matches and not exception:
        if change not in SUBSTANTIVE or not review.get('new_information') or not review.get('change_evidence'):
            errors.append('长期已见成果无可核验实质新增信息')
        for record in matches:
            for event in publication_events(record, category):
                try:
                    age = (today - exact_date(event['date'])).days
                    if age < 0: errors.append('历史收录日期在未来')
                    if 0 <= age <= 14: errors.append('14 天内普通重复或更新')
                except (ValueError, KeyError): errors.append('前次渠道收录日期不明')
    try:
        relevant = exact_date(review.get('effective_date'))
        # 首发日保持原值；只有有证据的实质更新或状态公告可采用更新日。
        original_field = 'release_date' if category == 'tools' else 'published_date'
        if category != 'conference_calls':
            original = exact_date(item.get(original_field))
            if original > today: errors.append('原始公开日期在未来')
            if relevant != original and not (exception or (change in SUBSTANTIVE and review.get('change_evidence') and review.get('new_information'))):
                errors.append('时效日期偏离原始公开日期且无实质更新证据')
        age = (today - relevant).days
        if age < 0: errors.append('未来日期不能入选')
        if category in {'papers', 'tools'}:
            if age > 30: errors.append('超过 30 天的普通材料或旧状态公告')
            elif age > 14 and not exception and not review.get('omission_reason'):
                errors.append('15–30 天缺重要遗漏理由')
        if evaluation(review['verified_at']) > evaluation(as_of): errors.append('核验时间晚于评估时点')
    except (ValueError, KeyError, TypeError): errors.append('日期或核验时点不明确')
    if category == 'papers' and item.get('publication_status') == 'forthcoming' and not url(review.get('acceptance_url')):
        errors.append('forthcoming 缺录用证据')
    if category == 'tools':
        for field in ('installation_url','example_url','release_url','known_issues_url'):
            if not url(review.get(field)): errors.append('软件缺少 ' + field)
        if not item.get('project_id') or not review.get('update_event') or not review.get('change_evidence'):
            errors.append('软件项目身份与更新事件未区分')
        if review.get('software_tested') is not False: errors.append('本轮须保留软件未实测声明')
    if category == 'conference_calls':
        errors.append('本轮会议状态与提醒链未实现，暂缓真实候选')
    if category == 'research_resources':
        if review.get('resource_use') == 'background-tutorial' or not review.get('timeliness_reason'):
            errors.append('研究资源须说明当前价值；长期材料仅作配套或后续选题')
    return sorted(set(errors))

def selection_errors(issue, history, as_of):
    errors = []
    if evaluation(as_of).date().isoformat() != issue.get('date'):
        errors.append('issue 日期与 Asia/Shanghai as-of 不一致')
    categories = ('lianxh_posts','papers','tools','research_resources','conference_calls')
    seen = set()
    for category in categories:
        for item in issue.get(category, []):
            errors += [item.get('id','?') + ': ' + e for e in assess(item, category, history, as_of)]
            keys = identities(item)
            if keys & seen: errors.append(item.get('id','?') + ': 同批成果重复')
            seen.update(keys)
    return errors
