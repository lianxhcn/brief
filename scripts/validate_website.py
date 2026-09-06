"""构建后检查正式公共索引和内部链接；不修改 search.json。"""
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from build_catalog_pages import public_issues
from website_content import INTERNAL_PHRASES
from site_config import ROOT, date_compact

class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.hrefs, self.ids = [], set()
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.hrefs.append(attrs['href'])

class VisibleText(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.skip = 0
        self.parts = []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'head'):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head'):
            self.skip -= 1
    def handle_data(self, text):
        if not self.skip:
            self.parts.append(text)

def validate(output):
    errors = []
    search = json.loads((output / 'search.json').read_text(encoding='utf-8'))
    public = [output / 'index.html', output / 'archive.html', *sorted((output / 'topics').glob('*.html'))]
    public += [output / 'issues' / date_compact(i['date']) / 'index.html' for i in public_issues()]
    indexes = [output / 'search.json', *output.glob('*.xml'), *output.glob('*.rss'), *output.glob('*listing*.json')]
    for path in [*public, *indexes]:
        text = path.read_text(encoding='utf-8')
        if re.search(r'DEMO|2099[-/]?01', text, re.I):
            errors.append(f'{path.name}: 公共页面或索引出现 DEMO')
    for issue in public_issues():
        route = 'issues/' + date_compact(issue['date']) + '/index.html'
        if not any(route in record.get('href', '') for record in search):
            errors.append(f'{route}: 正式期次未进入搜索')
    for path in public:
        visible = ' '.join(VisibleText(path.read_text(encoding='utf-8')).parts)
        for phrase in (*INTERNAL_PHRASES, '该页面内容'):
            if phrase in visible:
                errors.append(f'{path.name}: 公开可见文本含 {phrase}')
    for record in search:
        for phrase in INTERNAL_PHRASES:
            if phrase in record.get('text', ''):
                errors.append(f'搜索摘要含内部文案 {phrase}')
        if re.search(r'<(?:p|div|a)\b|\]\(https?://', record.get('text', '')):
            errors.append('搜索摘要含原始标记')
    for path in public:
        parsed = Links(path.read_text(encoding='utf-8'))
        for href in parsed.hrefs:
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (output / unquote(url.path).removeprefix('/brief/').lstrip('/')) if url.path.startswith('/') else path.parent / unquote(url.path)
            if target.is_dir():
                target /= 'index.html'
            if not target.exists():
                errors.append(f'{path.relative_to(output)}: 链接目标缺失 {href}')
            elif url.fragment and target.suffix == '.html' and unquote(url.fragment) not in Links(target.read_text(encoding='utf-8')).ids:
                errors.append(f'{path.relative_to(output)}: 锚点缺失 {href}')
    return errors

if __name__ == '__main__':
    errors = validate(ROOT / '_site')
    print('\n'.join(errors) if errors else 'PASS: 公共索引、正式搜索、DEMO 隔离及内部链接')
    raise SystemExit(bool(errors))
