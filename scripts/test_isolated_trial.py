"""固定样例测试；临时文件必须位于调用者指定的外部测试根。"""
import copy
from datetime import date, timedelta
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_local_draft import daily_issue
from editorial_rules import check_editorial
from isolated_trial import Isolation, coverage_errors
from trial_selection import assess, evaluation, identities, selection_errors
from validate_issue import validate_schema
from test_editorial_rules import fixture

ASOF='2026-09-07T18:00:00+08:00'

def complete_coverage():
    start='2026-09-01T00:00:00+08:00'
    return dict(status='complete',baseline=start,checked_to=ASOF,
        baseline_evidence=dict(status='confirmed',kind='user-decision',source='fixture only',locator='approved test point',sha256='a'*64,coverage_through=start),
        page_evidence=['fixture all pages'],post_records=[],required_post_ids=[],unresolved_posts=[])

def verified():
    item=copy.deepcopy(fixture()['papers'][0])
    item.pop('pdf_url'); item['bibliography'].pop('pdf')
    item['published_date']='2026-09-04'
    item['review']=dict(source_id='fixture',source_url='https://example.org/paper',
        version_read='v1',date_basis='官方首次公开日期',evidence_locator='摘要第 1 段',
        identity_evidence='核对 DOI 与题名',identity_status='resolved',
        evidence_level='abstract',version_matches=True,human_review='pending',
        effective_date='2026-09-04',verified_at=ASOF)
    return item

