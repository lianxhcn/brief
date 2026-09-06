"""R03 本地搜索只验收生成索引与脚本资产，真实交互留至 post-deploy。"""
import json,re,unittest
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]

class SearchIndexTests(unittest.TestCase):
    def test_formal_content_and_demo_isolation(self):
        data=json.loads((ROOT/'_site/search.json').read_text(encoding='utf-8'))
        text=json.dumps(data,ensure_ascii=False)
        self.assertIn('binsreg',text.lower())
        self.assertIn('20260905',text)
        self.assertIn('20260904',text)
        self.assertNotIn('DEMO',text.upper())
        self.assertNotIn('209901',text)

    def test_local_search_assets_exist(self):
        page=ROOT/'_site/issues/20260905/index.html'
        source=page.read_text(encoding='utf-8')
        assets=re.findall(r'<script[^>]+src="([^"]+)"',source)
        search=[a for a in assets if 'quarto-search' in a]
        self.assertTrue(search)
        for asset in assets:
            if urlsplit(asset).scheme:continue
            target=(page.parent/unquote(urlsplit(asset).path)).resolve()
            self.assertTrue(target.is_file(),asset)
            self.assertGreater(target.stat().st_size,0)

if __name__=='__main__':unittest.main()
