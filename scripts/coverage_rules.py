"""C-08 覆盖核对：独立观察目录、逐篇处置和有来源的区间必须相符。"""
from lianxh_exclusions import screen_post, normalized_url
from datetime import datetime, time, timedelta
from trial_selection import evaluation, exact_date, identities, publication_events


def coverage_errors(coverage, core_posts, as_of, observed_posts, history=()):
    errors = []
    if coverage.get('status') != 'complete':
        errors.append('C-08 覆盖不明')
    start = end = None
    try:
        start = evaluation(coverage.get('baseline'))
        end = evaluation(coverage.get('checked_to'))
        if start > end: errors.append('C-08 覆盖区间反向')
        if end != evaluation(as_of): errors.append('C-08 检查终点与 as-of 不一致')
    except (TypeError, ValueError):
        errors.append('C-08 起止时点缺失或无法解析')
    evidence = coverage.get('baseline_evidence')
    # 非空的否定说明不是基点证据；不从期次日期、mtime 或窗口倒推。
    if not isinstance(evidence, dict) or not (
        evidence.get('status') == 'confirmed'
        and evidence.get('kind') in {'formal-coverage', 'user-decision'}
        and evidence.get('source') and evidence.get('locator')
        and evidence.get('sha256')
        and evidence.get('coverage_through') == coverage.get('baseline')
    ):
        errors.append('C-08 缺来源明确的已确认基点证据')
    if not coverage.get('page_evidence'):
        errors.append('C-08 缺观察目录来源')

    rows = coverage.get('post_records', [])
    if not isinstance(rows, list) or not isinstance(observed_posts, list):
        return errors + ['C-08 观察或处置清单格式不合法']
    observed = {row.get('id'): row for row in observed_posts}
    records = {row.get('id'): row for row in rows}
    if None in observed or None in records or len(observed) != len(observed_posts) or len(records) != len(rows):
        errors.append('C-08 观察或处置 ID 缺失 / 重复')
    if set(observed) != set(records):
        errors.append('C-08 逐篇处置与独立观察目录不一致')
    required, unresolved, baseline_pending = set(), set(), set()
    core = set(core_posts)
    for post_id, post in observed.items():
        row = records.get(post_id)
        if row is None: continue
        if row.get('url') != post.get('url') or row.get('date') != post.get('date'):
            errors.append(f'C-08 {post_id} 来源 URL / 日期与观察目录不符')
        decision = row.get('decision')
        gate = screen_post(dict(post, content_classification=row.get('content_classification', {})))
        if gate['action'] == 'excluded':
            if decision != 'excluded' or not row.get('reason') or not row.get('evidence'):
                errors.append(f'C-08 {post_id} 须有据登记 excluded，不得计入待选或 already-short')
            if post_id in core: errors.append(f'C-08 {post_id} 排除项进入 core')
            continue
        if gate['action'] == 'review' and decision in {'proposed', 'already-short'}:
            errors.append(f'C-08 {post_id} 内容性质尚待核查')
        if decision == 'proposed': required.add(post_id)
        elif decision == 'pending': unresolved.add(post_id)
        elif decision == 'pending-baseline': baseline_pending.add(post_id)
        elif decision == 'already-short':
            # 只进网页 extended、只核验过和实际送达未知均不能替代短版证据。
            matching = [h for h in history if identities(post) & identities(h)]
            proven = False
            for h in matching:
                for event in publication_events(h, 'lianxh_posts'):
                    try:
                        proven |= exact_date(event.get('date')) <= evaluation(as_of).date()
                    except (TypeError, ValueError):
                        pass
            if not proven:
                errors.append(f'C-08 {post_id} 缺对应微信短版收录证据')
        elif decision == 'excluded':
            if not row.get('reason') or not row.get('evidence'):
                errors.append(f'C-08 {post_id} 排除缺理由或证据')
        elif decision != 'before-baseline':
            errors.append(f'C-08 {post_id} 未有合法处置')
        if decision in {'proposed', 'pending', 'pending-baseline'} and not row.get('reason'):
            errors.append(f'C-08 {post_id} 待处理记录缺说明')
        if decision == 'proposed' and post_id not in core:
            errors.append(f'C-08 {post_id} 应收录新推文存在遗漏')
        if decision != 'proposed' and post_id in core:
            errors.append(f'C-08 {post_id} 实际 core 与处置状态不符')
        # 日期只有日精度时采用区间界限，不凭空补成当天零点的发布时间。
        try:
            day = exact_date(post.get('date'))
            lo = datetime.combine(day, time.min, evaluation(as_of).tzinfo)
            hi = lo + timedelta(days=1)
            if decision == 'before-baseline' and (start is None or hi > start):
                errors.append(f'C-08 {post_id} 不能证明早于覆盖基点')
            if decision == 'proposed' and start is not None:
                if hi <= start or lo > evaluation(as_of):
                    errors.append(f'C-08 {post_id} 不在覆盖区间')
                elif lo < start:
                    errors.append(f'C-08 {post_id} 与基点同日，需更精确上线时间')
        except (TypeError, ValueError):
            errors.append(f'C-08 {post_id} 观察日期不明确')
    if core - set(observed): errors.append('C-08 core 存在未观察推文')
    if set(coverage.get('required_post_ids', [])) != required:
        errors.append('C-08 required_post_ids 与逐篇处置不一致')
    if set(coverage.get('unresolved_posts', [])) != unresolved:
        errors.append('C-08 unresolved_posts 与逐篇处置不一致')
    if unresolved: errors.append('C-08 尚有推文待核验或安排')
    if baseline_pending: errors.append('C-08 较早观察条目仍依赖可信基点，未判为已覆盖')
    return sorted(set(errors))
