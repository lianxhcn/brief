"""Conference regressions use external temporary roots and read-only real fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from conference_policy import conference_window, conference_publication_errors, conference_publication_kind, conference_change_facts
from editorial_desk import Desk, identity, write
from validate_issue import validate_history
from website_rules import conference_errors

ROOT = Path(__file__).resolve().parents[1]
ASOF = '2026-11-11T10:00:00+08:00'


def conference(**kw):
    row = dict(id='forum-2026', event_id='forum-2026', title='研究论坛',
        deadline='2026-11-15', deadline_kind='submission', event_date='2026-12-01',
        event_end_date='2026-12-03', status='open', official_url='https://example.org/forum',
        organizer_or_journal='大学', topic='经济研究', location='北京', fee_note='通知未列费用',
        published_date='2026-06-01', source_date_status='known', reminder=False)
    row.update(kw)
    return row


def published(item, day):
    return dict(item, events=[dict(kind='website', date=day, evidence='formal.json#'+item['id'])])


class WindowTests(unittest.TestCase):
    def test_old_announcement_near_deadlines_are_actionable(self):
        for day in ('2026-11-12','2026-11-13','2026-11-14','2026-11-15','2026-11-16'):
            with self.subTest(day=day):
                item=conference(deadline=day)
                self.assertTrue(conference_window(item,ASOF)['actionable'])
                self.assertEqual(conference_errors(item,ASOF),[])

    def test_same_day_not_assumed_to_close_at_midnight(self):
        item=conference(deadline='2026-11-11')
        self.assertIsNone(conference_window(item,ASOF)['actionable'])
        self.assertTrue(conference_errors(item,ASOF))
        item['deadline_at']='2026-11-11T18:00:00'
        self.assertIsNone(conference_window(item,ASOF)['actionable'])
        item['deadline_at']='2026-11-11T18:00:00+08:00'
        self.assertTrue(conference_window(item,ASOF)['actionable'])
        self.assertFalse(conference_window(item,'2026-11-11T19:00:00+08:00')['actionable'])

    def test_exact_foreign_timezone_not_changed_to_wrong_calendar_date(self):
        item=conference(deadline='2026-11-10', deadline_at='2026-11-10T23:59:00-05:00')
        self.assertTrue(conference_window(item,ASOF)['actionable'])

    def test_same_day_official_current_open_evidence(self):
        item=conference(deadline='2026-11-11',deadline_open_verified_at='2026-11-11T09:59:00+08:00',
                        deadline_open_evidence_url='https://example.org/current-open')
        self.assertTrue(conference_window(item,ASOF)['actionable'])
        item['deadline_open_verified_at']='2026-11-10T09:59:00+08:00'
        self.assertIsNone(conference_window(item,ASOF)['actionable'])

    def test_closed_submission_open_registration_is_labelled(self):
        item=conference(deadline='2026-11-01',submission_deadline='2026-11-01',registration_deadline='2026-11-20')
        self.assertFalse(conference_window(item,ASOF)['actionable'])
        item.update(deadline_kind='registration',deadline='2026-11-20')
        self.assertTrue(conference_window(item,ASOF)['actionable'])
        self.assertEqual(conference_errors(item,ASOF),[])
        item['deadline']='2026-11-01'
        self.assertIsNone(conference_window(item,ASOF)['actionable'])

    def test_registration_can_continue_during_multiday_event(self):
        item=conference(deadline_kind='registration',deadline='2026-12-02')
        self.assertTrue(conference_window(item,'2026-12-02T08:00:00+08:00')['actionable'] is None)
        item['deadline_at']='2026-12-02T12:00:00+08:00'
        self.assertTrue(conference_window(item,'2026-12-02T08:00:00+08:00')['actionable'])

    def test_unknown_date_not_no_eligible_and_unknown_fee_allowed(self):
        item=conference(deadline='unknown',source_date_status='unknown')
        item.pop('published_date')
        self.assertIsNone(conference_window(item,ASOF)['actionable'])
        item['deadline']='2026-11-15'
        self.assertEqual(conference_errors(item,ASOF),[])
        self.assertNotIn('published_date',item)


class RepeatTests(unittest.TestCase):
    def test_real_oct4_to_oct16_reminders(self):
        first=json.loads((ROOT/'content/issues/2026-10-04.json').read_text(encoding='utf-8'))
        later=json.loads((ROOT/'content/issues/2026-10-16.json').read_text(encoding='utf-8'))
        history=[published(item,'2026-10-04') for item in first['conference_calls']]
        for item in later['conference_calls']:
            if item.get('reminder'):
                self.assertEqual(conference_publication_errors(item,history,'2026-10-16'),[])
                self.assertEqual(conference_errors(item,'2026-10-16',history),[])

    def test_long_term_duplicate_and_same_day_rejected(self):
        old=published(conference(),'2026-09-01')
        item=conference(id='new-id',official_url='https://example.org/new-url')
        self.assertTrue(conference_publication_errors(item,[old],ASOF))
        item.update(reminder=True,previous_id=old['id'])
        self.assertEqual(conference_publication_errors(item,[old],ASOF),[])
        old['events'][0]['date']='2026-11-11'
        self.assertTrue(conference_publication_errors(item,[old],ASOF))

    def test_only_one_reminder_and_near_deadline_first_not_mechanical(self):
        first=published(conference(),'2026-11-10')
        reminder=conference(id='reminder',reminder=True,previous_id=first['id'])
        self.assertTrue(conference_publication_errors(reminder,[first],ASOF))
        reminder['review']={'reminder_necessity':'官方新增提交入口；原读者可能未见'}
        self.assertEqual(conference_publication_errors(reminder,[first],ASOF),[])
        self.assertTrue(conference_publication_errors(reminder,[first,published(reminder,'2026-11-10')],ASOF))

    def test_missing_or_undated_proof_not_publication(self):
        item=conference(reminder=True,previous_id='old')
        for events in ([],[dict(kind='website',evidence='x')],[dict(kind='website',date='2026-11-01')]):
            self.assertTrue(conference_publication_errors(item,[dict(conference(id='old'),events=events)],ASOF))

    def test_changed_event_id_same_official_notice_not_identity_escape(self):
        old=published(conference(),'2026-11-01')
        self.assertTrue(conference_publication_errors(conference(id='new',event_id='invented-edition'),[old],ASOF))

    def test_postponement_and_cancellation_preserve_identity(self):
        old=published(conference(),'2026-11-01')
        for kind,status in [('postponement','postponed'),('cancellation','cancelled')]:
            item=conference(id='change',status=status,previous_id=old['id'],review=dict(change_type=kind,
                announcement_url='https://example.org/notice',change_evidence='官方通知说明状态',impact='原计划需调整'))
            self.assertEqual(identity(item,'conference_calls'),identity(old,'conference_calls'))
            self.assertEqual(conference_publication_kind(item),kind)
            self.assertEqual(conference_publication_errors(item,[old],ASOF),[])
            self.assertTrue(conference_publication_errors(item,[old,published(item,'2026-11-10')],ASOF))
            item['review'].pop('impact')
            self.assertTrue(conference_publication_errors(item,[old],ASOF))

    def test_venue_and_participation_changes_need_actual_before_after(self):
        old=published(conference(),'2026-11-01')
        for kind,field,value in [('venue-change','location','上海'),('participation-change','fee_note','官方新通知免注册费')]:
            item=conference(id='change',previous_id=old['id'])
            item[field]=value
            item['review']=dict(change_type=kind,announcement_url='https://example.org/change',
                change_evidence={'before':{field:old[field]},'after':{field:value}},impact='读者参会安排改变')
            self.assertEqual(conference_publication_errors(item,[old],ASOF),[])
            item['review']['change_evidence']['before'][field]='invented'
            self.assertTrue(conference_publication_errors(item,[old],ASOF))

    def test_same_actual_change_ignores_notes_and_stale_previous_id(self):
        first=published(conference(),'2026-11-01')
        for kind,field,new_value in [('venue-change','location','上海'),('participation-change','fee_note','注册费500元')]:
            changed=conference(id='first-change',previous_id=first['id'])
            changed[field]=new_value
            changed['review']=dict(change_type=kind,announcement_url='https://example.org/update',impact='参会安排变化',
                change_evidence={'before':{field:first[field]},'after':{field:new_value},'note':'11月10日原核验备注'})
            earlier=published(changed,'2026-11-10')
            replay=copy.deepcopy(changed);replay['id']='new-id'
            replay['review']['change_evidence']['note']='11月11日重写备注；不是新事件'
            replay['review']['impact']='用不同措辞重写影响'
            self.assertEqual(conference_change_facts(replay),conference_change_facts(changed))
            self.assertTrue(any('相同重要变更' in error for error in conference_publication_errors(replay,[first,earlier],ASOF)))
            # A different page URL does not make the same transition new either.
            replay['review']['announcement_url']='https://example.org/update?copy=2'
            self.assertTrue(conference_publication_errors(replay,[first,earlier],ASOF))

    def test_same_official_url_later_actual_transition_is_allowed(self):
        first=published(conference(),'2026-11-01')
        prior=conference(id='venue1',previous_id=first['id'],location='上海')
        prior['review']=dict(change_type='venue-change',announcement_url='https://example.org/live-notice',impact='调整行程',
            change_evidence={'before':{'location':'北京'},'after':{'location':'上海'},'note':'第一份变更'})
        history=[first,published(prior,'2026-11-10')]
        current=conference(id='venue2',previous_id=prior['id'],location='广州')
        current['review']=dict(change_type='venue-change',announcement_url='https://example.org/live-notice',impact='再次调整行程',
            change_evidence={'before':{'location':'上海'},'after':{'location':'广州'},'note':'同入口上的后续真实更新'})
        self.assertEqual(conference_publication_errors(current,history,ASOF),[])
        current['review']['change_evidence']['before']['location']='北京'
        current['previous_id']=first['id']
        self.assertTrue(any('最新已刊事实' in error for error in conference_publication_errors(current,history,ASOF)))

    def test_postponement_or_cancellation_note_alone_is_not_a_new_event(self):
        first=published(conference(),'2026-11-01')
        for kind,status in [('postponement','postponed'),('cancellation','cancelled')]:
            prior=conference(id='state1',previous_id=first['id'],status=status)
            prior['review']=dict(change_type=kind,announcement_url='https://example.org/status',impact='原计划需调整',change_evidence='原官方状态公告')
            replay=copy.deepcopy(prior);replay['id']='state2';replay['review']['change_evidence']='同一公告换个说法'
            self.assertTrue(conference_publication_errors(replay,[first,published(prior,'2026-11-10')],ASOF))
        later=copy.deepcopy(prior)
        # Postponement at the same URL with a genuinely later conference date is distinct.
        prior.update(status='postponed');prior['review']['change_type']='postponement'
        later=copy.deepcopy(prior);later.update(id='new-postponement',previous_id=prior['id'],event_date='2026-12-10',event_end_date='2026-12-12')
        self.assertEqual(conference_publication_errors(later,[first,published(prior,'2026-11-10')],ASOF),[])

    def test_validate_history_checks_all_prior_occurrences(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            first=conference(deadline='2026-11-15')
            reminder=conference(id='r1',reminder=True,previous_id=first['id'])
            write(root/'2026-10-01.json',dict(date='2026-10-01',status='published',conference_calls=[first]))
            write(root/'2026-11-01.json',dict(date='2026-11-01',status='published',conference_calls=[reminder]))
            current=dict(date='2026-11-11',conference_calls=[dict(reminder,id='r2')])
            errors=[];validate_history(current,root/'current.json',root,errors)
            self.assertTrue(any('最多一次' in err for err in errors),errors)

    def test_real_legacy_bulletin_without_event_id_keeps_frozen_identity_unknown(self):
        source=ROOT/'content/issues/2026-09-04-conference.json'
        issue=json.loads(source.read_text(encoding='utf-8'))
        self.assertEqual({item['id'] for item in issue['conference_calls']},
            {'causal-data-science-meeting-2026','fma-asset-management-2027','iceb-2026'})
        self.assertTrue(all(not item.get('event_id') for item in issue['conference_calls']))
        errors=[];validate_history(issue,source,ROOT/'content/issues',errors)
        self.assertEqual(errors,[])
        current=copy.deepcopy(issue);current['date']='2026-11-12'
        with tempfile.TemporaryDirectory() as temp:
            errors=[];validate_history(current,Path(temp)/'current.json',Path(temp),errors)
        self.assertTrue(any('event_id' in error for error in errors))
        draft=copy.deepcopy(issue);draft.update(date='2026-11-11',status='draft')
        errors=[];validate_history(draft,source,ROOT/'content/issues',errors)
        self.assertTrue(any('event_id' in error for error in errors))


class PlannerObservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.desk=Desk(self.root)
        write(self.root/'config/source-registry.yml',{'editorial_sources':[
            dict(id='conference:brand',category='conferences',url='https://example.org',interval_days=7,review_weekdays=['mon','thu'],daily_incremental=False),
            dict(id='conference:discovery',category='conferences',url='https://example.org/discover',interval_days=7,review_weekdays=['mon','thu'],daily_incremental=True)]})
        (self.root/'raw.txt').write_text('实际通知原件',encoding='utf-8')
    def tearDown(self):self.tmp.cleanup()
    def ingest(self,**kw):
        row=dict(category='conference_calls',payload=conference(),source_id='conference:brand',evidence_path='raw.txt',at=ASOF)
        row.update(kw);return self.desk.ingest(row)
    def test_mon_thu_full_daily_discovery_and_active_pending_followup(self):
        p=self.desk.plan('2026-11-11')
        self.assertFalse(p['tasks'][0]['due']);self.assertTrue(p['tasks'][1]['due'])
        self.assertTrue(all(t['due'] and t['action']=='full-review' for t in self.desk.plan('2026-11-12')['tasks']))
        self.ingest();p=self.desk.plan('2026-11-11')
        self.assertTrue(p['tasks'][0]['due'])
        self.assertEqual(p['conference_summary']['unresolved_soon_deadline'],1)
        self.assertEqual(p['candidates'][0]['eligible_window'],True)
    def test_unknown_candidate_stays_visible_and_optional_output(self):
        self.ingest(payload=conference(deadline='unknown'))
        target=self.root/'verification/plan.json'
        p=self.desk.plan('2026-11-11',output_path=target)
        self.assertIsNone(p['candidates'][0]['eligible_window'])
        self.assertEqual(p['conference_summary']['unresolved_unknown'],1)
        self.assertTrue(target.is_file())
        self.assertFalse((self.root/'ops-local/runs/2026-11-11/editorial-plan.json').exists())
    def test_observation_keeps_raw_unmapped_and_never_advances_success(self):
        row=dict(source_id='conference:brand',at=ASOF,stage='unmapped-findings',evidence_path='raw.txt',
                 reason='列表发现线索；详情未读',next_action='读取详情核对当届与截止')
        state=self.desk.observe(row)
        actual=state['sources']['conference:brand']['last_observation']
        self.assertEqual(actual['sha256'],hashlib.sha256((self.root/'raw.txt').read_bytes()).hexdigest())
        self.assertNotIn('last_success',state['sources']['conference:brand'])
        self.assertEqual(state['candidates'],{})
        self.desk.observe(row);self.assertEqual(len(list(self.desk.events.glob('*.json'))),1)
        for bad in [dict(row,complete=True),dict(row,candidate_ids=['fake']),dict(row,status='no-eligible'),dict(row,sha256='bad')]:
            with self.assertRaises(ValueError):self.desk.observe(bad)
    def test_partial_or_failed_observation_preserves_old_success(self):
        self.desk.check(dict(source_id='conference:brand',at='2026-11-09',status='no-eligible',complete=True,
            window_start='2026-11-01',window_end='2026-11-09',candidate_ids=[],reason='完整筛选范围内无合格项',evidence_path='raw.txt'))
        for stage in ('partial-screen','access-failed'):
            state=self.desk.observe(dict(source_id='conference:brand',at=ASOF,stage=stage,evidence_path='raw.txt',reason='有界读取或失败',next_action='沿原边界接续'))
            self.assertEqual(state['sources']['conference:brand']['last_success']['window_end'],'2026-11-09')
    def test_historical_first_discovery_requires_actual_hash_basis(self):
        row=dict(first_discovered='2026-11-02',first_discovered_evidence_path='raw.txt',
            first_discovered_evidence_sha256=hashlib.sha256((self.root/'raw.txt').read_bytes()).hexdigest(),
            first_discovered_basis={'observed_ids':['conf-cfrn-11593'],'observed_at':'2026-11-02'},next_action='核对具体差异',owner='editor')
        self.ingest(**row)
        c=next(iter(self.desk.rebuild()['candidates'].values()))
        self.assertEqual(c['first_discovered'],'2026-11-02')
        self.assertEqual(c['owner'],'editor');self.assertEqual(c['status'],'needs-review')
        event=json.loads(next(self.desk.events.glob('*.json')).read_text(encoding='utf-8'))
        self.assertEqual(event['at'],ASOF)
        row['first_discovered_evidence_sha256']='bad'
        with self.assertRaises(ValueError):self.ingest(payload=conference(id='another',event_id='another'),**row)
        row.pop('first_discovered_basis')
        with self.assertRaises(ValueError):self.ingest(payload=conference(id='third',event_id='third'),**row)

    def test_ready_updates_current_gap_and_preserves_original_event(self):
        self.ingest(gap='关键通知待核',next_action='读取主办方通知')
        key=identity(conference(),'conference_calls')
        # Isolate ledger transition; payload schema itself is tested by existing validate_item tests.
        with patch('validate_issue.validate_item'):
            state=self.desk.decide(dict(key=key,at=ASOF,status='ready',payload=conference(),
                reason='当届事实已核对',reviewed_by='editor'))
        current=state['candidates'][key]
        self.assertIsNone(current['gap'])
        self.assertEqual(current['next_action'],'审核合格，待编辑比较与编排')
        original=[json.loads(p.read_text(encoding='utf-8')) for p in self.desk.events.glob('*.json')]
        self.assertTrue(any(e.get('candidate',{}).get('gap')=='关键通知待核' for e in original))
    def test_strict_check_not_weakened_for_raw_fetch(self):
        with self.assertRaises(ValueError):
            self.desk.check(dict(source_id='conference:brand',at='2026-11-11',status='found',complete=False,
                window_start='2026-11-11',window_end='2026-11-11',candidate_ids=[],reason='只有HTTP200',evidence_path='raw.txt'))

    def test_successful_fetch_records_observation_not_coverage(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,*args):return b'<html>actual fetched fixture</html>'
        with patch('editorial_desk.urlopen',return_value=Response()):
            result=self.desk.fetch('conference:brand','2026-11-11')
        self.assertEqual(result['status'],'awaiting-screen')
        source=self.desk.rebuild()['sources']['conference:brand']
        self.assertEqual(source['last_observation']['stage'],'awaiting-screen')
        self.assertNotIn('last_success',source)

    def test_c08_first_conference_before_ordinary_paper_no_quota(self):
        self.ingest()
        for category,item in [('papers',{'id':'p','title':'paper'}),('lianxh_posts',{'id':'post','title':'连享会推文'})]:
            self.desk.emit(dict(kind='candidate',at=ASOF,key=category,candidate=dict(id=item['id'],payload=item,category=category,status='needs-review')))
        self.assertEqual([row['category'] for row in self.desk.plan('2026-11-11')['candidates']],['lianxh_posts','conference_calls','papers'])

    def test_published_still_open_activates_only_explicit_brand(self):
        item=conference(deadline='2026-11-30',review={'source_id':'brand'})
        key=identity(item,'conference_calls')
        self.desk.emit(dict(kind='candidate',at='2026-11-01',key=key,candidate=dict(
            id=item['id'],payload=item,category='conference_calls',status='needs-review',provenance='content/issues/2026-11-01.json')))
        self.desk.emit(dict(kind='publication',at='2026-11-01',issue_date='2026-11-01',key=key))
        plan=self.desk.plan('2026-11-11')
        self.assertTrue(plan['tasks'][0]['due'])
        self.assertEqual(plan['tasks'][0]['action'],'incremental-follow-up')
        self.assertEqual(plan['candidates'],[])
        self.assertEqual(plan['conference_action_queue'],[])  # Not near deadline; no fabricated reminder.


if __name__ == '__main__':unittest.main()
