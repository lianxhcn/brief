"""Pure conference windows and publication occurrence checks; no I/O or proof creation."""
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit
import json
import unicodedata

CST = timezone(timedelta(hours=8))


def _day(value):
    if not isinstance(value, str):
        raise ValueError('date missing')
    if len(value) == 10:
        return date.fromisoformat(value)
    return _moment(value).date()


def _moment(value):
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        raise ValueError('timezone missing')
    return moment.astimezone(CST)


def _url(value):
    return isinstance(value, str) and urlsplit(value).scheme in {'http', 'https'} and bool(urlsplit(value).netloc)


def conference_publication_kind(item):
    """A conference identity is stable; introduction/reminder/change are occurrences."""
    change = item.get('review', {}).get('change_type')
    if change in {'postponement', 'cancellation', 'venue-change', 'participation-change'}:
        return change
    if item.get('status') in {'postponed', 'cancelled'}:
        return {'postponed': 'postponement', 'cancelled': 'cancellation'}[item['status']]
    return 'deadline-reminder' if item.get('reminder') is True else 'initial'


def conference_window(item, as_of):
    """Evaluate the *labelled* submission/registration window, never announcement age.

    Same-day date-only deadlines remain unknown. An aware deadline_at, or an
    aware deadline_open_verified_at with deadline_open_evidence_url, can resolve
    that ambiguity. No end-of-day/timezone is inferred. Registration can remain
    open after submission, but a publisher must label deadline_kind accordingly.
    """
    result = dict(actionable=None, status='unknown', deadline_kind=item.get('deadline_kind'),
                  effective_deadline=item.get('deadline'), days_remaining=None,
                  next_action='核对当届、有效期限及官方通知')
    try:
        today = _day(as_of)
        kind = item.get('deadline_kind')
        raw = item.get(kind + '_deadline') if kind in {'submission', 'registration'} else None
        if raw and item.get('deadline') and raw != item['deadline']:
            result.update(status='inconsistent-labelled-deadline', next_action='将公开 deadline 与所标投稿/报名期限统一；保留另一期限的独立字段')
            return result
        raw = raw or item.get('deadline')
        deadline = _day(raw)
        result.update(effective_deadline=raw, days_remaining=(deadline - today).days)
        if kind not in {'submission', 'registration'}:
            result['status'] = 'unknown-deadline-kind'
            return result
        if item.get('status') in {'closed', 'postponed', 'cancelled'}:
            result.update(actionable=False, status=item['status'], next_action='核对状态变更；不作为开放征稿或报名')
            return result
        if item.get('status') != 'open':
            result['status'] = 'unknown-open-status'
            return result
        event = _day(item['event_date'])
        last_event = _day(item.get('event_end_date') or item.get('event_end') or item['event_date'])
        if last_event < event or deadline > (last_event if kind == 'registration' else event):
            result.update(actionable=False, status='invalid-date-order', next_action='核对截止日与会期')
            return result
        exact = item.get(kind + '_deadline_at') or item.get('deadline_at')
        if exact:
            try:
                limit = datetime.fromisoformat(exact)
                if limit.tzinfo is None or limit.date() != deadline:
                    raise ValueError('deadline date mismatch')
                if len(as_of) == 10 and deadline > today:
                    # Tomorrow-or-later does not need an invented clock today.
                    result.update(actionable=True, status='open', next_action='审核后比较安排')
                    return result
                now = _moment(as_of)
            except (ValueError, TypeError):
                result.update(status='unknown-timezone-or-time', next_action='核对截止时间、时区及实际评估时点')
                return result
            result.update(actionable=now < limit, status='open' if now < limit else 'expired',
                          next_action='审核后比较安排' if now < limit else '参与窗口已结束')
            return result
        if deadline < today or last_event < today:
            result.update(actionable=False, status='expired', next_action='核对是否另有有效报名窗口或正式延期')
            return result
        if deadline == today:
            try:
                checked = _moment(item['deadline_open_verified_at'])
                now = _moment(as_of)
                if checked.date() != today or checked > now or not _url(item.get('deadline_open_evidence_url')):
                    raise ValueError('not current official openness')
            except (KeyError, ValueError, TypeError):
                result.update(status='same-day-unverified', next_action='当天截止：核对具体时间、时区和当前是否开放')
                return result
        result.update(actionable=True, status='open', next_action='优先核验并比较安排' if result['days_remaining'] <= 5 else '审核后尽早比较安排')
    except (KeyError, ValueError, TypeError):
        result.update(status='unknown-date', next_action='核对明确到日的期限和会期；保留未知')
    return result


