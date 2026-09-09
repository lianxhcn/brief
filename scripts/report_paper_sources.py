"""输出当期及滚动七天论文来源分布；不将历史偏差标记为合规。"""
import argparse
from collections import Counter
from datetime import date, timedelta
import json
from pathlib import Path


def distribution(issues):
    counts = Counter()
    for issue in issues:
        for paper in issue.get('papers', []):
            status = paper.get('publication_status', 'unknown')
            # 历史缺少平台字段时只标识存储域名，不推断发表身份。
            platform = paper.get('working_paper_source') or paper.get('journal', 'unknown')
            field = paper.get('field', 'unknown')
            counts[(status, platform, field)] += 1
    return [dict(publication_status=k[0], source=k[1], field=k[2], count=v) for k, v in sorted(counts.items())]


def report(root, target):
    selected = []
    for path in sorted((root / 'content/issues').glob('*.json')):
        issue = json.loads(path.read_text(encoding='utf-8-sig'))
        if issue.get('issue_type') != 'daily' or issue.get('status') != 'published':
            continue
        when = date.fromisoformat(issue['date'])
        if target - timedelta(days=6) <= when <= target:
            selected.append(issue)
    return dict(date=target.isoformat(), daily=distribution([i for i in selected if i['date'] == target.isoformat()]),
                rolling_seven_days=distribution(selected), included_issue_dates=[i['date'] for i in selected])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', required=True, type=date.fromisoformat)
    args = parser.parse_args()
    print(json.dumps(report(Path(__file__).resolve().parents[1], args.date), ensure_ascii=False, indent=2))
