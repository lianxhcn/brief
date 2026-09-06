"""网站课程实体：人工审核后展示；完整日期控制排序、去重和到期隐藏。"""
import html
import json
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from website_citations import external_link, safe_url

CONFIG = Path(__file__).resolve().parents[1] / 'config/promotions.json'


def load_config():
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    if config['course_source'] != 'https://www.lianxh.cn/blogs/44.html':
        raise ValueError('课程候选来源不符合 U-07')
    if config['course_hub'] != 'https://www.lianxh.cn/KC.html':
        raise ValueError('课程综合入口无效')
    if config['subscription'] != {'status': 'pending', 'enabled': False}:
        raise ValueError('订阅方案尚待裁定')
    return config


def current_date():
    return datetime.now(ZoneInfo('Asia/Shanghai')).date()


def iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('必须保存完整年月日')
    return date.fromisoformat(value)


def active_courses(config=None, today=None):
    """只消费已确认实体，不联网、不修改稳定配置；异常记录保持待人工审核。"""
    config = load_config() if config is None else config
    today = current_date() if today is None else today
    groups = {}
    for item in config.get('approved_courses', []):
        # 别名由人工确认，不能凭标题相似推断为同一课程。
        identity = item.get('id')
        if not identity:
            continue
        groups.setdefault(identity, []).append(item)
    courses = []
    for identity, records in groups.items():
        normalized = []
        for item in records:
            try:
                if (item.get('review_status') != 'approved' or
                    item.get('status') != 'confirmed' or
                    not item.get('reviewed_date') or not safe_url(item.get('source_url')) or
                    not item.get('evidence') or not item.get('title')):
                    raise ValueError('缺少可靠审核证据')
                dates = sorted(set(iso_date(value) for value in item['dates']))
                start, end = iso_date(item['course_start_date']), iso_date(item['course_end_date'])
                if not dates or start != dates[0] or end != dates[-1]:
                    raise ValueError('授课日期与起止日期冲突')
                # unavailable 必须有人工核验依据；网络失败不自动把详情标为不可用。
                links = [link for link in item.get('links', [])
                         if link.get('availability') == 'confirmed' and safe_url(link.get('url'))]
                links.sort(key=lambda link: (not bool(re.search(r'/details/\d+\.html$', link['url'])), link['url']))
                if not links:
                    raise ValueError('没有确认可用的安全链接')
                normalized.append(dict(item, url=links[0]['url'], dates=[d.isoformat() for d in dates]))
            except (ValueError, KeyError, TypeError):
                normalized = []
                break
        if not normalized:
            continue
        # 同实体的事实冲突时不挑一份猜测；链接别名差异允许合并。
        fields = ('title', 'dates', 'course_start_date', 'course_end_date', 'status', 'poster')
        if any(any(record.get(k) != normalized[0].get(k) for k in fields) for record in normalized):
            continue
        item = min(normalized, key=lambda i: (not bool(re.search(r'/details/\d+\.html$', i['url'])), i['url']))
        future = [value for value in item['dates'] if iso_date(value) >= today]
        if not future:
            continue
        courses.append(dict(item, next_date=future[0]))
    return sorted(courses, key=lambda i: (i['next_date'], i['id']))[:3]


def attributes(item):
    # 浏览器再次按中国日期隐藏过期推广，避免静态构建缓存一直展示旧课程。
    values = {'course-id': item['id'], 'course-start': item['course_start_date'],
              'course-end': item['course_end_date'], 'course-status': item['status']}
    return ' '.join(f'data-{key}="{html.escape(value, quote=True)}"' for key, value in values.items())


def dates_text(item):
    return '、'.join(iso_date(value).strftime('%m/%d') for value in item['dates'])


def render_promotion(config=None, today=None):
    courses = active_courses(config, today)
    if not courses:
        return ''
    rows = [f'<li {attributes(item)}>' + external_link(item['title'], item['url']) +
            f'<span class="course-dates">{html.escape(dates_text(item))}</span></li>' for item in courses]
    return ('<div class="promotion-slot"><div class="course-hub-callout" role="complementary" aria-label="近期课程">'
            '<details><summary>近期课程</summary><ul>' + ''.join(rows) + '</ul></details></div></div>')


def render_home_promotion(config=None, today=None):
    cards = []
    for item in active_courses(config, today):
        if not safe_url(item.get('poster')):
            continue
        cards.append(f'<figure class="course-poster" {attributes(item)}>'
                     f'<a href="{html.escape(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer">'
                     f'<img src="{html.escape(item["poster"], quote=True)}" alt="{html.escape(item["title"], quote=True)}：'
                     f'{html.escape("、".join(item["dates"]))}" width="1200" height="540" loading="lazy"></a></figure>')
    return '<div class="home-promotions">' + ''.join(cards) + '</div>' if cards else ''
