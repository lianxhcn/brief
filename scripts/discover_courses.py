"""手动发现课程候选，只写 ops-local；禁止直接替换公开配置。"""
import argparse
import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urljoin

SOURCE = 'https://www.lianxh.cn/blogs/44.html'
ROOT = Path(__file__).resolve().parents[1]

class CourseParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.active = None
        self.heading = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            href = attrs.get('href', '')
            if re.fullmatch(r'/details/\d+\.html', href):
                self.active = dict(url=urljoin(SOURCE, href), title='', text='')
        if self.active and tag == 'h5':
            self.heading = True

    def handle_data(self, text):
        if self.active:
            self.active['text'] += text + ' '
            if self.heading:
                self.active['title'] += text

    def handle_endtag(self, tag):
        if tag == 'h5':
            self.heading = False
        if tag == 'a' and self.active:
            item = self.active
            match = re.search(r'\b20\d{2}-\d{2}-\d{2}\b', item.pop('text'))
            if match and item['title'].strip() and not any(x in item['title'] for x in ('公开课', '招聘')):
                item['title'] = item['title'].strip()
                item['source_date'] = date.fromisoformat(match[0]).isoformat()
                self.items.append(item)
            self.active = None

def parse_courses(text, retrieved_date):
    if '<title>专题课程' not in text:
        raise ValueError('课程来源页面结构或标题异常')
    parser = CourseParser()
    parser.feed(text)
    if not parser.items:
        raise ValueError('未识别到课程候选，保留已有配置')
    # 排序仅用于候选复核，不代表正在报名。来源日期不是开课日期。
    items = sorted({i['url']: i for i in parser.items}.values(), key=lambda i: i['source_date'], reverse=True)
    return dict(source_url=SOURCE, retrieved_date=retrieved_date, review_status='pending', candidates=items[:10])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, help='使用已保存的公开 HTML 进行离线验证')
    args = parser.parse_args()
    try:
        text = args.html.read_text(encoding='utf-8') if args.html else urlopen(SOURCE, timeout=20).read().decode('utf-8')
        result = parse_courses(text, date.today().isoformat())
        # 固定私有候选位置；解析成功才原子替换，失败不清空旧记录。
        output = ROOT / 'ops-local/promotion-candidates.json'
        output.parent.mkdir(exist_ok=True)
        temp = output.with_suffix('.tmp')
        temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temp.replace(output)
    except (OSError, ValueError) as exc:
        print(f'FAILURE: {exc}; 公开推广配置保持不变。')
        return 1
    print(f'候选 {len(result["candidates"])} 条，待人工审核：{output}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
