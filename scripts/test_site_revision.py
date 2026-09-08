"""D-20260908-02 的反例与端到端事实检查。"""
import copy, json, unittest, hashlib, tempfile
from pathlib import Path
from website_rules import check_website, discovery_errors, conference_errors
from website_citations import arxiv_pdf, format_myapa, bibliography_metadata
from public_history import collections, resolve, validate_collection
from build_catalog_pages import entries, public_issues
from validate_issue import validate_wechat
from trial_selection import assess
ROOT=Path(__file__).resolve().parents[1]

def issue():return json.loads((ROOT/'content/issues/2026-09-08.json').read_text(encoding='utf-8'))
class SiteRevisionTests(unittest.TestCase):
    def test_demo_preserves_source_links_without_public_indexing(self):
        from render_issue_pages import render_page
        for p in (ROOT/'content/issues').glob('*demo*.json'):
            data=json.loads(p.read_text(encoding='utf-8'));page=render_page(data)
            self.assertIn('search: false',page)
            for item in data.get('papers',[]):self.assertIn(item.get('doi_url') or item.get('homepage_url'),page)

    def test_real_daily_counts(self):
        for i in public_issues():
            if i['issue_type']!='daily':continue
            self.assertEqual(check_website(i,ROOT),[])
            items=[x for k in ('lianxh_posts','papers','tools','research_resources','conference_calls') for x in i.get(k,[])]
            self.assertEqual(len(items),12)
    def test_four_core_fails(self):
        i=issue()
        for k in ('lianxh_posts','papers','tools','conference_calls'):i[k]=[x for x in i[k] if x['priority']=='core']
        self.assertTrue(any('不足 10' in e for e in check_website(i)))
    def test_short_issue_requires_real_draft(self):
        i=issue();i['papers']=i['papers'][:2];i['tools']=[];i['conference_calls']=[]
        i['short_issue']=dict(reason='充分检索后仅 4 条合格',actual_count=4,searched_sufficiently=True,draft_path='draft.json',draft_sha256='x')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'draft.json';p.write_text(json.dumps(i),encoding='utf-8')
            self.assertTrue(check_website(i,d))
            i['short_issue']['draft_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(check_website(i,d),[])
            i['discovery']=[r for r in i['discovery'] if r['category']!='software']
            self.assertTrue(check_website(i,d))
    def test_total_upper_and_duplicate(self):
        i=issue();i['papers']+=copy.deepcopy(i['papers'])
        errors=check_website(i)
        self.assertTrue(any('最多' in e for e in errors));self.assertTrue(any('重复' in e for e in errors))
    def test_arxiv_derived_without_network(self):
        self.assertEqual(arxiv_pdf(dict(doi_url='https://doi.org/10.48550/arXiv.2609.05372')),'https://arxiv.org/pdf/2609.05372.pdf')
        m=issue()['papers'][0]['bibliography'];m.pop('pdf')
        self.assertIn('>PDF<',format_myapa(m))
        with self.assertRaises(ValueError):arxiv_pdf(dict(arxiv_id='2609.05372',homepage_url='https://arxiv.org/abs/2609.01467'))
        i=issue();i['papers'][0].pop('pdf_url');self.assertTrue(check_website(i))
    def test_native_bibliography_drift(self):
        for field,value in [('title','An unrelated title'),('authors',['Wrong, A.']),('doi_url','https://doi.org/10.1/incorrect')]:
            item=issue()['papers'][0];item['bibliography'][field]=value
            with self.assertRaises(ValueError):bibliography_metadata(item)
    def test_discovery_states_are_distinct(self):
        records=issue()['discovery'];self.assertEqual(discovery_errors(records),[])
        records[-1]['adopted_count']=1
        self.assertTrue(discovery_errors(records))
        records=issue()['discovery'];records[0]['status']='not-searched'
        self.assertTrue(discovery_errors(records))
    def test_tags_required(self):
        i=issue();i['lianxh_posts'][0]['catalog']['tags']=[]
        self.assertTrue(any('标签' in e for e in check_website(i)))
    def test_conference_valid_expired_and_reminder(self):
        c=issue()['conference_calls'][0];self.assertEqual(conference_errors(c,'2026-09-08'),[])
        self.assertTrue(conference_errors(c,'2026-11-09'))
        c['reminder']=True;self.assertTrue(conference_errors(c,'2026-10-12'))
        first=copy.deepcopy(c);first['reminder']=False;first['events']=[dict(kind='website',date='2026-09-08',evidence='published issue')]
        c['previous_id']=first['id'];self.assertEqual(conference_errors(c,'2026-10-12',[first]),[])
        first['reminder']=True;self.assertTrue(conference_errors(c,'2026-10-12',[first]))
    def test_conference_assess_no_blanket_rejection(self):
        c=issue()['conference_calls'][0]
        c['review']=dict(source_id='host',source_url=c['official_url'],version_read='第一轮',date_basis='通知日期',evidence_locator='官方通知',identity_evidence='主办方与年份',evidence_level='official-page',version_matches=True,identity_status='resolved',human_review='pending',effective_date=c['published_date'],verified_at='2026-09-08T12:00:00+08:00')
        self.assertEqual(assess(c,'conference_calls',[],'2026-09-08T13:00:00+08:00'),[])
    def test_history_is_shared_and_indexed(self):
        slug,data=collections()[0]
        self.assertEqual(validate_collection(data),[])
        self.assertEqual(len(data['entries']),48)
        self.assertEqual({r['category'] for r in data['entries']},{'lianxh_posts','papers','tools','conference_calls'})
        values=entries(public_issues());self.assertEqual(len({i['id'] for i in values}),len(values))
        self.assertTrue(any(i['id']=='arxiv-2608-31085' and i.get('history_slug') for i in values))
        self.assertFalse(any('ai-agent-data-analysis'==i['id'] for i in values))
        for row in data['entries']:
            if row.get('source_file'): self.assertNotIn('payload',row)
    def test_backfill_dates_and_stata_window(self):
        i=issue();tool=i['tools'][0]
        tool['release_date']=tool['published_date']='2026-07-08'
        self.assertEqual(check_website(i),[])
        tool['release_date']=tool['published_date']='2026-07-07'
        self.assertTrue(any('时效' in e for e in check_website(i)))
        i=issue();i['papers'][-1]['published_date']='2026-09-09'
        self.assertTrue(any('倒填' in e for e in check_website(i)))

    def test_conference_pipeline_reports_actual_counts(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from subprocess import CompletedProcess
        from isolated_trial import run
        for count in (0,1,2,3,4):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as d:
                root=Path(d);observed=root/'observed.json';observed.write_text('[]',encoding='utf-8')
                candidates=[]
                for n in range(count):
                    c=copy.deepcopy(issue()['conference_calls'][0])
                    c.update(id='fixture-event-'+str(n),event_id='fixture-'+str(n),title='测试会议 '+str(n),official_url='https://example.org/event/'+str(n))
                    c['review']=dict(source_id='fixture',source_url=c['official_url'],version_read='v1',date_basis='official',evidence_locator='fixture',identity_evidence='fixture identity',evidence_level='official-page',version_matches=True,identity_status='resolved',human_review='pending',effective_date=c['published_date'],verified_at='2026-09-08T12:00:00+08:00')
                    candidates.append(dict(id=c['id'],kind='conference',payload=c,status='eligible',core_or_extended='core'))
                data=dict(as_of='2026-09-08T13:00:00+08:00',history=[],candidates=candidates,coverage={},observed_posts_sha256=hashlib.sha256(observed.read_bytes()).hexdigest())
                source=root/'sources.json';source.write_text('[{"id":"fixture"}]',encoding='utf-8')
                snapshot=root/'snapshot.json';snapshot.write_text(json.dumps(data),encoding='utf-8')
                args=SimpleNamespace(as_of=data['as_of'],snapshot=snapshot,sources=source,observed_posts=observed,output_root=root/'out',mode='conference')
                # 独立验证选稿到页面/TXT；Quarto 本身由全站真实构建验收。
                with patch('isolated_trial.forbidden_paths',return_value=[ROOT]), patch('isolated_trial.subprocess.run',return_value=CompletedProcess([],0,'','')):
                    result=run(args)
                self.assertEqual(result['conference_eligible_count'],count)
                self.assertEqual(bool(result['errors']),count not in (2,3),result['errors'])
                self.assertEqual(result['release_status'],'no-release')
                self.assertTrue((root/'out/draft/issue.json').exists())

    def test_original_wechat_remains_verifiable(self):
        for day in ('2026-09-05','2026-09-08'):
            i=json.loads((ROOT/'content/issues'/f'{day}.json').read_text(encoding='utf-8'));errors=[]
            validate_wechat(i,ROOT/'publish/wechat',errors);self.assertEqual(errors,[])
if __name__=='__main__':unittest.main()
