"""微信字段 formatter：共享已核验事实，不解析 legacy citation，不做选稿。"""
import re
from urllib.parse import urlsplit
from website_citations import bibliography_metadata, safe_url

JOURNAL_LABELS = {
    'The Quarterly Journal of Economics': 'QJE',
    'American Economic Review': 'AER',
    'Journal of Political Economy': 'JPE',
    'Econometrica': 'Econometrica',
    'The Review of Economic Studies': 'REStud',
}
KINDS = {'lianxh_posts': ('✍️', '新推文'), 'papers': ('📰', '论文'),
         'tools': ('📦', '软件'), 'research_resources': ('📦', '资源'),
         'conference_calls': ('📅', '会议征稿')}
URL_TOKEN = re.compile(r'https?://\S+')


def single_line(value):
    # 结构字段不能夹带换行、空白行或未编辑内容。
    if not isinstance(value, str) or not value.strip() or '\n' in value or '\r' in value:
        raise ValueError('微信字段必须是非空单行文本')
    return value


def format_url(label, url):
    label = single_line(label)
    if not safe_url(url) or url[-1] in '。。，,；;：:！!？?）)]}':
        raise ValueError('微信 URL 不合法或末尾紧贴标点')
    return f'{label}： {url} '


def valid_url_line(line):
    # 保留行尾真实 U+0020，禁止 strip() 后再验证。
    matches = list(URL_TOKEN.finditer(line))
    if len(matches) != 1:
        return False
    match = matches[0]
    label = line[:match.start()]
    return (label.endswith('： ') and not label.endswith('：  ')
            and bool(label[:-2]) and not label[:-2].endswith(' ')
            and line[match.end():] == ' '
            and safe_url(match.group()) == match.group()
            and match.group()[-1] not in '。。，,；;：:！!？?）)]}')


def item_heading(category, item, number):
    emoji, kind = KINDS[category]
    source = ''
    if category == 'papers':
        journal = item.get('journal', '')
        source = JOURNAL_LABELS.get(journal, journal)
    elif category == 'tools':
        source = item.get('ecosystem', '')
        if source == 'Stata':
            kind = '命令'
    elif category in ('research_resources', 'conference_calls'):
        source = item.get('source_name', '')
    title = single_line(item['title'])
    if source:
        single_line(source)
        # 只处理已知来源的精确前缀；不从标题发现或推断来源。
        for prefix in (source + '：', source + ':'):
            if title.startswith(prefix):
                title = title[len(prefix):].lstrip()
                break
        single_line(title)
        kind += ' · ' + source
    return f'{emoji} {number:02d}｜{kind}：{title}'


def short_authors(authors):
    if not isinstance(authors, list) or not authors:
        raise ValueError('BLOCKED: 缺少有序作者 metadata')
    names = []
    for author in authors:
        # 仅接受明确的 APA 倒置姓名；复姓、连字符原样保留。
        match = re.fullmatch(r'([^,\n]+),\s*(?:[^\W\d_]\.\s*[- ]?\s*)+', author) if isinstance(author, str) else None
        if not match:
            raise ValueError(f'BLOCKED: 无法安全生成作者短名：{author!r}')
        names.append(match.group(1).strip())
    if len(names) > 3:
        return names[0] + ' et al.'
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' & ' + names[-1]


def format_wechat_citation(metadata):
    # 完整题名也合规；只在已有独立 main_title 字段时省略副标题。
    # 不按冒号或句号自动拆分题名，避免损坏真实主标题。
    title = single_line(metadata.get('main_title') or metadata['title']).rstrip('.')
    if metadata.get('main_title') and not metadata['title'].startswith(title):
        raise ValueError('BLOCKED: main_title 与完整题名不一致')
    source = single_line(metadata['source'])
    source = JOURNAL_LABELS.get(source, source)
    status = metadata.get('publication_status')
    if status == 'forthcoming':
        source += ', forthcoming'
    elif metadata.get('volume'):
        source += ', ' + str(metadata['volume'])
        if metadata.get('issue'):
            source += '(' + str(metadata['issue']) + ')'
        if metadata.get('pages'):
            source += ': ' + str(metadata['pages'])
    return f"{short_authors(metadata['authors'])} ({metadata['year']}). {title}. {source.rstrip('.')}."


def paper_metadata(item):
    metadata = bibliography_metadata(item)
    # 微信另校验已存在的共享字段，不更改网站既有格式或事实。
    for key, meta_key in (('publication_status', 'publication_status'), ('journal', 'source')):
        if item.get(key) and metadata.get(meta_key) != item[key]:
            raise ValueError(f'BLOCKED: 论文 {key} 与 bibliography 不一致')
    return metadata


def reader_links(category, item):
    if category == 'papers':
        metadata = paper_metadata(item)
        result = [('主页', item['homepage_url'])]
        pdf = metadata.get('pdf', {})
        if (safe_url(pdf.get('url')) and pdf.get('public_access') is True
                and pdf.get('retrieved_date') and safe_url(pdf.get('source_url'))
                and urlsplit(pdf['url']).hostname != 'doi.org'):
            if item.get('pdf_url') != pdf['url']:
                raise ValueError('BLOCKED: 微信 PDF 与 bibliography 不一致')
            version = pdf.get('version') or item.get('pdf_version')
            if pdf.get('version') and item.get('pdf_version') and pdf['version'] != item['pdf_version']:
                raise ValueError('BLOCKED: PDF 版本不一致')
            result.append(('PDF' + (f' ({single_line(version)})' if version else ''), pdf['url']))
        return result
    if category == 'lianxh_posts':
        return [('阅读全文', item['url'])]
    if category == 'conference_calls':
        return [('通知', item['official_url'])]
    url = item['url']
    # hostname 映射仅用于链接 label，不用于标题来源推断。
    label = item.get('source_name') or {'cran.r-project.org': 'CRAN', 'pypi.org': 'PyPI',
                                      'github.com': 'GitHub'}.get(urlsplit(url).hostname, '主页')
    return [(label, url)]


def item_lines(category, item, number):
    summary = item.get('wechat_summary')
    if not summary and category == 'conference_calls':
        summary = f"主题或范围：{single_line(item['topic'])}；截止日期：{item['deadline']}"
    lines = [item_heading(category, item, number), single_line(summary)]
    if category == 'papers':
        lines.append('引文：' + format_wechat_citation(paper_metadata(item)))
    elif category == 'tools':
        lines.append(f"版本：{item['ecosystem']} / {item['name']} {item['version']}；发布：{item['release_date']}")
    elif category == 'conference_calls':
        lines.append(f"截止：{item['deadline']}")
    lines.extend(format_url(label, url) for label, url in reader_links(category, item))
    return lines
