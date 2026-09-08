"""将指定日期起的正式微信短版另存到人工分发目录，不复制 DEMO。"""
import argparse
import hashlib
import json
from pathlib import Path
from site_config import is_public_issue

ROOT = Path(__file__).resolve().parents[1]

def copy_wechat(destination, since='2026-09-08'):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    for source in sorted((ROOT / 'content/issues').glob('*.json')):
        issue = json.loads(source.read_text(encoding='utf-8'))
        if not is_public_issue(issue) or issue['date'] < since:
            continue
        name = issue['date'] + '.txt'
        data = (ROOT / 'publish/wechat' / name).read_bytes()
        target = destination / name
        if target.exists():
            if target.read_bytes() != data:
                raise ValueError('目标存在不同内容，保留原文件：' + str(target))
            status = 'unchanged'
        else:
            with target.open('xb') as handle:
                handle.write(data)
            status = 'copied'
        if target.read_bytes() != data:
            raise ValueError('复制校验失败：' + str(target))
        results.append(dict(file=name, status=status, sha256=hashlib.sha256(data).hexdigest()))
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--since', default='2026-09-08')
    args = parser.parse_args()
    destination = args.destination
    if destination is None:
        config = json.loads((ROOT/'ops-local/wechat-delivery.json').read_text(encoding='utf-8'))
        destination = Path(config['destination'])
    print(json.dumps(copy_wechat(destination, args.since), ensure_ascii=False, indent=2))
