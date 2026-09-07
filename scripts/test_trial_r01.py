"""R01 有意义反例：覆盖伪完成、渠道语义与分类窗口。"""
import copy
import unittest
from pathlib import Path
from test_isolated_trial import ASOF, verified, complete_coverage
from trial_selection import assess
from coverage_rules import coverage_errors
from website_citations import format_myapa


class R01Tests(unittest.TestCase):
    def test_unknown_baseline_cannot_be_complete(self):
        c=complete_coverage(); c.update(baseline=None,baseline_evidence='没有明确覆盖点，unknown')
        self.assertTrue(coverage_errors(c,[],ASOF,[]))

    def test_endpoint_and_interval(self):
        for change in [dict(checked_to='2026-09-07T19:00:00+08:00'),dict(checked_to='2026-09-06T18:00:00+08:00'),dict(baseline='2026-09-08T00:00:00+08:00')]:
            c=complete_coverage(); c.update(change)
            self.assertTrue(coverage_errors(c,[],ASOF,[]))

    def test_dropped_unresolved_or_row(self):
        post=dict(id='p',url='https://example.org/p',date='2026-09-04')
        c=complete_coverage(); c['post_records']=[dict(post,decision='pending',reason='日期含义不明')]
        self.assertTrue(any('unresolved_posts' in e for e in coverage_errors(c,[],ASOF,[post])))
        c['post_records']=[]
        self.assertTrue(any('观察目录' in e for e in coverage_errors(c,[],ASOF,[post])))

    def test_verified_only_not_publication(self):
        item=verified()
        old=dict(item,events=[dict(kind='verified',date='2026-09-06',evidence='candidate ledger')])
        self.assertEqual(assess(item,'papers',[old],ASOF),[])
        old['events']=[dict(kind='git_snapshot',date='2026-09-06',evidence='unapproved version')]
        self.assertEqual(assess(item,'papers',[old],ASOF),[])

    def test_website_extended_post_not_short(self):
        post=verified(); post.update(id='post',url='https://example.org/post')
        old=dict(post,events=[dict(kind='website',date='2026-09-04',priority='extended',evidence='formal page')])
        self.assertEqual(assess(post,'lianxh_posts',[old],ASOF),[])
        observed=dict(id='post',url=post['url'],date='2026-09-04')
        c=complete_coverage(); c['post_records']=[dict(observed,decision='already-short')]
        self.assertTrue(coverage_errors(c,[],ASOF,[observed],[old]))
        old['events'].append(dict(kind='wechat_short',date='2026-09-04',evidence='formal TXT URL'))
        self.assertTrue(assess(post,'lianxh_posts',[old],ASOF))
        self.assertEqual(coverage_errors(c,[],ASOF,[observed],[old]),[])
        old['events'][-1]['date']='2026-09-08'
        self.assertTrue(coverage_errors(c,[],ASOF,[observed],[old]))

    def test_extended_paper_remains_long_term_seen(self):
        paper=verified()
        old=dict(paper,events=[dict(kind='website',priority='extended',date='2026-07-01',evidence='formal website')])
        self.assertTrue(assess(paper,'papers',[old],ASOF))

    def test_old_post_in_coverage_not_paper_window(self):
        post=verified(); post.update(id='post',url='https://example.org/post',published_date='2026-08-01')
        post['review']['effective_date']='2026-08-01'
        self.assertEqual(assess(post,'lianxh_posts',[],ASOF),[])
        self.assertTrue(assess(post,'papers',[],ASOF))
        observed=dict(id='post',url=post['url'],date='2026-08-01')
        c=complete_coverage(); c['baseline']='2026-07-01T00:00:00+08:00'
        c['baseline_evidence']['coverage_through']=c['baseline']
        c.update(required_post_ids=['post'],post_records=[dict(observed,decision='proposed',reason='暂停期间未进入短版的新推文')])
        self.assertEqual(coverage_errors(c,['post'],ASOF,[observed]),[])

    def test_resource_uses_value_not_paper_cutoff(self):
        item=verified(); item['published_date']='2026-08-01'
        item['review'].update(effective_date='2026-08-01',resource_use='practice-case',timeliness_reason='当前研究任务的实践案例，保留真实日期')
        self.assertEqual(assess(item,'research_resources',[],ASOF),[])
        item['review']['resource_use']='background-tutorial'
        self.assertTrue(assess(item,'research_resources',[],ASOF))

    def test_title_terminal_punctuation(self):
        m=dict(authors=['Cai, Y.'],year=2026,source='arXiv')
        for title in ('Does this change publication bias?', 'A result!', 'A result.', 'A result'):
            rendered=format_myapa(dict(m,title=title))
            self.assertNotIn('?.',rendered); self.assertNotIn('!.',rendered)
            expected=title if title[-1] in '.?!' else title+'.'
            self.assertIn(expected+' arXiv.',rendered)

if __name__=='__main__': unittest.main()
