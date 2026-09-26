"""核对当天课程发现结果是否已转入网站配置；不会改写配置或自动批准。"""
import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from website_promotions import active_courses

ROOT = Path(__file__).resolve().parents[1]


def check_handoff(discovery, config, today):
    # 首轮关注近 30 天新发布课程；旧课程仍由原来的实体日期机制管理。
    errors = []
    if discovery.get('retrieved_date') != today.isoformat():
        errors.append('课程来源尚未完成当日检查，不能沿用旧候选冒充今日结果')
    if not discovery.get('candidates'):
        errors.append('课程候选为空，需核对来源和解析结果')
    courses = config.get('approved_courses', [])
    pending = []
    for candidate in discovery.get('candidates', []):
        source_date = date.fromisoformat(candidate['source_date'])
        if source_date > today:
            errors.append('课程来源日期晚于当前日期：' + candidate['url'])
            continue
        if source_date < today - timedelta(days=30):
            continue
        reviewed = False
        for course in courses:
            urls = {course.get('url'), course.get('source_url')}
            urls.update(link.get('url') for link in course.get('links', []))
            if candidate['url'] not in urls:
                continue
            try:
                # 已结束课程仍可算作完成审核，不要求它重新出现在页面上。
                at = min(today, date.fromisoformat(course['course_end_date']))
                valid = active_courses(dict(config, approved_courses=[course]), at)
                reviewed = bool(valid) and source_date <= date.fromisoformat(course['reviewed_date']) <= today
            except (KeyError, ValueError, TypeError):
                reviewed = False
            if reviewed:
                break
        if not reviewed:
            pending.append(candidate)
            errors.append('新课程尚未完成网站配置审核：' + candidate['url'])
    return dict(date=today.isoformat(), passed=not errors, errors=errors, pending=pending)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', default=date.today().isoformat())
    args = parser.parse_args()
    today = date.fromisoformat(args.date)
    try:
        discovery = json.loads((ROOT/'ops-local/promotion-candidates.json').read_text(encoding='utf-8'))
        config = json.loads((ROOT/'config/promotions.json').read_text(encoding='utf-8'))
        result = check_handoff(discovery, config, today)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = dict(date=args.date, passed=False, errors=[str(exc)])
    output = ROOT/'ops-local/runs'/args.date/'course-handoff.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
