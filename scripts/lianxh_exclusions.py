"""日常与历史共用的前置筛选；只读分类，不抓取或修改渠道历史。"""
import re
from urllib.parse import urlsplit, urlunsplit
REVISION = 'R02-MERGED-20260907-02'
HOSTS = {'lianxh.cn', 'www.lianxh.cn'}
CONFIRMED = {
 '17': ('fixed', '合并任务书 2.1：用户指定常驻推广页'),
 '1900': ('course-promotion', 'R02 body-review-evidence / post-1900：课程招生'),
 '1919': ('assistant-recruitment', 'R02 body-review-evidence / post-1919：助教招聘'),
 '1923': ('open-class-notice', 'R02 body-review-evidence / post-1923：公开课时间地点'),
}
PROMOTIONS = {'course-promotion', 'assistant-recruitment', 'open-class-notice'}
RESEARCH = {'research', 'lecture-notes', 'software-tutorial', 'recruitment-data-research'}

def normalized_url(value):
    """仅连享会文章合并协议、www、追踪尾缀；其他域保留查询语义。"""
    p = urlsplit(value or '')
    if p.scheme in {'http', 'https'} and p.hostname in HOSTS and re.fullmatch(r'/details/\d+\.html', p.path):
        return 'https://www.lianxh.cn' + p.path
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path, p.query, ''))

def screen_post(item):
    """关键词仅预筛；确认的实质研究不因置顶或标题中的关键词排除。"""
    p = urlsplit(item.get('url') or item.get('review', {}).get('source_url', ''))
    source = item.get('source_id') or item.get('review', {}).get('source_id')
    local = p.hostname in HOSTS or (not p.hostname and source in {'lianxh', 'lianxh-posts', 'lianxh.cn'})
    if not local: return dict(action='retain', reason='', evidence='')
    match = re.fullmatch(r'/details/(\d+)\.html', p.path)
    ids = {str(item.get('id', '')).removeprefix('post-')}
    if match: ids.add(match.group(1))
    for key in sorted(ids):
        if key in CONFIRMED:
            reason, evidence = CONFIRMED[key]
            return dict(action='excluded', reason=reason, evidence=evidence)
    c = item.get('content_classification', {})
    trusted = c.get('status') == 'confirmed' and bool(c.get('evidence'))
    if trusted and (c.get('kind') in PROMOTIONS or (c.get('kind') == 'evergreen' and c.get('no_substantive_change') is True)):
        return dict(action='excluded', reason=c['kind'], evidence=c['evidence'])
    if trusted and c.get('kind') in RESEARCH: return dict(action='retain', reason='', evidence=c['evidence'])
    text = item.get('title', '') + ' ' + ' '.join(item.get('tags', []))
    if re.search(r'招生|公开课|助教招聘', text):
        return dict(action='review', reason='推广关键词待正文分类，不能直接排除', evidence='')
    return dict(action='retain', reason='', evidence='')
