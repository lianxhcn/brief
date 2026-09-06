"""Task 09 网站单元测试，覆盖缺失元数据、隔离与安全降级。"""
import copy
import json
import unittest
from pathlib import Path
from urllib.parse import unquote
from website_citations import format_myapa, website_citation
from website_promotions import load_config, render_promotion
from discover_courses import parse_courses
from render_issue_pages import render_page
from build_catalog_pages import home_page, archive_page, public_issues, entries, DISPLAY_LABELS
from site_config import is_public_issue

ROOT = Path(__file__).resolve().parents[1]

class CitationTests(unittest.TestCase):
    def fixture(self):
        return dict(authors=['Alpha, A.', 'Beta, B.', 'Gamma, C.'], year=2026,
                    title='A title: Evidence & uncertainty?', source='Journal', volume='12', issue='3', pages='1–20')

    def test_complete_and_encoding(self):
        m = self.fixture()
        m['doi_url'] = 'https://doi.org/10.1234/example'
        m['homepage_url'] = 'https://example.org/paper'
        out = format_myapa(m)
        self.assertIn('Alpha, A., Beta, B., &amp; Gamma, C.', out)
        self.assertIn('Journal, 12(3), 1–20.', out)
        self.assertIn('Evidence &amp; uncertainty?', out)
        self.assertIn('q=A%20title%3A%20Evidence%20%26%20uncertainty%3F', out)
        self.assertNotIn('https://example.org/paper', out)

    def test_missing_and_forthcoming(self):
        for status in ('forthcoming', 'working-paper', 'published'):
            m = self.fixture()
            for field in ('volume', 'issue', 'pages'):
                del m[field]
            m['publication_status'] = status
            out = format_myapa(m)
            self.assertNotIn('>PDF<', out)
            self.assertNotIn('>Link<', out)
            self.assertNotIn('None', out)
            self.assertEqual('(forthcoming)' in out, status == 'forthcoming')

    def test_pdf_requires_evidence(self):
        m = self.fixture()
        m['pdf'] = dict(url='https://example.org/paper.pdf')
        self.assertNotIn('>PDF<', format_myapa(m))
        m['pdf'].update(public_access=True, retrieved_date='2026-09-05', source_url='https://example.org/research')
        self.assertIn('>PDF<', format_myapa(m))
        m['pdf']['url'] = 'https://doi.org/10.1234/example'
        self.assertNotIn('>PDF<', format_myapa(m))
        m['pdf']['url'] = 'javascript:alert(1)'
        self.assertNotIn('javascript:', format_myapa(m))

    def test_real_papers_and_no_mutation(self):
        issue = json.loads((ROOT / 'content/issues/2026-09-05.json').read_text(encoding='utf-8'))
        original = copy.deepcopy(issue)
        self.assertEqual(render_page(issue).count('class="myapa"'), 3)
        self.assertEqual(issue, original)
        for p in issue['papers']:
            self.assertIn('>Google<', website_citation(p))

    def test_unknown_metadata_fails_closed(self):
        with self.assertRaises(ValueError):
            website_citation(dict(id='unreviewed'))

class WebsiteTests(unittest.TestCase):
    def test_demo_metadata_and_public_lists(self):
        for path in (ROOT / 'content/issues').glob('*demo*.json'):
            issue = json.loads(path.read_text(encoding='utf-8'))
            self.assertFalse(is_public_issue(issue))
            page = render_page(issue)
            self.assertIn('search: false', page)
            self.assertIn('sitemap: false', page)
        issues = public_issues()
        for text in (home_page(issues), archive_page(issues), str(entries(issues))):
            self.assertNotIn('2099', text)
            self.assertNotIn('DEMO', text)

    def test_home_bounded_and_archive_sorted(self):
        issues = [dict(date=f'2026-09-{i:02}', title=f'期次{i}') for i in range(30, 0, -1)]
        self.assertEqual(home_page(issues).count('](issues/'), 1)
        self.assertEqual(archive_page(issues).count('](issues/'), 30)
        self.assertLess(archive_page(issues).index('2026-09-30'), archive_page(issues).index('2026-09-01'))
        self.assertEqual(set(DISPLAY_LABELS.values()), {'新推文', '新论文', '新方法', '会议征稿'})

    def test_promotion_review_boundary(self):
        c = load_config()
        c['approved_courses'] = [dict(title='不应出现', url='https://example.org')]
        out = render_promotion(c)
        self.assertNotIn('不应出现', out)
        self.assertEqual(out, '')  # 未审核候选不产生推广卡片
        self.assertNotIn('<form', out)

    def test_course_parser(self):
        html = '<title>专题课程 | 连享会</title><a href="/details/1900.html"><h5>数据分析</h5>2026-08-25</a>'
        result = parse_courses(html, '2026-09-06')
        self.assertEqual(result['review_status'], 'pending')
        self.assertEqual(result['candidates'][0]['source_date'], '2026-08-25')
        self.assertNotIn('正在报名', str(result))
        for invalid in ('<title>Error</title>', html.replace('数据分析', '公开课')):
            with self.assertRaises(ValueError):
                parse_courses(invalid, '2026-09-06')

if __name__ == '__main__':
    unittest.main()
