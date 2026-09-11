"""检查来源 URL 的 HTML 转义与真实参数差异。"""
import tempfile
import unittest
from pathlib import Path
from validate_issue import validate_page

class PageURLTests(unittest.TestCase):
    def check_url(self, rendered):
        issue = dict(date='2026-09-11', status='draft', issue_type='daily',
                     tools=[dict(id='example-tool', priority='core',
                                 url='https://example.org/?a=1&b=2')])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / 'issues/20260911/index.qmd'
            page.parent.mkdir(parents=True)
            page.write_text('## 本期重点\n### 示例 {#example-tool}\n' + rendered, encoding='utf-8')
            errors = []
            validate_page(issue, root, errors)
            return errors

    def test_escaped_query_is_present(self):
        self.assertEqual(self.check_url('https://example.org/?a=1&amp;b=2'), [])

    def test_changed_query_is_rejected(self):
        self.assertTrue(any('URL' in e for e in self.check_url('https://example.org/?a=1&amp;b=3')))

    def test_literal_asterisk_in_heading_and_citation(self):
        from render_issue_pages import escape
        from website_citations import format_myapa
        self.assertEqual(escape('O*NET'), 'O&#42;NET')
        citation = format_myapa(dict(authors=['Example, A.'], year=2026,
            title='O*NET Plus and O*NET', source='Journal'))
        self.assertIn('O&#42;NET Plus and O&#42;NET', citation)
