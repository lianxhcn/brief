"""发现课程不能在排除研究正文之后丢失。"""
import unittest
from datetime import date
from check_course_handoff import check_handoff
from website_promotions import load_config


class CourseHandoffTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 9, 27)
        self.config = load_config()
        self.discovery = dict(retrieved_date='2026-09-27', candidates=[dict(
            url='https://www.lianxh.cn/details/1940.html', source_date='2026-09-24')])

    def test_new_course_reaches_approved_config(self):
        self.assertTrue(check_handoff(self.discovery, self.config, self.today)['passed'])

    def test_missing_course_is_not_silent(self):
        self.config['approved_courses'] = []
        result = check_handoff(self.discovery, self.config, self.today)
        self.assertFalse(result['passed'])
        self.assertEqual(len(result['pending']), 1)

    def test_stale_discovery_and_invalid_dates_fail(self):
        self.discovery['retrieved_date'] = '2026-09-26'
        self.assertFalse(check_handoff(self.discovery, self.config, self.today)['passed'])
        self.discovery['retrieved_date'] = '2026-09-27'
        for item in self.config['approved_courses']:
            item['course_end_date'] = 'unknown'
        self.assertFalse(check_handoff(self.discovery, self.config, self.today)['passed'])

    def test_pending_review_does_not_count_as_completed(self):
        for item in self.config['approved_courses']:
            item['review_status'] = 'pending'
        self.assertFalse(check_handoff(self.discovery, self.config, self.today)['passed'])

    def test_historical_candidates_do_not_require_new_promotion(self):
        self.config['approved_courses'] = []
        self.discovery['candidates'][0]['source_date'] = '2026-05-01'
        self.assertTrue(check_handoff(self.discovery, self.config, self.today)['passed'])
