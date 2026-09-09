"""论文政策正反例；example.org 仅为测试夹具。"""
import copy
import unittest
from paper_policy import POLICY, paper_policy_errors
from editorial_rules import check_editorial


def fixture():
    def row(source):
        return dict(source=source, status='no-eligible', checked_at='2026-09-10',
                    window_start='2026-08-27', window_end='2026-09-10',
                    evidence_url='https://example.org/test', candidate_ids=[], reason='测试夹具')
    return dict(date='2026-09-10', issue_type='daily', status='draft', papers=[],
                paper_review=dict(journal_checks=[row(s) for names in POLICY['top_journal_groups'].values() for s in names],
                                  working_paper_checks=[row(s) for s in POLICY['working_paper_sources']]))


class PolicyTests(unittest.TestCase):
    def test_complete_and_missing_coverage(self):
        issue = fixture()
        self.assertEqual(paper_policy_errors(issue), [])
        issue['paper_review']['journal_checks'] = []
        self.assertTrue(paper_policy_errors(issue))

    def test_failure_stale_and_unsearched(self):
        for change in ({'status': 'not-searched'}, {'status': 'access-failed'}, {'checked_at': '2026-09-01'}):
            issue = fixture()
            issue['paper_review']['journal_checks'][0].update(change)
            self.assertTrue(paper_policy_errors(issue))

    def test_formal_identity_requires_evidence(self):
        issue = fixture()
        p = dict(id='p1', priority='core', journal='The Quarterly Journal of Economics', publication_status='working-paper', working_paper_source='arXiv')
        issue['papers'] = [p]
        self.assertTrue(paper_policy_errors(issue))
        p['publication_status'] = 'published'
        self.assertTrue(paper_policy_errors(issue))
        p['publication_evidence_url'] = 'https://example.org/article'
        self.assertEqual(paper_policy_errors(issue), [])

    def test_exception_cannot_bypass_coverage(self):
        issue = fixture()
        issue['papers'] = [dict(id='p1', priority='core', publication_status='working-paper', working_paper_source='NBER')]
        issue['paper_review']['composition_exception'] = dict(code='no-eligible', reason='测试原因', reviewed_by='test', compared_candidate_ids=[], selected_paper_ids=['p1'])
        self.assertEqual(paper_policy_errors(issue), [])
        issue['paper_review']['journal_checks'] = []
        self.assertTrue(paper_policy_errors(issue))

    def test_platform_concentration(self):
        issue = fixture()
        issue['papers'] = [dict(id=str(i), priority='extended', publication_status='working-paper', working_paper_source='arXiv') for i in range(4)]
        self.assertTrue(paper_policy_errors(issue))
        issue['paper_review']['extended_composition_exception'] = dict(reason='测试不足', reviewed_by='test', compared_candidate_ids=[], replacement_paper_ids=['0', '1'])
        issue['paper_review']['source_balance_review'] = dict(reason='测试比较', reviewed_by='test', compared_sources=['NBER', 'arXiv'])
        self.assertEqual(paper_policy_errors(issue), [])

    def test_extended_half_target_and_shortage(self):
        issue = fixture()
        issue['papers'] = [dict(id='a', priority='extended', publication_status='published', journal='Econometrica', publication_evidence_url='https://example.org/article'), dict(id='b', priority='extended', publication_status='working-paper', working_paper_source='NBER')]
        self.assertEqual(paper_policy_errors(issue), [])
        issue['papers'].append(dict(id='c', priority='extended', publication_status='working-paper', working_paper_source='arXiv'))
        self.assertTrue(paper_policy_errors(issue))
        issue['paper_review']['extended_composition_exception'] = dict(reason='测试顶刊不足', reviewed_by='test', compared_candidate_ids=['a'], replacement_paper_ids=['c'])
        self.assertEqual(paper_policy_errors(issue), [])
        issue['paper_review']['journal_checks'] = []
        self.assertTrue(paper_policy_errors(issue))

    def test_historical_compatibility_and_shared_gate(self):
        issue = dict(date='2026-09-09', issue_type='daily', status='published')
        self.assertEqual(paper_policy_errors(issue), [])
        issue['date'] = '2026-09-10'
        self.assertTrue(check_editorial(issue))
        issue['date'] = '2026-09-09'
        issue['paper_policy_version'] = 1
        self.assertTrue(check_editorial(issue))

if __name__ == '__main__':
    unittest.main()
