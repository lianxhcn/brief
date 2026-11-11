"""D-20261111-02: isolated copies, real old cores, actual per-item date semantics."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch

from issue_dates import (website_addition_errors, issue_date_errors, item_evaluation_as_of,
                         item_evaluation_date, item_website_record_date, review_date)
from editorial_desk import Desk, identity, publication_moment, write
from website_rules import check_website
from validate_issue import validate_history, validate_wechat
from trial_selection import selection_errors
from render_issue_pages import render_page, render_section
from build_catalog_pages import entries, card
from website_content import fingerprint

ROOT=Path(__file__).resolve().parents[1]
ASOF='2026-11-11T15:20:00+08:00'


def fixture(number='11592'):
    day={'11592':'2026-11-08','11593':'2026-11-10'}[number]
    issue=json.loads((ROOT/'content/issues'/f'{day}.json').read_text(encoding='utf-8'))
    # Root may already have prepared the live draft; always reconstruct the old fixture.
    issue['conference_calls']=[i for i in issue.get('conference_calls',[]) if not i.get('website_addition')]
    # Explicit synthetic review fixture with public identities/dates; no dependency
    # on private migration materials, approval records or actual online proof.
    nwu=number=='11592'
    official='https://ems.nwu.edu.cn/info/1047/11044.htm' if nwu else 'https://airi.cufe.edu.cn/info/1012/1273.htm'
    item=dict(id='conf-cfrn-'+number,event_id='cwea-global-governance-political-economy-2026' if nwu else 'china-digital-intelligence-finance-annual-2026',
        title='隔离测试会议',deadline='2026-11-18' if nwu else '2026-11-15',deadline_kind='submission',
        event_date='2026-11-28' if nwu else '2026-12-05',event_end='2026-11-28' if nwu else '2026-12-06',
        published_date='2026-09-30' if nwu else '2026-10-19',retrieved_date='2026-11-11',first_discovered_date='2026-11-02',
        source_url=official,official_url=official,organizer_or_journal='测试主办方',topic='研究',location='北京',fee_note='测试费用字段',
        status='open',reminder=False,page_note='隔离测试摘要，不用于发布。',catalog=dict(section='academic-updates',tags=[],software=[],methods=[],fields=[]),
        review=dict(source_id='conference:cfrn',source_url=official,version_read='isolated test fixture',date_basis='fixture dates',
            evidence_locator='fixture',identity_evidence='explicit edition',evidence_level='official-page',version_matches=True,identity_status='resolved',
            effective_date='2026-11-11',verified_at='2026-11-11T15:00:00+08:00',human_review='pending'))
    item.update(priority='extended',website_addition=dict(added_date='2026-11-11',evaluated_at=ASOF,decision_id='D-20261111-02'))
    return issue,item


class WebsiteAdditionTests(unittest.TestCase):
    def test_planner_supplement_reminder_uses_actual_first_publication_in_cst(self):
        issue,item=fixture()
        for first,at,scope,expected in [
            ('2026-11-14T09:00:00+08:00','2026-11-11T15:20:00+08:00','website-supplement',False),
            (None,'2026-11-14T09:00:00+08:00','website-supplement',False),
            # UTC-5 Nov12 becomes CST Nov13: five days left, not six.
            ('2026-11-12T18:30:00-05:00','2026-11-12T18:30:00-05:00','website-supplement',False),
            (None,'2026-11-14T09:00:00','website-supplement',False),
            ('2026-11-14T09:00:00+08:00','2026-11-14T09:00:00+08:00',None,True),
        ]:
            with self.subTest(first=first,at=at,scope=scope),tempfile.TemporaryDirectory() as temp:
                root=Path(temp)
                write(root/'config/source-registry.yml',{'editorial_sources':[dict(id='conference:cfrn',category='conferences',url=item['official_url'],interval_days=3)]})
                desk=Desk(root);key=identity(item,'conference_calls')
                desk.emit(dict(kind='candidate',at='2026-11-11',key=key,candidate=dict(id=item['id'],category='conference_calls',payload=item,status='ready',source_id='conference:cfrn')))
                fact=dict(kind='publication',at=at,key=key,issue_date=issue['date'],target_issue_date=issue['date'],publication_type='initial')
                if scope:fact['publication_scope']=scope
                if first:fact['website_first_published_at']=first
                desk.emit(fact)
                plan=desk.plan('2026-11-15',output_path=root/'verification/plan.json')
                reminders=[row for row in plan['conference_action_queue'] if row['action']=='compare-one-reminder']
                self.assertEqual(bool(reminders),expected)
                self.assertEqual(plan['candidates'],[])

    def test_real_demo_files_pass_the_exact_ci_cli_without_real_publication_semantics(self):
        demos=sorted((ROOT/'content/issues').glob('*demo*.json'))
        self.assertEqual(len(demos),2)
        for source in demos:
            with self.subTest(source=source.name):
                run=subprocess.run([sys.executable,'-B','scripts/validate_issue.py','--input',str(source),
                    '--history-dir','content/issues','--wechat-dir','publish/wechat','--issues-dir','.'],
                    cwd=ROOT,text=True,encoding='utf-8',capture_output=True)
                self.assertEqual(run.returncode,0,run.stdout+'\n'+run.stderr)
        # The isolation exception must never transfer to a real draft.
        errors=[]
        with tempfile.TemporaryDirectory() as temp:
            validate_history(dict(date='2026-11-12',status='draft',conference_calls=[{'id':'missing-edition'}]),
                Path(temp)/'draft.json',Path(temp),errors)
        self.assertTrue(any('event_id' in error for error in errors),errors)

    def test_two_specific_items_and_actual_day_without_moving_original_clock(self):
        for number in ('11592','11593'):
            issue,item=fixture(number);old=copy.deepcopy(issue);issue['conference_calls'].append(item)
            self.assertEqual(website_addition_errors(issue),[])
            self.assertEqual(issue_date_errors(issue),[])
            self.assertEqual(review_date(issue).isoformat(),old['date'])
            self.assertEqual(item_evaluation_as_of(issue,item),ASOF)
            self.assertEqual(item_evaluation_date(issue,item).isoformat(),'2026-11-11')
            self.assertEqual(item_website_record_date(issue,item),'2026-11-11')
            paper=issue['papers'][0]
            self.assertEqual(item_evaluation_as_of(issue,paper),old.get('as_of') or old['date'])
            self.assertEqual(item_website_record_date(issue,paper),old['date'])
            for field in ('papers','paper_review','retrieved_date','as_of','lianxh_posts','tools'):
                self.assertEqual(issue.get(field),old.get(field))

    def test_no_general_historical_or_core_or_paper_exemption(self):
        issue,item=fixture();issue['conference_calls'].append(item)
        for change in ({'id':'unapproved-conference'}, {'priority':'core'}):
            bad=copy.deepcopy(issue);bad['conference_calls'][0].update(change)
            self.assertTrue(website_addition_errors(bad))
        bad=copy.deepcopy(issue);bad['date']='2026-11-09'
        self.assertTrue(website_addition_errors(bad))
        bad=copy.deepcopy(issue);bad['papers'][0]['website_addition']=copy.deepcopy(item['website_addition'])
        self.assertTrue(website_addition_errors(bad))
        for moved in ({'revised_date':'2026-11-11'}, {'as_of':ASOF},
                      {'backfill':{'prepared_date':'2026-11-11','reason':'not a whole-issue backfill'}}):
            bad=copy.deepcopy(issue);bad.update(moved)
            self.assertTrue(website_addition_errors(bad))

    def test_invalid_or_backdated_or_naive_addition_timestamps_rejected(self):
        issue,item=fixture();issue['conference_calls'].append(item)
        for update in ({'added_date':'2026-11-08'}, {'decision_id':'other'},
                       {'evaluated_at':'2026-11-11T16:00:00'}, {'evaluated_at':'2026-11-10T16:00:00+08:00'}):
            bad=copy.deepcopy(issue);bad['conference_calls'][0]['website_addition'].update(update)
            self.assertTrue(website_addition_errors(bad))
        bad=copy.deepcopy(issue);bad['conference_calls'][0]['review']['verified_at']='2026-11-11T17:00:00+08:00'
        self.assertTrue(website_addition_errors(bad))

    def test_addition_window_uses_nov11_not_old_page_date(self):
        issue,item=fixture();issue['conference_calls'].append(item)
        self.assertEqual(check_website(issue),[])
        # Synthetic expired deadline: open on Nov8, closed at actual Nov11 addition.
        item.update(deadline='2026-11-09',submission_deadline='2026-11-09')
        self.assertTrue(any('已过期会议' in error for error in check_website(issue)))

    def test_later_carrier_page_prior_publication_still_blocks_older_page_addition(self):
        issue,item=fixture();issue['conference_calls'].append(item)
        prior=dict(item,id='prior-item');prior.pop('website_addition')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            write(root/'2026-11-10.json',dict(date='2026-11-10',status='published',conference_calls=[prior]))
            errors=[];validate_history(issue,root/'2026-11-08.json',root,errors)
            self.assertTrue(any('同届已介绍' in error for error in errors),errors)

    def test_actual_addition_date_is_used_for_future_history_and_reminder(self):
        old,item=fixture();old['conference_calls'].append(item)
        # Deliberate fixture deadline makes Nov8 look early, while actual Nov11 is near.
        item.update(deadline='2026-11-15',submission_deadline='2026-11-15')
        reminder=copy.deepcopy(item);reminder.pop('website_addition')
        reminder.update(id='fixture-reminder',reminder=True,previous_id=item['id'])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);write(root/'2026-11-08.json',old)
            future=dict(date='2026-11-12',status='draft',conference_calls=[reminder])
            errors=[];validate_history(future,root/'2026-11-12.json',root,errors)
            self.assertTrue(any('首次介绍已临近截止' in error for error in errors),errors)
            earlier=dict(date='2026-11-10',status='published',conference_calls=[dict(reminder,reminder=False)])
            errors=[];validate_history(earlier,root/'2026-11-10.json',root,errors)
            self.assertEqual(errors,[])  # No fictitious Nov8 publication is projected backwards.

    def test_trial_keeps_old_paper_asof_and_evaluates_only_added_conference_now(self):
        issue,item=fixture();asof=issue.get('as_of') or issue['date']+'T23:59:00+08:00'
        before=selection_errors(issue,[],asof)
        item['review']['human_review']='pending'  # Explicit isolated-trial contract, not human acceptance.
        issue['conference_calls'].append(item)
        after=selection_errors(issue,[],asof)
        self.assertEqual(before,after)

    def test_old_daily_proof_cannot_backdate_addition_during_migration(self):
        issue,item=fixture();issue['conference_calls'].append(item)
        proof=dict(status='published',commit='old-original-commit',date=issue['date'])
        self.assertIsNone(publication_moment(issue,proof,item)[0])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);write(root/'content/issues'/f"{issue['date']}.json",issue)
            write(root/'ops-local/runs'/issue['date']/'publication.json',proof)
            desk=Desk(root);state=desk.migrate();key=identity(item,'conference_calls')
            self.assertEqual(state['candidates'][key]['first_discovered'],'2026-11-02')
            self.assertFalse(any(p['key']==key for p in state['publications']))
            original=list(desk.events.glob('*.json'))
            candidate=[json.loads(p.read_text(encoding='utf-8')) for p in original if json.loads(p.read_text(encoding='utf-8')).get('key')==key][0]
            self.assertEqual(candidate['at'],'2026-11-11')
            desk.emit(dict(kind='publication',at='2026-11-11T18:00:00+08:00',key=key,target_issue_date=issue['date'],website_record=True,live_verified=True,commit='new-fixture-commit'))
            existing={p.name:p.read_bytes() for p in desk.events.glob('*.json')}
            state=desk.migrate()
            self.assertEqual(state['candidates'][key]['status'],'published')
            self.assertTrue(all((desk.events/name).read_bytes()==raw for name,raw in existing.items()))

    def test_renderer_and_catalog_show_only_true_update_date_original_core_unchanged(self):
        old,item=fixture();issue=copy.deepcopy(old);issue['conference_calls'].append(item)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);records=json.loads((ROOT/'config/website-content.json').read_text(encoding='utf-8'))
            records[item['id']]=dict(source_sha256=fingerprint(item),summary=item['page_note'])
            write(root/'config/website-content.json',records)
            with patch('website_content.ROOT',root),patch('render_issue_pages.render_promotion',return_value=''),patch('public_history.collections',return_value=[]):
                original_core=render_section(old,'core','本期重点')
                self.assertEqual(render_section(issue,'core','本期重点'),original_core)
                page=render_page(issue)
                self.assertEqual(page.count('更新：2026-11-11'),1)
                self.assertNotIn('D-20261111-02',page);self.assertNotIn('evaluated_at',page)
                row=next(row for row in entries([issue]) if row['id']==item['id'])
                output=card(row)
                self.assertIn('更新：2026-11-11',output)
                self.assertIn('../issues/20261108/#'+item['id'],output)
                self.assertIn('期次日期：2026-11-08',output)
                ordinary=next(row for row in entries([issue]) if row['id']!=item['id'])
                self.assertNotIn('website-update',card(ordinary))
        errors=[];validate_wechat(issue,ROOT/'publish/wechat',errors)
        self.assertEqual(errors,[])


if __name__=='__main__':unittest.main()
