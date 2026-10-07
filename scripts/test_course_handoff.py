"""发现课程不能在排除研究正文之后丢失。"""
import unittest
from datetime import date
from check_course_handoff import check_handoff


class CourseHandoffTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 9, 27)
        # 固定测试夹具不读取每日变动的推广配置，避免审核日更新破坏历史用例。
        link = 'https://www.lianxh.cn/details/1940.html'
        self.config = dict(approved_courses=[dict(
            id='llm-agent-2026', title='LLM × Agent', url=link,
            source_url=link, evidence='测试夹具：已核验课程',
            reviewed_date='2026-09-27', review_status='approved', status='confirmed',
            dates=['2026-11-28', '2026-11-29'],
            course_start_date='2026-11-28', course_end_date='2026-11-29',
            links=[dict(url=link, availability='confirmed')])])
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
