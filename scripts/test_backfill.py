"""Backfill dates must stay factual without weakening ordinary daily checks."""
import copy
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from editorial_desk import Desk, publication_moment, write
from editorial_rules import check_editorial
from issue_dates import issue_date_errors, review_date
from paper_policy import paper_policy_errors
from render_issue_pages import render_page
from test_editorial_rules import fixture as editorial_fixture
from test_isolated_trial import ASOF, verified
from test_paper_policy import fixture as policy_fixture
from trial_selection import selection_errors
from website_rules import check_website


def backfill_fixture():
    issue = editorial_fixture()
    issue['backfill'] = dict(prepared_date='2026-09-08', reason='迁移期间补刊')
    issue['retrieved_date'] = '2026-09-08'
    for category in ('lianxh_posts', 'papers', 'tools'):
        for item in issue[category]:
            item['retrieved_date'] = item['added_date'] = '2026-09-08'
            if category == 'lianxh_posts':
                item['published_date'] = '2026-09-04'
            elif category == 'papers':
                item['published_date'] = '2026-08-20'
    return issue


class BackfillDateTests(unittest.TestCase):
    def test_actual_review_day_without_rewriting_content_date(self):
        issue = backfill_fixture()
        self.assertEqual(review_date(issue), date(2026, 9, 8))
        self.assertEqual(issue['date'], '2026-09-05')
        self.assertEqual(check_editorial(issue), [])

    def test_alias_compatibility_and_conflicts(self):
        for alias in ('revised_date', 'revision_date'):
            issue = editorial_fixture()
            issue[alias] = '2026-09-08'
            self.assertEqual(review_date(issue), date(2026, 9, 8))
        issue.update(revised_date='2026-09-07', revision_date='2026-09-08')
        self.assertTrue(issue_date_errors(issue))
        issue = backfill_fixture()
        issue['revised_date'] = '2026-09-07'
        self.assertTrue(issue_date_errors(issue))

    def test_invalid_or_future_preparation_dates_rejected(self):
        for value in ('2026-09-04', '2099-01-01', 'unknown', '2026-09'):
            issue = backfill_fixture()
            issue['backfill']['prepared_date'] = value
            self.assertTrue(issue_date_errors(issue), value)
        for metadata in ({}, [], None, dict(prepared_date='2026-09-08', reason='')):
            issue = backfill_fixture()
            issue['backfill'] = metadata
            self.assertTrue(issue_date_errors(issue), metadata)

    def test_late_source_cannot_be_backdated_even_in_extended(self):
        issue = backfill_fixture()
        future = copy.deepcopy(issue['papers'][0])
        future.update(id='extended-late', priority='extended', published_date='2026-09-06')
        issue['papers'].append(future)
        self.assertTrue(any('不得倒填' in error for error in check_editorial(issue)))
        issue = backfill_fixture()
        issue['tools'][0]['release_date'] = '2026-09-06'
        self.assertTrue(check_editorial(issue))

    def test_retrieval_and_added_dates_cannot_exceed_real_preparation(self):
        for field in ('retrieved_date', 'added_date'):
            issue = backfill_fixture()
            issue['papers'][0][field] = '2026-09-09'
            self.assertTrue(issue_date_errors(issue))
        issue = backfill_fixture()
        issue['retrieved_date'] = '2026-09-09'
        self.assertTrue(issue_date_errors(issue))

    def test_extended_items_need_real_source_and_retrieval_dates(self):
        for field in ('published_date', 'retrieved_date'):
            issue = backfill_fixture()
            item = copy.deepcopy(issue['papers'][0])
            item.update(id='extended-undated', priority='extended')
            item.pop(field)
            issue['papers'].append(item)
            self.assertTrue(any('补刊缺少 ' + field in error for error in check_editorial(issue)))

    def test_month_only_source_date_is_not_filled_to_first_day(self):
        issue = backfill_fixture()
        issue['papers'][0]['published_date'] = '2026-09'
        self.assertTrue(issue_date_errors(issue))

    def test_normal_asof_stays_same_day_backfill_uses_actual_day(self):
        item = verified()
        issue = dict(date='2026-09-05', papers=[item])
        self.assertTrue(any('as-of 不一致' in error for error in selection_errors(issue, [], ASOF)))
        issue['backfill'] = dict(prepared_date='2026-09-07', reason='迁移期间补刊')
        self.assertEqual(selection_errors(issue, [], ASOF), [])
        wrong = '2026-09-08T18:00:00+08:00'
        self.assertTrue(any('prepared_date' in error for error in selection_errors(issue, [], wrong)))

    def test_source_cutoff_and_verified_at_are_both_enforced(self):
        item = verified()
        issue = dict(date='2026-09-05', backfill=dict(prepared_date='2026-09-07', reason='补刊'), papers=[item])
        item['published_date'] = item['review']['effective_date'] = '2026-09-06'
        self.assertTrue(any('不得倒填' in error for error in selection_errors(issue, [], ASOF)))
        item['published_date'] = item['review']['effective_date'] = '2026-09-04'
        item['review']['verified_at'] = '2026-09-08T00:00:00+08:00'
        self.assertTrue(any('核验时间晚于' in error for error in selection_errors(issue, [], ASOF)))

    def test_journal_checks_use_actual_preparation_day(self):
        issue = policy_fixture()
        issue['backfill'] = dict(prepared_date='2026-09-15', reason='补刊')
        self.assertTrue(paper_policy_errors(issue))  # 9/10 checks are stale on 9/15.
        for rows in issue['paper_review'].values():
            for row in rows:
                row.update(checked_at='2026-09-15', window_start='2026-09-01', window_end='2026-09-15')
        self.assertEqual(paper_policy_errors(issue), [])
        issue.pop('backfill')
        self.assertTrue(paper_policy_errors(issue))  # Ordinary 9/10 cannot use future checks.

    def test_readers_see_actual_backfill_note_not_internal_revision(self):
        issue = backfill_fixture()
        issue.update(status='published', revision_note='INTERNAL-NOT-FOR-READERS')
        # 只检查期次日期说明；不伪造已审核条目或绕过读者摘要指纹。
        issue.update(lianxh_posts=[], papers=[], tools=[])
        with patch('render_issue_pages.render_promotion', return_value=''):
            page = render_page(issue)
        self.assertIn('连享会 · 快讯 | 2026.09.05', page)
        self.assertIn('本期于 2026-09-08 补录。', page)
        self.assertNotIn('INTERNAL-NOT-FOR-READERS', page)

    def test_ordinary_issue_does_not_gain_a_backfill_note(self):
        issue = dict(editorial_fixture(), status='published', lianxh_posts=[], papers=[], tools=[])
        with patch('render_issue_pages.render_promotion', return_value=''):
            page = render_page(issue)
        self.assertNotIn('backfill-note', page)

    def test_expired_conference_checked_at_actual_preparation_day(self):
        issue = dict(date='2026-09-05', issue_type='daily', backfill=dict(prepared_date='2026-09-08', reason='补刊'),
                     conference_calls=[dict(id='conference', priority='core', event_id='meeting', organizer_or_journal='University',
                         topic='Methods', official_url='https://example.org/meeting', event_date='2026-09-10',
                         location='北京', fee_note='未知', deadline_kind='submission', deadline='2026-09-07', status='open')])
        self.assertTrue(any('已过期会议' in error for error in check_website(issue)))


class BackfillPublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.desk = Desk(self.root)
        self.issue = dict(date='2026-09-05', status='published', backfill=dict(prepared_date='2026-09-08', reason='补刊'),
                          papers=[dict(id='paper-backfill', title='Paper', priority='core', doi_url='https://doi.org/10.1/test', added_date='2026-09-08')])
        write(self.root/'content/issues/2026-09-05.json', self.issue)

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_live_proof_cannot_create_historical_publication(self):
        state = self.desk.migrate()
        self.assertEqual(state['publications'], [])
        candidate = next(iter(state['candidates'].values()))
        self.assertEqual(candidate['first_discovered'], '2026-09-08')
        self.assertEqual(candidate['status'], 'needs-review')

    def test_actual_publication_time_separate_from_issue_date_and_idempotent(self):
        proof = dict(status='published', commit='abc123', published_at='2026-09-09T10:00:00+08:00')
        write(self.root/'ops-local/runs/2026-09-05/publication.json', proof)
        state = self.desk.migrate()
        self.assertEqual(len(state['publications']), 1)
        publication = state['publications'][0]
        self.assertEqual(publication['at'], proof['published_at'])
        self.assertEqual(publication['issue_date'], '2026-09-05')
        self.assertEqual(publication['wechat_sent'], 'unknown')
        self.assertEqual(publication['timestamp_basis'], 'actual-publication')
        self.assertEqual(len(self.desk.migrate()['publications']), 1)

    def test_undated_naive_future_or_unconfirmed_proof_cannot_invent_time(self):
        for proof in ({}, dict(status='published', commit='abc'),
                      dict(status='published', commit='abc', published_at='2026-09-09T10:00:00'),
                      dict(status='published', commit='abc', published_at='2099-01-01T00:00:00+08:00'),
                      dict(status='pending', commit='abc', published_at='2026-09-09T10:00:00+08:00')):
            self.assertIsNone(publication_moment(self.issue, proof)[0])

    def test_other_issue_proof_cannot_be_reused(self):
        proof = dict(date='2026-09-06', status='published', commit='abc', published_at='2026-09-09T10:00:00+08:00')
        self.assertEqual(publication_moment(self.issue, proof), (None, 'mismatched-issue-proof'))

    def test_verification_timestamp_is_labelled_as_verification(self):
        proof = dict(status='published', commit='abc', verified_at='2026-09-09T10:05:00+08:00')
        self.assertEqual(publication_moment(self.issue, proof), (proof['verified_at'], 'actual-online-verification'))

    def test_actual_timestamp_is_normalized_to_shanghai_for_event_order(self):
        proof = dict(status='published', commit='abc', published_at='2026-09-08T16:30:00Z')
        self.assertEqual(publication_moment(self.issue, proof), ('2026-09-09T00:30:00+08:00', 'actual-publication'))

    def test_bounded_source_check_preserves_found_without_advancing_success(self):
        for flags, advances in (({}, True), ({'complete': False}, False),
                                ({'exhaustive': False}, False),
                                ({'complete': True, 'exhaustive': False}, False),
                                ({'complete': True, 'exhaustive': True}, True)):
            for fallback in (False, True):
                with self.subTest(flags=flags, fallback=fallback), tempfile.TemporaryDirectory() as tmp:
                    desk = Desk(tmp)
                    old = dict(kind='check', at='2026-09-06', source_id='working-paper:nber',
                               status='no-eligible', complete=True, window_start='2026-08-20',
                               window_end='2026-09-06', candidate_ids=[], reason='Previous complete check')
                    old_key = desk.emit(old)
                    old_path = desk.events/(old_key+'.json')
                    old_bytes = old_path.read_bytes()
                    current = dict(source='NBER', status='found', checked_at='2026-09-08',
                                   window_start='2026-08-25', window_end='2026-09-08',
                                   candidate_ids=['paper-backfill'], evidence_url='https://www.nber.org/',
                                   reason='Current bounded listing', **flags)
                    row = dict(current, status='access-failed', fallback=current) if fallback else current
                    issue = dict(self.issue, paper_review={'working_paper_checks': [row]})
                    write(Path(tmp)/'content/issues/2026-09-05.json', issue)
                    state = desk.migrate()
                    source = state['sources']['working-paper:nber']
                    self.assertEqual(source['last_attempt']['status'], 'found')
                    self.assertEqual(source['last_attempt']['complete'], advances)
                    self.assertEqual(source['last_success']['at'], '2026-09-08' if advances else old['at'])
                    self.assertEqual(old_path.read_bytes(), old_bytes)
                    self.assertEqual(len(list(desk.events.glob('*.json'))), 3)

    def test_old_non_backfill_migration_contract_unchanged(self):
        self.issue.pop('backfill')
        write(self.root/'content/issues/2026-09-05.json', self.issue)
        state = self.desk.migrate()
        publication = state['publications'][0]
        self.assertEqual(publication['at'], '2026-09-05')
        self.assertNotIn('timestamp_basis', publication)
        self.assertEqual(publication['wechat_sent'], 'unknown')


if __name__ == '__main__':
    unittest.main()