def _same_event(item, old):
    # Explicit edition identity/aliases only; URL and a similar title do not prove an edition.
    if item.get('event_id') and item.get('event_id') == old.get('event_id'):
        return True
    aliases = set(item.get('identity_aliases', []))
    old_aliases = set(old.get('identity_aliases', []))
    return bool((aliases | {item.get('event_id')}) & (old_aliases | {old.get('event_id')} ) - {None, ''})


def _published_events(row):
    found = []
    for event in row.get('events', []):
        if event.get('kind') not in {'website', 'wechat_short'} or not event.get('evidence'):
            continue
        try:
            _day(event['date'])
        except (KeyError, TypeError, ValueError):
            continue
        found.append(event)
    return found


CHANGE_FIELDS = {
    'venue-change': {'location', 'event_date', 'event_end_date'},
    'participation-change': {'deadline', 'deadline_kind', 'submission_deadline', 'registration_deadline',
                             'fee_note', 'eligibility', 'participation_requirements'},
    'postponement': {'status', 'deadline', 'submission_deadline', 'registration_deadline', 'event_date', 'event_end_date'},
    'cancellation': {'status'},
}


def _normalized(value):
    if isinstance(value, str):
        return ' '.join(unicodedata.normalize('NFKC', value).split())
    if isinstance(value, dict):
        return {key: _normalized(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalized(v) for v in value]
    return value


def conference_change_facts(item):
    """Normalize actual change fields; remarks and links are evidence, not identity.

    This projection does not prove the facts. Callers must still supply official
    evidence, dated publications and the previous payload. URLs can host later
    legitimate updates; changing a URL or a prose note cannot create an event.
    """
    kind = conference_publication_kind(item)
    allowed = CHANGE_FIELDS.get(kind, set())
    proof = item.get('review', {}).get('change_evidence', {})
    before = proof.get('before', {}) if isinstance(proof, dict) else {}
    after = proof.get('after', {}) if isinstance(proof, dict) else {}
    if not isinstance(before, dict):before = {}
    if not isinstance(after, dict):after = {}
    if kind in {'venue-change', 'participation-change'}:
        transitions = {field: {'before': _normalized(before[field]), 'after': _normalized(after[field])}
                       for field in sorted(allowed & before.keys() & after.keys())
                       if _normalized(before[field]) != _normalized(after[field])}
        return {'kind': kind, 'transitions': transitions}
    return {'kind': kind, 'after': {field: _normalized(item[field]) for field in sorted(allowed) if field in item}}


def _change_signature(item):
    return json.dumps(conference_change_facts(item), sort_keys=True, ensure_ascii=False)


def _latest_values(previous, field):
    """Known latest dated field values, without guessing order within an undated day."""
    rows = [(max(_day(e['date']) for e in _published_events(row)), row[field])
            for row in previous if field in row]
    if not rows:return set()
    last = max(day for day, value in rows)
    return {json.dumps(_normalized(value), sort_keys=True, ensure_ascii=False) for day, value in rows if day == last}


def conference_publication_errors(item, history, as_of):
    """Check supplied dated publication facts; never infer or create live proof.

    History rows are full prior payloads with events=[{kind,date,evidence}].
    Missing/undated evidence is not a publication fact and remains an explicit
    history gap. Multiple channels for one row do not create extra reminders.
    """
    errors = []
    if not item.get('event_id'):
        return ['会议缺少稳定同届 event_id']
    related = [row for row in history if _same_event(item, row)]
    collisions = [row for row in history if not _same_event(item, row) and _published_events(row)
                  and ((item.get('id') and item.get('id') == row.get('id'))
                       or (item.get('official_url') and item.get('official_url') == row.get('official_url')))]
    if collisions:
        errors.append('历史条目或官方入口相同但同届身份不同，须先核对身份；不靠更换 event_id 绕过去重')
    if any(not _published_events(row) for row in related):
        errors.append('同届历史缺少有日期的渠道发布证据，须先核对用途')
    previous = [row for row in related if _published_events(row)]
    try:
        today = _day(as_of)
        if any(_day(event['date']) >= today for row in previous for event in _published_events(row)):
            errors.append('同届存在当日或未来发布事实，不得再次发布')
    except (ValueError, TypeError):
        errors.append('会议评估日期无效')
        return errors
    kind = conference_publication_kind(item)
    review = item.get('review', {})
    previous_id = item.get('previous_id') or review.get('previous_id')
    ids = {row.get('id') for row in previous}
    if kind == 'initial':
        if previous:
            errors.append('同届已介绍，须按有证据的提醒或重要变更处理')
        return errors
    if not previous or previous_id not in ids:
        errors.append('提醒或重要变更缺少前次条目及真实发布关联')
    if kind == 'deadline-reminder':
        if any(conference_publication_kind(row) == 'deadline-reminder' for row in previous):
            errors.append('每届最多一次普通截止提醒')
        initials = [row for row in previous if conference_publication_kind(row) == 'initial']
        if not initials:
            errors.append('提醒缺少首次介绍记录')
        for row in initials:
            first_day = min(_day(e['date']) for e in _published_events(row))
            then = conference_window(row, first_day.isoformat())
            now = conference_window(item, as_of)
            if then['days_remaining'] is not None and 0 <= then['days_remaining'] <= 5 and then['effective_deadline'] == now['effective_deadline'] and not review.get('reminder_necessity'):
                errors.append('首次介绍已临近截止，不机械重复提醒；须说明额外提醒必要性')
    else:
        if not _url(review.get('announcement_url') or item.get('announcement_url')) or not review.get('impact') or not review.get('change_evidence'):
            errors.append('重要变更缺官方公告、变更证据或具体影响')
        if any(_change_signature(row) == _change_signature(item) for row in previous
               if conference_publication_kind(row) == kind):
            errors.append('相同重要变更已发布，不重复刊载')
        if kind in {'venue-change', 'participation-change'}:
            proof = review.get('change_evidence', {})
            allowed = CHANGE_FIELDS[kind]
            before = proof.get('before', {}) if isinstance(proof, dict) else {}
            after = proof.get('after', {}) if isinstance(proof, dict) else {}
            if not isinstance(before, dict):before = {}
            if not isinstance(after, dict):after = {}
            linked = [row for row in previous if row.get('id') == previous_id]
            changed = [field for field in allowed & before.keys() & after.keys()
                       if _normalized(before[field]) != _normalized(after[field]) and field in item
                       and _normalized(item[field]) == _normalized(after[field])
                       and any(field in row and _normalized(row[field]) == _normalized(before[field]) for row in linked)]
            if not changed:
                errors.append('举办地或参与条件变更须有与前次及本次字段一致的实际 before/after 证据')
            for field in changed:
                latest = _latest_values(previous, field)
                baseline = json.dumps(_normalized(before[field]), sort_keys=True, ensure_ascii=False)
                if len(latest) != 1 or baseline not in latest:
                    errors.append('重要变更 before 与最新已刊事实不一致：' + field)
        elif kind in {'postponement', 'cancellation'} and previous:
            actual = conference_change_facts(item)['after']
            if any(len(_latest_values(previous, field)) > 1 for field in actual):
                errors.append('延期或取消的最新已刊事实有冲突，须先核对状态和日期')
            differences = [field for field, value in actual.items()
                           if _latest_values(previous, field)
                           and json.dumps(value, sort_keys=True, ensure_ascii=False) not in _latest_values(previous, field)]
            if not differences:
                errors.append('延期或取消没有相对最新已刊事实的实际新增状态或日期')
    return sorted(set(errors))
