"""用隔离目录验证跨日事实、覆盖和恢复，不操作生产发布。"""
import json,tempfile,unittest
from pathlib import Path
from editorial_desk import Desk,write,identity,command_lock

class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.d=Desk(self.root)
        write(self.root/'config/source-registry.yml',{'editorial_sources':[dict(id='software:r',category='software-R',url='https://example.org',interval_days=3)]})
        (self.root/'evidence.txt').write_text('actual sample',encoding='utf-8')
    def tearDown(self):self.tmp.cleanup()
    def check(self,**kw):
        row=dict(source_id='software:r',at='2026-09-14',status='found',complete=True,window_start='2026-09-01',window_end='2026-09-14',candidate_ids=['pkg'],reason='reviewed',evidence_path='evidence.txt');row.update(kw);return self.d.check(row)
    def test_exclusive_command_lock_releases(self):
        with command_lock(self.root):
            with self.assertRaises(OSError):
                with command_lock(self.root):pass
        with command_lock(self.root):pass
    def test_repeated_events_are_idempotent(self):
        self.check();self.check();self.assertEqual(len(list(self.d.events.glob('*.json'))),1)
    def test_failure_keeps_success_cursor(self):
        self.check();s=self.check(at='2026-09-15',status='access-failed',complete=False,candidate_ids=[])
        self.assertEqual(s['sources']['software:r']['last_success']['window_end'],'2026-09-14')
        self.assertEqual(s['sources']['software:r']['last_attempt']['status'],'access-failed')
    def test_partial_page_does_not_advance(self):
        self.check();s=self.check(at='2026-09-15',window_end='2026-09-15',complete=False)
        self.assertEqual(s['sources']['software:r']['last_success']['window_end'],'2026-09-14')
    def test_failed_complete_rejected(self):
        with self.assertRaises(ValueError):self.check(status='access-failed')
    def test_missing_evidence_rejected(self):
        with self.assertRaises(ValueError):self.check(evidence_path='absent')
    def test_future_coverage_rejected(self):
        with self.assertRaises(ValueError):self.check(window_end='2099-01-01')
    def test_due_dates_preserve_old_date(self):
        self.check();p=self.d.plan('2026-09-15');self.assertFalse(p['tasks'][0]['due']);self.assertEqual(p['tasks'][0]['last_success'],'2026-09-14')
        self.assertTrue(self.d.plan('2026-09-17')['tasks'][0]['due'])
    def test_published_never_returns_to_pool(self):
        for e in [dict(kind='candidate',at='2026-09-14',key='k',candidate=dict(id='a',payload={'title':'A'},status='needs-review')),dict(kind='publication',at='2026-09-14',order=2,key='k'),dict(kind='candidate',at='2026-09-15',key='k',candidate=dict(id='a',payload={'title':'A'},status='needs-review'))]:self.d.emit(e)
        self.assertEqual(self.d.rebuild()['candidates']['k']['status'],'published');self.assertEqual(self.d.plan('2026-09-15')['candidates'],[])
    def test_arxiv_versions_share_identity(self):
        self.assertEqual(identity(dict(doi_url='https://doi.org/10.48550/arXiv.2609.12345v2')),identity(dict(doi_url='https://doi.org/10.48550/arxiv.2609.12345')))
    def test_software_ecosystems_distinct(self):
        a=dict(id='x',name='same',ecosystem='R');b=dict(a,ecosystem='Python');self.assertNotEqual(identity(a,'tools'),identity(b,'tools'))
    def test_conference_date_change_same_event(self):
        a=dict(id='x',event_id='forum-2026',deadline='2026-10-01');self.assertEqual(identity(a,'conference_calls'),identity(dict(a,deadline='2026-10-12'),'conference_calls'))
    def test_build_blocked_without_source_and_comparison(self):
        r=self.d.audit('2026-09-15',dict(date='2026-09-15'),dict(date='2026-09-15'));self.assertFalse(r['passed'])
    def test_expired_candidates_not_news(self):
        self.d.emit(dict(kind='candidate',at='2026-08-01',key='k',candidate=dict(id='a',payload={'title':'A'},status='needs-review',metadata={'published-online':{'date-parts':[[2026,8,1]]}})))
        self.assertFalse(self.d.plan('2026-09-15')['candidates'][0]['eligible_window'])
    def test_atomic_state_rebuild_after_loss(self):
        self.check();(self.d.base/'state.json').unlink();self.assertIn('software:r',self.d.rebuild()['sources'])

if __name__=='__main__':unittest.main()
