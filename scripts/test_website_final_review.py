"""R02 网站推广的实体、日期、异常与跨页面一致性回归。"""
import copy
import contextlib
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
import discover_courses
from website_promotions import active_courses, load_config, render_promotion, render_home_promotion
from build_catalog_pages import section_page, entries, public_issues, home_page, archive_page

TODAY = date(2026, 9, 6)

class FinalReviewTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.course = copy.deepcopy(self.config['approved_courses'][0])

    def selected(self):
        return active_courses(self.config, TODAY)

    def test_alias_dedupe_and_details_priority(self):
        alias = copy.deepcopy(self.course)
        alias['links'] = [alias['links'][0]]
        self.config['approved_courses'] = [alias, self.course]
        result = self.selected()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['url'], 'https://www.lianxh.cn/details/1900.html')

    def test_unavailable_details_safe_fallback(self):
        self.config['approved_courses'][0]['links'][1]['availability'] = 'unavailable'
        self.assertEqual(self.selected()[0]['url'], 'https://www.lianxh.cn/aic.html')
        self.config['approved_courses'][0]['links'][0]['url'] = 'javascript:alert(1)'
        self.assertEqual(self.selected(), [])

    def test_nearest_remaining_session_sort_and_limit(self):
        courses = []
        for i, values in enumerate((['2026-08-01','2026-10-01'], ['2026-09-30'], ['2026-09-06'], ['2026-09-07'])):
            course = dict(self.course, id=f'course-{i}', dates=values, course_start_date=values[0], course_end_date=values[-1])
            courses.append(course)
        self.config['approved_courses'] = courses
        self.assertEqual([c['id'] for c in self.selected()], ['course-2','course-3','course-1'])

    def test_final_day_inclusive_then_hidden_both_renderers(self):
        for renderer in (render_promotion, render_home_promotion):
            self.assertTrue(renderer(self.config, date(2026,10,31)))
            self.assertEqual(renderer(self.config, date(2026,11,1)), '')

    def test_bad_dates_and_missing_evidence_do_not_mutate(self):
        for field, value in [('dates', []), ('dates', ['10/17']), ('dates', ['2026-02-30']),
                             ('course_end_date', ''), ('course_end_date','2026-10-24'),
                             ('source_url',''), ('review_status','pending'), ('status','registering')]:
            with self.subTest(field=field,value=value):
                config = copy.deepcopy(self.config)
                config['approved_courses'][0][field] = value
                before = copy.deepcopy(config)
                self.assertEqual(active_courses(config, TODAY), [])
                self.assertEqual(config, before)

    def test_conflicting_entity_is_hidden(self):
        duplicate = dict(self.course, title='Unconfirmed new title')
        self.config['approved_courses'].append(duplicate)
        self.assertEqual(self.selected(), [])

    def test_fetch_failure_keeps_stable_config_but_expires(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            stable=root/'config/promotions.json'; stable.parent.mkdir()
            stable.write_text(json.dumps(self.config),encoding='utf-8')
            before=stable.read_bytes()
            with patch.object(discover_courses,'ROOT',root), patch('sys.argv',['discover_courses.py']), patch.object(discover_courses,'urlopen',side_effect=OSError('offline')), contextlib.redirect_stdout(io.StringIO()) as log:
                self.assertEqual(discover_courses.main(),1)
            self.assertIn('FAILURE',log.getvalue())
            self.assertEqual(stable.read_bytes(),before)
            cached=json.loads(stable.read_text(encoding='utf-8'))
            self.assertTrue(active_courses(cached,TODAY))
            self.assertEqual(active_courses(cached,date(2026,11,1)),[])

    def test_home_sidebar_share_entity(self):
        home=render_home_promotion(self.config,TODAY)
        side=render_promotion(self.config,TODAY)
        for field in ('id','course_start_date','course_end_date','status'):
            self.assertIn(self.course[field],home)
            self.assertIn(self.course[field],side)
        for value in (self.course['title'],self.course['url']):
            self.assertIn(value,home)
            self.assertIn(value,side)
        self.assertIn(self.course['poster'],home)
        self.assertNotIn('course-hub-callout',home)

    def test_topic_cleanup_and_terminology(self):
        values=entries(public_issues())
        page=section_page('新推文','redundant',values)
        for old in ('## 条目','查看栏目索引','查看日期详版','redundant'):
            self.assertNotIn(old,page)
        self.assertIn('href="https://www.lianxh.cn"',page)
        self.assertEqual(page.count('lianxh.cn 最新推文'),1)
        self.assertIn('>查看本期</a>',page)
        for text in (home_page(public_issues()),archive_page(public_issues())):
            self.assertNotIn('公开详版',text)
            self.assertNotIn('微信短版',text)
        self.assertIn('微信群版',home_page(public_issues()))

if __name__ == '__main__':
    unittest.main()
