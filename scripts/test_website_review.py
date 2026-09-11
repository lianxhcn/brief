"""R01 公开正文、栏目命名和 QA 保留的回归测试。"""
import copy
import json
import re
import unittest
from pathlib import Path
from datetime import date
from build_catalog_pages import public_issues, home_page, archive_page, SECTIONS
from render_issue_pages import render_page, escape
from website_content import public_summary, INTERNAL_PHRASES
from website_promotions import load_config, render_promotion

ROOT = Path(__file__).resolve().parents[1]

class UserReviewTests(unittest.TestCase):
    def test_public_hygiene_and_original_metadata(self):
        for issue in public_issues():
            original = copy.deepcopy(issue)
            page = render_page(issue)
            for value in (*INTERNAL_PHRASES, '## 状态', '生态：', '名称：'):
                self.assertNotIn(value, page)
            self.assertEqual(issue, original)
            self.assertIn('retrieved_date', issue)
            self.assertEqual(page.count(issue['date'].replace('-', '.')), 1)

    def test_hierarchy_and_stable_anchors(self):
        for issue in public_issues():
            page = render_page(issue)
            self.assertIn('## 本期重点', page)
            for key, label in [('papers', '新论文'), ('tools', '新方法'), ('conference_calls', '会议征稿')]:
                if issue.get(key):
                    self.assertIn(f'### {label}', page)
                    for item in issue[key]:
                        self.assertIn(f"#### {escape(item['title'])} {{#{item['id']}}}", page)

    def test_summary_changes_need_review(self):
        item = copy.deepcopy(public_issues()[0]['papers'][0])
        item['page_note'] += ' new evidence'
        with self.assertRaises(ValueError):
            public_summary(item)

    def test_compact_courses(self):
        config = load_config()
        config['approved_courses'] *= 4
        text = render_promotion(config, date(2026, 9, 6))
        self.assertEqual(text.count('<li '), 1)
        self.assertIn('10/17、10/24、10/31', text)
        for value in ('以官网为准', 'review_status', '抓取', 'blogs/44', 'KC.html'):
            self.assertNotIn(value, text)
        config['approved_courses'][0]['dates'] = []
        self.assertEqual(render_promotion(config, date(2026, 9, 6)), '')

    def test_archive_single_date(self):
        # 固定两期输入，归档标签测试不依赖生产期次数量。
        fixtures = [dict(date='2026-09-05'), dict(date='2026-09-04')]
        labels = re.findall(r'<li><a[^>]*>([^<]+)</a></li>', archive_page(fixtures))
        self.assertEqual(labels, ['连享会 · 快讯 | 2026.09.05', '连享会 · 快讯 | 2026.09.04'])

    def test_nav_and_cards(self):
        home = home_page(public_issues())
        config = (ROOT / '_quarto.yml').read_text(encoding='utf-8')
        self.assertIn('toc-title: 本页目录', config)
        for _, label, description in SECTIONS:
            self.assertIn('text: ' + label, config)
            self.assertIn('>' + label + '</a>', home)
            self.assertNotIn(description, home)

if __name__ == '__main__':
    unittest.main()
