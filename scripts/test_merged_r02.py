"""R02 合并补正；所有内容及事件为 synthetic fixture。"""
import copy
import unittest
from unittest.mock import patch
from lianxh_exclusions import screen_post, normalized_url
from trial_selection import assess
from historical_collection import validate_collection, carry_followups
from coverage_rules import coverage_errors
from build_local_draft import assemble_daily_issue
from test_isolated_trial import complete_coverage, ASOF
import test_historical_collection as historical_fixture

class MergedTests(unittest.TestCase):
    def post(self, number='17', **kw):
        return dict(id='post-'+number, url='https://www.lianxh.cn/details/'+number+'.html', **kw)
    def test_fixed_url_variants_before_invalid_date(self):
        for host in ('www.lianxh.cn','lianxh.cn'):
            for protocol in ('http','https'):
                for tail in ('','?tracking=1','#top','?x=1#top'):
                    item=dict(id='alias',url=f'{protocol}://{host}/details/17.html{tail}',published_date='2099-01-01')
                    self.assertEqual(screen_post(item)['action'],'excluded')
                    with patch('trial_selection.evaluation', side_effect=AssertionError('date evaluated')):
                        self.assertEqual(assess(item,'lianxh_posts',[],'invalid'),['fixed'])
    def test_fixed_id_without_url_scoped(self):
        self.assertEqual(screen_post(dict(id='post-17',source_id='lianxh'))['action'],'excluded')
        self.assertEqual(screen_post(dict(id='post-17',source_id='foreign'))['action'],'retain')
    def test_cross_domain_not_excluded(self):
        for host in ('example.org','lianxh.cn.example.org'):
            self.assertEqual(screen_post(dict(id='post-17',url=f'https://{host}/details/17.html'))['action'],'retain')
    def test_confirmed_promotion_cases(self):
        for n in ('1900','1919','1923'):
            for day in ('2026-09-07','2099-01-01','unknown'):
                self.assertEqual(screen_post(self.post(n,published_date=day))['action'],'excluded')
    def test_research_keyword_and_pinned_negatives(self):
        for kind,title in [('lecture-notes','公开课课程讲义'),('recruitment-data-research','招聘数据研究'),('software-tutorial','软件教程')]:
            item=self.post('999',title=title,pinned=True,content_classification=dict(status='confirmed',kind=kind,evidence='synthetic body'))
            self.assertEqual(screen_post(item)['action'],'retain')
        self.assertEqual(screen_post(self.post('1920',pinned=True))['action'],'retain')
    def test_keywords_only_require_review(self):
        self.assertEqual(screen_post(self.post('999',title='公开课预告'))['action'],'review')
    def test_evergreen_requires_no_change_evidence(self):
        item=self.post('999',published_date='2099-01-01',content_classification=dict(status='confirmed',kind='evergreen',evidence='synthetic same body/version',no_substantive_change=True))
        self.assertEqual(screen_post(item)['action'],'excluded')
        item['content_classification'].pop('evidence')
        self.assertEqual(screen_post(item)['action'],'retain')
    def test_c08_excluded_does_not_count_or_parse_date(self):
        post=dict(self.post(),date='unknown');c=complete_coverage()
        c['post_records']=[dict(post,decision='excluded',reason='fixed',evidence='synthetic user rule')]
        self.assertEqual(coverage_errors(c,[],ASOF,[post]),[])
        for field in ('required_post_ids','unresolved_posts'):
            bad=copy.deepcopy(c);bad[field]=['post-17']
            self.assertTrue(coverage_errors(bad,[],ASOF,[post]))
        for decision in ('proposed','pending','already-short'):
            bad=copy.deepcopy(c);bad['post_records'][0]['decision']=decision
            self.assertTrue(coverage_errors(bad,[],ASOF,[post]))
    def test_daily_assembly_excludes_before_count(self):
        result=assemble_daily_issue('2026-09-07',[dict(kind='post',core_or_extended='core',payload=self.post())])
        self.assertEqual(result['lianxh_posts'],[])
    def test_followups_reject_excluded_preserve_history(self):
        history=[dict(self.post(),events=[dict(kind='wechat_short',date='2026-09-01',evidence='synthetic')])]
        old=copy.deepcopy(history)
        with self.assertRaises(ValueError):carry_followups([self.post()],history,ASOF)
        self.assertEqual(history,old)
    def fixture(self):
        h=historical_fixture.HistoricalTests();h.setUp();return h.d,h.o
    def test_entry_date_mutation_rejected(self):
        d,o=self.fixture();d['entries'][0]['source_date']='2026-09-07'
        self.assertTrue(validate_collection(d,o,[]))
    def test_entry_title_mutation_rejected(self):
        d,o=self.fixture();d['entries'][0]['payload']['title']='other'
        self.assertTrue(validate_collection(d,o,[]))
    def test_entry_url_mutation_rejected(self):
        d,o=self.fixture();d['entries'][0]['payload']['url']='https://example.org/other'
        self.assertTrue(validate_collection(d,o,[]))
    def test_same_id_different_payload_rejected(self):
        d,o=self.fixture();entry=copy.deepcopy(d['entries'][0]);entry['category']='papers';entry['payload'].update(title='different',url='https://example.org/different');d['entries'].append(entry)
        self.assertTrue(any('entry ID' in e for e in validate_collection(d,o,[])))
    def test_other_date_kind_not_forced_to_display(self):
        d,o=self.fixture();d['entries'][0].update(date_kind='first-public',source_date='2026-08-16',date_evidence='synthetic original publication record')
        self.assertEqual(validate_collection(d,o,[]),[])
    def test_normalized_entry_url(self):
        d,o=self.fixture();o[0]['url']='https://www.lianxh.cn/details/999.html';d['post_register'][0]['url']=o[0]['url'];d['entries'][0]['payload']['url']='http://lianxh.cn/details/999.html?x=1#top'
        self.assertEqual(validate_collection(d,o,[]),[])
    def test_historical_entry_shared_gate(self):
        d,o=self.fixture();p=self.post();o[0].update(p);d['post_register'][0].update(p);d['entries'][0]['payload'].update(p)
        self.assertTrue(any('fixed' in e for e in validate_collection(d,o,[])))

if __name__=='__main__': unittest.main()