class TrialTests(unittest.TestCase):
    def test_coverage_empty_is_not_failure(self):
        complete=complete_coverage()
        self.assertEqual(coverage_errors(complete, [], ASOF, []), [])
        for bad in (dict(status='failed'), dict(status='complete')):
            self.assertTrue(coverage_errors(bad, [], ASOF, []))

    def test_coverage_omission_and_unresolved(self):
        coverage=complete_coverage()
        post=dict(id='new',url='https://example.org/new',date='2026-09-04')
        coverage.update(required_post_ids=['new'],post_records=[dict(post,decision='proposed',reason='内容已核验')])
        self.assertTrue(coverage_errors(coverage, [], ASOF, [post]))
        self.assertEqual(coverage_errors(coverage, ['new'], ASOF, [post]), [])
        coverage['unresolved_posts']=['another']
        self.assertTrue(coverage_errors(coverage, ['new'], ASOF, [post]))

    def test_zero_software_working_papers(self):
        issue=fixture(); issue['tools']=[]
        issue['papers']=[dict(issue['papers'][0],id=f'p-{i}',publication_status='working-paper') for i in range(3)]
        self.assertEqual(check_editorial(issue),[])

    def test_zero_papers_three_software(self):
        issue=fixture(); issue['papers']=[]
        issue['tools']=[dict(issue['tools'][0],id=f't-{i}') for i in range(3)]
        self.assertEqual(check_editorial(issue),[])

    def test_non_top_five_and_resource(self):
        issue=fixture(); issue['papers'][0]['journal']='Journal of Finance'
        issue['research_resources']=[dict(issue['lianxh_posts'][0],id='job-resource')]
        self.assertEqual(check_editorial(issue),[])

    def test_quantity_limits(self):
        for count in (0,1,2,6):
            issue=fixture(); issue.update(papers=[],tools=[],lianxh_posts=[dict(issue['lianxh_posts'][0],id=f'post-{i}') for i in range(count)])
            self.assertTrue(check_editorial(issue))
        issue=fixture(); issue['research_resources']=[dict(issue['lianxh_posts'][0],priority='extended',id=f'e-{i}') for i in range(11)]
        errors=[]; validate_schema(issue,Path('fixture'),errors)
        self.assertTrue(any('extended' in e for e in errors))

    def test_date_windows(self):
        for age,reason,okay in [(0,'',True),(14,'',True),(15,'',False),(15,'重要遗漏：新方法值得补充',True),(30,'重要遗漏',True),(31,'重要遗漏',False),(-1,'',False)]:
            with self.subTest(age=age,reason=reason):
                item=verified(); item['review']['effective_date']=(date(2026,9,7)-timedelta(days=age)).isoformat(); item['published_date']=item['review']['effective_date']; item['review']['omission_reason']=reason
                self.assertEqual(not assess(item,'papers',[],ASOF),okay)
        for value in ('2026-09','unknown','2020-01-01'):
            item=verified(); item['review']['effective_date']=value
            self.assertTrue(assess(item,'papers',[],ASOF))
        self.assertEqual(evaluation('2026-09-06T20:00:00+00:00').date(),date(2026,9,7))
        with self.assertRaises(ValueError): evaluation('2026-09-07T18:00:00')

    def test_discovery_cannot_refresh_first_date(self):
        for original in ('2020-01-01','2026-09'):
            item=verified(); item['published_date']=original
            self.assertTrue(assess(item,'papers',[],ASOF))
        item=verified(); item['published_date']='2020-01-01'
        item['review'].update(change_type='method',new_information='新增估计方法',change_evidence='官方版本说明')
        self.assertEqual(assess(item,'papers',[],ASOF),[])

    def test_long_history_and_exception(self):
        item=verified(); old=dict(item,id='old',events=[dict(kind='website',date='2026-07-01',evidence='fixture formal page')])
        self.assertTrue(assess(item,'papers',[old],ASOF))
        item['review'].update(change_type='data',new_information='增加新样本',change_evidence='原始更新说明')
        self.assertEqual(assess(item,'papers',[old],ASOF),[])
        old['events'][0]['date']='2026-09-01'
        self.assertTrue(assess(item,'papers',[old],ASOF))
        item['review'].update(is_exception=True)
        self.assertTrue(assess(item,'papers',[old],ASOF))
        item['review'].update(change_type='correction',previous_id='old',announcement_url='https://example.org/notice',impact='修正标准误计算',change_evidence='原始勘误第 2 段')
        self.assertEqual(assess(item,'papers',[old],ASOF),[])
        for field in ('previous_id','announcement_url','impact','change_evidence'):
            bad=copy.deepcopy(item); bad['review'].pop(field)
            self.assertTrue(assess(bad,'papers',[old],ASOF))

    def test_paper_cross_platform(self):
        item=verified(); item['identity_aliases']=['arxiv:2608.12345']
        old=dict(id='preprint',arxiv_id='2608.12345v1',history_date='2026-07-01')
        self.assertTrue(assess(item,'papers',[old],ASOF))

    def test_software_identity(self):
        python=dict(ecosystem='Python',name='same',project_id='project:one')
        github=dict(url='https://github.com/author/one',project_id='project:one')
        r=dict(ecosystem='R',name='same',project_id='project:two')
        self.assertTrue(identities(python)&identities(github))
        self.assertFalse(identities(python)&identities(r))

    def test_evidence_pdf_and_version(self):
        item=verified(); self.assertEqual(assess(item,'papers',[],ASOF),[])
        for field,value in [('version_matches',False),('detailed_claims',True),('identity_status','unknown'),('human_review','approved')]:
            bad=copy.deepcopy(item); bad['review'][field]=value
            self.assertTrue(assess(bad,'papers',[],ASOF))
        item['pdf_url']=item['doi_url']
        self.assertTrue(assess(item,'papers',[],ASOF))

    def test_builder_validator_same_asof(self):
        issue=fixture(); item=verified()
        ledger=[dict(kind='paper',core_or_extended='core',payload=dict(item,id=f'p-{i}',doi_url=f'https://doi.org/10.1/{i}',homepage_url=f'https://example.org/{i}',title=f'Paper {i}')) for i in range(3)]
        issue=daily_issue('2026-09-07',ledger,as_of=ASOF)
        self.assertEqual(selection_errors(issue,[],ASOF),[])
        ledger[0]['payload']['review']['effective_date']='2020-01-01'
        with self.assertRaises(ValueError): daily_issue('2026-09-07',ledger,as_of=ASOF)

    def test_conference_deferred(self):
        for change in ('none','postponement','cancellation'):
            item=verified(); item['review']['change_type']=change
            self.assertTrue(assess(item,'conference_calls',[],ASOF))

    def test_isolation_paths(self):
        base=Path(os.environ['TASK11_TEST_ROOT']).resolve()
        base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as tmp:
            tmp=Path(tmp); production=tmp/'production'; production.mkdir()
            for bad in (None,production,production/'child',tmp/'x'/'..'/'production',tmp):
                with self.assertRaises(ValueError): Isolation(bad,[production])
            guard=Isolation(tmp/'external',[production]); guard.write('okay.txt','okay')
            with self.assertRaises(ValueError): guard.write('../production/bad.txt','bad')
            with self.assertRaises(ValueError): Isolation(tmp/'external',[production])
            original=Path.resolve
            def alias(path,*a,**kw):
                return production if path.name=='junction' else original(path,*a,**kw)
            with patch.object(Path,'resolve',alias):
                with self.assertRaises(ValueError): Isolation(tmp/'junction',[production])
            self.assertEqual(list(production.iterdir()),[])

if __name__=='__main__': unittest.main()
