"""标签点击复用 Quarto 全站关键词搜索，兼容任意部署子路径。"""
import html
from urllib.parse import quote


def tag_links(values):
    links = []
    for value in dict.fromkeys(values):
        label = html.escape(str(value), quote=True)
        url = '?q=' + quote(str(value), safe='') + '&show-results=1'
        links.append(f'<a class="tag-link" href="{html.escape(url, quote=True)}" title="全站搜索：{label}">{label}</a>')
    return ' · '.join(links)
