"""读者文案清理不改事实、日期精度、摘要来源和方法边界。"""
import copy
import unittest
from unittest.mock import patch
from build_catalog_pages import public_issues
from public_history import collections, render_collection
from render_issue_pages import render_page
from website_content import fingerprint, public_summary, reader_text_errors


class ReaderHygieneTests(unittest.TestCase):
    def test_internal_work_notes_are_rejected_without_keyword_overreach(self):
        for text in ('本期不足 9 条：内部原因', '补录：2026-11-09',
                     '收录日期：2026-11-09', '本轮只核摘要，未运行。',
                     '本轮完整读 help，未核数值。', '本期阅读摘要。',
                     '查看本期核验记录。', '查看本期阅读原文。本期阅读摘要。'):
            self.assertTrue(reader_text_errors(text), text)
        for text in ('软件开发与工作论文；维护者说明修复了误差，因果识别仍需假设。',
                     '本期核心算法使用工具变量。', '本期读者可以按关键词查找。',
                     '查看本期阅读原文'):
            self.assertEqual(reader_text_errors(text), [])
        item = {'id': 'fixture'}
        record = {'fixture': {'source_sha256': fingerprint(item), 'summary': '本期未实测。'}}
        with patch('website_content.json.loads', return_value=record):
            with self.assertRaises(ValueError):
                public_summary(item)

    def test_all_public_issues_hide_work_metadata_and_keep_items(self):
        for issue in public_issues():
            before = copy.deepcopy(issue)
            page = render_page(issue)
            self.assertEqual(reader_text_errors(page), [], issue['date'])
            self.assertNotIn('backfill-note', page)
            self.assertEqual(issue, before)
            for category in ('lianxh_posts','papers','tools','research_resources','conference_calls'):
                for item in issue.get(category, []):
                    self.assertIn('{#' + item['id'] + '}', page)
                    source_date = item.get('published_date') or item.get('release_date')
                    if item.get('added_date') and source_date and source_date != 'unknown':
                        self.assertIn('来源日期：' + source_date, page)

    def test_history_hides_maintenance_dates_and_keeps_sources(self):
        for slug, data in collections():
            before = copy.deepcopy(data)
            page = render_collection(data)
            self.assertEqual(reader_text_errors(page), [], slug)
            self.assertNotIn('栏目索引中仅计一次', page)
            for row in data['entries']:
                self.assertIn('来源日期：' + row['source_date'], page)
            self.assertEqual(data, before)


if __name__ == '__main__':
    unittest.main()
