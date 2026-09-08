"""分页边界、跨页完整性和过期生成文件的回归检查。"""
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build_catalog_pages as catalog


class PaginationTests(unittest.TestCase):
    def rows(self, count, section='lianxh-new'):
        return [dict(id=f'item-{i}', date='2026-09-08', title=f'Title {i}',
                     note='Summary', section=section,
                     catalog=dict(software=[], methods=[], fields=[], tags=[]))
                for i in range(count)]

    def test_boundaries_without_hidden_extra_cards(self):
        for count in (0, 1, 10, 11, 20, 21, 101):
            with self.subTest(count=count):
                rows = self.rows(count)
                outputs = catalog.catalog_outputs([], rows)
                pages = [outputs['topics/' + catalog.page_name('lianxh-new', n)]
                         for n in range(1, catalog.page_count(rows) + 1)]
                found = []
                for page in pages:
                    self.assertLessEqual(page.count('<article class="catalog-card">'), 10)
                    self.assertNotIn('catalog-filter', page)
                    found += re.findall(r'href="../issues/20260908/#(item-\d+)"', page)
                self.assertEqual(found, [r['id'] for r in rows])

    def test_navigation_and_first_page_url(self):
        rows = self.rows(21)
        outputs = catalog.catalog_outputs([], rows)
        first = outputs['topics/lianxh-new.qmd']
        middle = outputs['topics/lianxh-new-2.qmd']
        last = outputs['topics/lianxh-new-3.qmd']
        self.assertNotIn('rel="prev"', first)
        self.assertIn('rel="next" href="lianxh-new-2.html"', first)
        self.assertIn('rel="prev" href="lianxh-new.html"', middle)
        self.assertNotIn('rel="next"', last)
        self.assertIn('第 3 / 3 页 · 共 21 条', last)
        with self.assertRaises(ValueError):
            catalog.page_slice(rows, 4)

    def test_all_sections_paginate_independently(self):
        rows = [r for key, _, _ in catalog.SECTIONS for r in self.rows(11, key)]
        outputs = catalog.catalog_outputs([], rows)
        for key, _, _ in catalog.SECTIONS:
            self.assertEqual(outputs[f'topics/{key}.qmd'].count('<article '), 10)
            self.assertEqual(outputs[f'topics/{key}-2.qmd'].count('<article '), 1)

    def test_archive_month_boundary_and_latest_three(self):
        dates = [f'2026-09-{i:02d}' for i in range(8, 0, -1)] + [f'2026-08-{i:02d}' for i in range(31, 18, -1)]
        issues = [dict(date=d, title=d) for d in dates]
        outputs = catalog.catalog_outputs(issues, [])
        page = outputs['archive.qmd']
        self.assertNotIn('archive-2.qmd', outputs)
        self.assertEqual(re.findall(r'href="issues/(\d{8})/"', page), [d.replace('-', '') for d in dates])
        self.assertEqual(page.count('class="archive-month"'), 2)
        self.assertEqual(page.count('class="archive-month" open'), 2)
        self.assertNotIn('第 1 / 1 页', page)
        from site_config import issue_title
        self.assertEqual(re.findall(r'^- \[([^]]+)\]', outputs['index.qmd'], re.M), [issue_title(d) for d in dates[:3]])

    def test_archive_cross_year_no_split_or_loss(self):
        dates = [f'{y}-{m:02d}-01' for y in (2026, 2025, 2024) for m in range(12, 0, -1)]
        issues = [dict(date=d) for d in reversed(dates)]
        # 归档自身保证日期倒序；首页由 public_issues 提供有序输入。
        pages = [catalog.archive_page(issues, n) for n in (1, 2, 3)]
        found = [d for page in pages for d in re.findall(r'href="issues/(\d{8})/"', page)]
        self.assertEqual(found, [d.replace('-', '') for d in dates])
        for page in pages:
            self.assertEqual(page.count('class="archive-month"'), 12)
        self.assertIn('href="archive-2.html"', pages[0])
        self.assertIn('href="archive.html"', pages[1])
        with self.assertRaises(ValueError): catalog.archive_page(issues, 4)

    def test_shared_title_ignores_legacy_title(self):
        from site_config import issue_title
        from render_issue_pages import render_page
        import copy
        issue = copy.deepcopy(catalog.public_issues()[-1])
        issue['title'] = '旧标题不应显示'
        for text in (catalog.home_page([issue]), catalog.archive_page([issue]), render_page(issue)):
            self.assertIn(issue_title(issue), text)
            self.assertNotIn(issue['title'], text)

    def test_tag_links_encode_special_characters(self):
        from website_tags import tag_links
        from urllib.parse import parse_qs, urlsplit
        import html
        tags = ['双重差分', 'R&D / <test> + C++']
        links = tag_links(tags)
        urls = re.findall(r'href="([^"]+)"', links)
        self.assertEqual([parse_qs(urlsplit(html.unescape(u)).query)['q'][0] for u in urls], tags)
        self.assertNotIn('<test>', links)
        self.assertEqual(len(re.findall(r'href=', tag_links(['CCE', 'CCE']))), 1)
        self.assertIn('show-results=1', links)

    def test_archive_auto_expand_threshold(self):
        from datetime import date, timedelta
        def issues(n):
            return [dict(date=(date(2026, 9, 1) + timedelta(days=i)).isoformat()) for i in range(n)]
        self.assertIn('class="archive-month" open', catalog.archive_page(issues(31)))
        self.assertNotIn('class="archive-month" open', catalog.archive_page(issues(32)))
        self.assertNotIn('class="archive-month" open', catalog.archive_page([dict(date='2026-01-01'), dict(date='2025-12-31')]))

    def test_stale_page_ownership(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(catalog, 'ROOT', root):
                owned = root / 'archive-2.qmd'
                owned.write_text(catalog.GENERATED_MARKER, encoding='utf-8')
                self.assertEqual(catalog.stale_catalog_pages({}), [owned])
                self.assertEqual(catalog.stale_catalog_pages({'archive-2.qmd': ''}), [])
                owned.write_text('Manual content', encoding='utf-8')
                with self.assertRaises(ValueError):
                    catalog.stale_catalog_pages({})


if __name__ == '__main__':
    unittest.main()
