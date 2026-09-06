"""使用已有 Playwright 检查真实浏览器布局，不生成图片或发布。"""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / '_site')))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    evidence = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for width in (1440, 768, 375):
                page = browser.new_page(viewport=dict(width=width, height=900))
                page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
                for path in ('/', '/issues/20260905/', '/issues/20260904/', '/archive.html', '/topics/research-frontier.html', '/topics/lianxh-new.html', '/topics/methods-tools.html', '/topics/academic-updates.html', '/topics/index.html'):
                    print(f'CHECK {width} {path}', flush=True)
                    page.goto(base + path, wait_until='domcontentloaded')
                    page.locator('#quarto-content').wait_for()
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, path, '页面溢出')
                    assert page.locator('#quarto-search').count() == 1
                    assert page.locator('a[href]').evaluate_all("els => els.filter(a => /^https?:$/.test(a.protocol) && a.origin !== location.origin).every(a => a.target === '_blank' && a.rel.includes('noopener') && a.rel.includes('noreferrer'))")
                    if width < 992:
                        toggle = page.locator('.navbar-toggler')
                        toggle.click()
                        assert toggle.get_attribute('aria-expanded') == 'true'
                        toggle.click()
                    body = page.locator('body').inner_text()
                    for term in ('公开详版', '微信短版', '查看日期详版'):
                        assert term not in body, (path, term)
                    if path == '/':
                        assert page.locator('.course-hub-callout').count() == 0
                        assert page.locator('.home-promotions .course-poster img').count() == 1
                        assert page.locator('main.content').evaluate("el => !el.querySelector('.home-promotions').nextElementSibling")
                    else:
                        assert page.locator('.course-hub-callout').count() == 1
                    if path.startswith('/topics/') and path != '/topics/index.html':
                        assert '查看栏目索引' not in body
                        assert page.locator('main.content h2:not(#toc-title)').count() == 0
                        assert page.locator('.catalog-card p a').evaluate_all("els => els.every(a => a.textContent === '查看本期')")
                    if path == '/topics/lianxh-new.html':
                        assert page.get_by_role('link',name='lianxh.cn 最新推文',exact=True).get_attribute('href').rstrip('/') == 'https://www.lianxh.cn'
                    if page.locator('section#延伸信息').count():
                        spacing = page.locator('section#延伸信息').evaluate("el => {const s=getComputedStyle(el); return [parseFloat(s.marginTop),parseFloat(s.paddingTop),s.borderTopWidth,s.borderTopColor]}")
                        assert 24 <= spacing[0] <= 32 and 24 <= spacing[1] <= 32 and spacing[2] == '1px', spacing
                    if page.locator('.course-hub-callout').count():
                        assert page.locator('.course-hub-callout').evaluate("el => !['fixed', 'absolute'].includes(getComputedStyle(el).position)")
                        assert page.locator('.course-hub-callout details, .course-hub-callout summary').count() == 0
                        title = page.locator('.course-hub-callout__title')
                        assert title.inner_text() == '最新课程'
                        assert title.evaluate("el => getComputedStyle(el).color") == 'rgb(35, 78, 112)'
                        assert page.locator('.course-hub-callout li').first.is_visible()
                        assert page.locator('.course-dates').first.is_visible()
                    if width >= 1280 and page.locator('.course-hub-callout').count():
                        card = page.locator('.course-hub-callout')
                        assert card.evaluate("el => el.parentElement.id === 'quarto-margin-sidebar'")
                        bounds = card.bounding_box()
                        main = page.locator('main.content').bounding_box()
                        assert bounds['x'] >= main['x'] + main['width'] - 2
                        assert 300 <= bounds['width'] <= 340, bounds
                        assert main['width'] >= 650, main
                        if page.locator('#TOC').count():
                            toc = page.locator('#TOC').bounding_box()
                            assert bounds['y'] >= toc['y'] + toc['height'] - 2
                        # 将卡片增高 500px，验证正文位置不随之移动。
                        before = page.locator('main.content h2:not(#toc-title), main.content .catalog-grid').first.bounding_box()['y']
                        card.evaluate("el => el.style.minHeight = '500px'")
                        after = page.locator('main.content h2:not(#toc-title), main.content .catalog-grid').first.bounding_box()['y']
                        assert abs(after - before) < 1
                        card.evaluate("el => el.style.minHeight = ''")
                    if '/issues/' in path:
                        gap = page.evaluate("document.querySelector('main.content h2:not(#toc-title)').getBoundingClientRect().top - document.querySelector('#title-block-header').getBoundingClientRect().bottom")
                        assert -1 <= gap <= (65 if width >= 1280 else 125), (width, path, gap)
                        assert page.locator('#toc-title').text_content().strip() == '本页目录'
                        assert 'PUBLISHED' not in page.locator('main.content').inner_text()
                    evidence.append(dict(width=width, path=path, layout='PASS'))
                page.close()
            expired = browser.new_page()
            expired.clock.install(time=__import__('datetime').datetime(2026,11,1,12))
            for path, selector in [('/', '.home-promotions'), ('/issues/20260905/', '.course-hub-callout')]:
                expired.goto(base + path, wait_until='domcontentloaded')
                assert expired.locator(selector).is_hidden()
                evidence.append(dict(path=path, cached_expiry='PASS'))
            expired.close()
            browser.close()
    finally:
        server.shutdown()
    out = ROOT / 'logs/task09-small-polish/responsive.json'
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'PASS: {len(evidence)} browser checks; {out}')

if __name__ == '__main__':
    main()
