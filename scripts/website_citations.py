"""共享已核验 bibliography resolver 与网站专用 myAPA formatter。"""
import html
import json
import re
from pathlib import Path
from urllib.parse import quote, urlsplit

def safe_url(value):
    if not isinstance(value, str) or re.search(r'\s', value):
        return ''
    parsed = urlsplit(value)
    return value if parsed.scheme in ('https', 'http') and parsed.netloc else ''

def external_link(label, url):
    return f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a>'

def format_myapa(m):
    # 标题由编辑提供 sentence case，避免 lower() 损坏专有名词。
    authors = m['authors']
    if not authors or not all(isinstance(a, str) and a.strip() for a in authors):
        raise ValueError('myAPA 需要有序作者列表')
    names = authors[0] if len(authors) == 1 else (' & '.join(authors) if len(authors) == 2 else ', '.join(authors[:-1]) + ', & ' + authors[-1])
    source = m['source']
    if m.get('volume'):
        source += ', ' + str(m['volume'])
        if m.get('issue'):
            source += '(' + str(m['issue']) + ')'
    if m.get('pages'):
        source += ', ' + str(m['pages'])
    if m.get('publication_status') == 'forthcoming':
        source += ' (forthcoming)'
    title = m['title'].rstrip()
    # 保留真实题名及其结尾标点；没有句末标点时才补句号。
    title_end = title if title.endswith(('.', '?', '!', '。', '？', '！')) else title + '.'
    text = f"{names.rstrip('.')}. ({m['year']}). {title_end} {source.rstrip('.')}."
    links = []
    url = safe_url(m.get('doi_url')) or safe_url(m.get('homepage_url'))
    if url:
        links.append(external_link('Link', url))
    # PDF 核验记录绑定具体 URL；不以 DOI 冒充 PDF。
    pdf = m.get('pdf', {})
    if (safe_url(pdf.get('url')) and pdf.get('public_access') is True
            and pdf.get('retrieved_date') and safe_url(pdf.get('source_url'))
            and urlsplit(pdf['url']).netloc != 'doi.org'):
        links.append(external_link('PDF', pdf['url']))
    links.append(external_link('Google', 'https://scholar.google.com/scholar?q=' + quote(m['title'], safe='')))
    return '<p class="myapa">' + html.escape(text) + ' ' + ', '.join(links) + '</p>'

def bibliography_metadata(item):
    path = Path(__file__).resolve().parents[1] / 'config/website-citations.json'
    metadata = item.get('bibliography') or json.loads(path.read_text(encoding='utf-8')).get(item['id'])
    if metadata is None:
        raise ValueError(f"{item['id']}: 缺少已核验的网站引文元数据")
    # 兼容期 sidecar 必须继续匹配共享事实，避免两端元数据漂移。
    if not item.get('bibliography'):
        citation = item.get('citation', '')
        if metadata['title'].casefold() not in citation.casefold():
            raise ValueError('网站完整题名与共享事实不一致')
        if metadata.get('doi_url') != item.get('doi_url'):
            raise ValueError('网站 DOI 与共享事实不一致')
        if metadata.get('pdf', {}).get('url') != item.get('pdf_url'):
            raise ValueError('网站 PDF 核验记录与共享事实不一致')
        positions = [citation.find(author) for author in metadata['authors']]
        if any(p < 0 for p in positions) or positions != sorted(positions):
            raise ValueError('网站作者顺序与共享事实不一致')
    return metadata


def website_citation(item):
    return format_myapa(bibliography_metadata(item))
