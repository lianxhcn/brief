"""Separate the issue's content date from actual review and backfill dates."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

CATEGORIES = ('lianxh_posts', 'papers', 'tools', 'research_resources', 'conference_calls')
CST = timezone(timedelta(hours=8))


def exact_date(value: object) -> date:
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('日期须明确为 YYYY-MM-DD')
    return date.fromisoformat(value)


def review_date(issue: dict) -> date:
    """Return the actual review day; reject conflicting date aliases."""
    content_day = exact_date(issue.get('date'))
    aliases = [exact_date(issue[key]) for key in ('revised_date', 'revision_date') if issue.get(key)]
    if aliases and any(day != aliases[0] for day in aliases):
        raise ValueError('revised_date 与 revision_date 不一致')
    if 'backfill' in issue:
        backfill = issue['backfill']
        if not isinstance(backfill, dict) or not isinstance(backfill.get('reason'), str) or not backfill['reason'].strip():
            raise ValueError('backfill 须提供 prepared_date 和非空 reason')
        actual_day = exact_date(backfill.get('prepared_date'))
        if actual_day < content_day:
            raise ValueError('补录日期不得早于内容所属日期')
        if actual_day > datetime.now(CST).date():
            raise ValueError('补录日期不得在未来')
        if aliases and any(day != actual_day for day in aliases):
            raise ValueError('修订日期须与 backfill.prepared_date 一致')
    else:
        actual_day = aliases[0] if aliases else content_day
    if actual_day < content_day:
        raise ValueError('核验或修订日期不得早于内容所属日期')
    return actual_day


def issue_date_errors(issue: dict) -> list[str]:
    """Validate backfill facts without changing historical or ordinary issues."""
    try:
        actual_day = review_date(issue)
        content_day = exact_date(issue.get('date'))
    except (TypeError, ValueError) as exc:
        return ['期次日期口径：' + str(exc)]
    if 'backfill' not in issue:
        return []
    errors = []
    if issue.get('retrieved_date'):
        try:
            if exact_date(issue['retrieved_date']) > actual_day:
                errors.append('期次 retrieved_date 晚于实际补录日期')
        except ValueError:
            errors.append('期次 retrieved_date 日期格式不合法')
    for category in CATEGORIES:
        for item in issue.get(category, []):
            label = item.get('id', '<unknown>')
            source_field = 'release_date' if category == 'tools' else 'published_date'
            for field in (source_field, 'retrieved_date'):
                if not item.get(field):
                    errors.append(f'{label}: 补刊缺少 {field}，不能确认所属日或实际核验日')
            for field in ('published_date', 'release_date', 'retrieved_date', 'added_date'):
                if not item.get(field):
                    continue
                try:
                    # 补刊需要日精度，不能把未知日补成月初来通过所属日截止。
                    when = exact_date(item[field])
                    limit = content_day if field in ('published_date', 'release_date') else actual_day
                    if when > limit:
                        label_date = '内容所属日期，不得倒填' if field in ('published_date', 'release_date') else '实际补录日期'
                        errors.append(f'{label}: {field} 晚于{label_date}')
                except (TypeError, ValueError):
                    errors.append(f'{label}: {field} 日期格式不合法')
    return errors
