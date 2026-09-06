"""R03：实际目录的断点、键盘、导航、状态与重复移动回归。"""
import json, threading
from pathlib import Path
from functools import partial
from urllib.parse import unquote
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT/'_site')))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    results=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            for path in ('/','/issues/20260905/','/issues/20260904/','/archive.html','/topics/index.html','/topics/lianxh-new.html'):
                page=browser.new_page(viewport={'width':1440,'height':900})
                errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.route('**/*',lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
                page.goto(base+path,wait_until='networkidle')
                toc=page.locator('#TOC')
                if not toc.count():
                    assert page.locator('.inline-toc').count()==0
                    results.append(dict(path=path,empty_toc='no invented menu',status='PASS'))
                    page.close();continue
                original=toc.locator('a[data-scroll-target]').evaluate_all('els=>els.map(e=>({href:e.hash,label:e.textContent}))')
                page.evaluate('window.originalToc = document.getElementById("TOC")')
                for width in (1440,1280,1279,768,375,1440):
                    print('TOC',path,width,flush=True)
                    page.set_viewport_size({'width':width,'height':900})
                    details=page.locator('.inline-toc');summary=details.locator('summary')
                    if width>=1280:
                        expect(details).to_be_hidden()
                        expect(page.locator('#quarto-margin-sidebar #TOC')).to_be_visible()
                    else:
                        expect(details).to_be_visible()
                        expect(page.locator('#quarto-margin-sidebar')).to_be_hidden()
                        expect(summary).to_have_attribute('aria-expanded','false')
                        assert details.evaluate('el=>!["fixed","absolute","sticky"].includes(getComputedStyle(el).position)')
                        assert details.evaluate('el=>el.previousElementSibling.id==="title-block-header" || el.previousElementSibling.classList.contains("brief-cover")')
                        # 原生 summary 可用鼠标、Enter 与 Space 操作，状态须同步。
                        summary.click();expect(summary).to_have_attribute('aria-expanded','true')
                        summary.click();expect(summary).to_have_attribute('aria-expanded','false')
                        summary.focus();summary.press('Enter');expect(summary).to_have_attribute('aria-expanded','true')
                        summary.press('Space');expect(summary).to_have_attribute('aria-expanded','false')
                        for i,entry in enumerate(original):
                            summary.click()
                            link=toc.locator('a[data-scroll-target]').nth(i)
                            expect(link).to_be_visible()
                            if i==0: link.focus();link.press('Enter')
                            else: link.click()
                            expect(summary).to_have_attribute('aria-expanded','false')
                            target_id=unquote(entry['href'][1:])
                            page.wait_for_function('(id)=>decodeURIComponent(location.hash.slice(1))===id',arg=target_id)
                            # 跳转后标题必须在导航下方，并有键盘焦点；不靠 force 点击。
                            page.wait_for_function('''id=>{
                              const target=document.getElementById(id);
                              const h=target.matches('h1,h2,h3,h4')?target:target.querySelector('h1,h2,h3,h4');
                              const r=h.getBoundingClientRect();
                              const header=document.getElementById('quarto-header').getBoundingClientRect();
                              return document.activeElement===h && r.top>=Math.max(header.bottom,0)-1 && r.top<innerHeight;
                            }''',arg=target_id,timeout=5000)
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                    assert toc.locator('a[data-scroll-target]').evaluate_all('els=>els.map(e=>({href:e.hash,label:e.textContent}))')==original
                    assert page.evaluate('document.getElementById("TOC")===window.originalToc')
                    assert page.locator('#TOC').count()==1
                    results.append(dict(path=path,width=width,anchors=len(original),status='PASS'))
                assert not errors,errors
                page.close()
            browser.close()
    finally: server.shutdown()
    (ROOT/'logs/task09-r03/toc-checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS:',len(results),'TOC cases')

if __name__=='__main__':main()
