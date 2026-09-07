"""历史集合的边界、模式、独立登记与后续状态回归测试。"""
import copy
import unittest
from historical_collection import validate_collection, carry_followups, render_collection
from trial_selection import exact_date, assess

class HistoricalTests(unittest.TestCase):
    def setUp(self):
        self.o=[{'id':'post-a','title':'题名','url':'https://example.org/a','author':'作者','display_date':'2026-08-15'}]
        self.d={'type':'historical-collection','range_start':'2026-08-15','range_end':'2026-09-07',
            'checked_at':'2026-09-07T19:00:00+08:00','added_at':'2026-09-08T09:00:00+08:00',
            'human_review':'pending','release_status':'no-release','events':[],
            'post_register':[dict(self.o[0],decision='proposed',reason='已读正文')],
            'entries':[{'category':'lianxh_posts','payload':{'id':'post-a','title':'题名','url':'https://example.org/a','page_note':'阅读导引'},
                'source_date':'2026-08-15','date_kind':'page-display','date_evidence':'目录与正文','verified_at':'2026-09-07T18:00:00+08:00',
                'evidence_locator':'正文第 1 节','historical_value':'教学用途','decision':'proposed'}]}
    def test_inclusive_range(self):
        for day in ('2026-08-15','2026-09-07'):
            self.d['entries'][0]['source_date']=day
            self.o[0]['display_date']=day
            self.d['post_register'][0]['display_date']=day
            self.assertEqual(validate_collection(self.d,self.o,[]),[])
        for day in ('2026-08-14','2026-09-08'):
            self.d['entries'][0]['source_date']=day
            self.assertTrue(validate_collection(self.d,self.o,[]))
    def test_month_and_discovery_rejected(self):
        self.d['entries'][0]['source_date']='2026-08'
        self.assertTrue(validate_collection(self.d,self.o,[]))
        self.d['entries'][0]['source_date']='2026-08-15'
        self.d['entries'][0]['date_kind']='discovery'
        self.assertTrue(validate_collection(self.d,self.o,[]))
    def test_daily_mode_not_accepted(self):
        self.d['type']='daily'
        self.assertTrue(validate_collection(self.d,self.o,[]))
    def test_publish_event_rejected(self):
        self.d['events']=[{'kind':'website'}]
        self.assertTrue(validate_collection(self.d,self.o,[]))
    def test_register_omission_and_mutation(self):
        self.assertTrue(validate_collection(self.d,[],[]))
        self.d['post_register'][0]['display_date']='2026-09-01'
        self.assertTrue(validate_collection(self.d,self.o,[]))
    def test_identity_version_duplicate(self):
        second=copy.deepcopy(self.d['entries'][0]);second['payload']['id']='post-b'
        self.d['entries'].append(second)
        self.assertTrue(validate_collection(self.d,self.o,[]))
    def test_link_paper_to_post_instead_of_duplicate(self):
        self.d['entries'][0]['payload']['related_work']='arxiv:2608.31059'
        paper=copy.deepcopy(self.d['entries'][0]);paper['category']='papers'
        paper['payload']={'id':'paper-a','title':'English title','arxiv_id':'2608.31059v2','page_note':'主题','homepage_url':'https://arxiv.org/abs/2608.31059v2'}
        self.d['entries'].append(paper)
        self.assertTrue(validate_collection(self.d,self.o,[]))
    def test_formal_versus_verified(self):
        h=[dict(self.d['entries'][0]['payload'],events=[{'kind':'verified','date':'2026-09-01','evidence':'note'}])]
        self.assertEqual(validate_collection(self.d,self.o,h),[])
        h[0]['events'][0]['kind']='website'
        self.assertTrue(validate_collection(self.d,self.o,h))
        self.d['post_register'][0]['decision']='reuse'
        self.d['entries'][0].update(decision='reuse',existing_website_url='https://example.org/published')
        self.assertEqual(validate_collection(self.d,self.o,h),[])
    def test_followup_survives_endpoint(self):
        rows=[dict(self.o[0],decision='deferred',wechat_short_status='unknown',sent_status='unknown')]
        result=carry_followups(rows,[],'2026-10-01T09:00:00+08:00')
        self.assertEqual(len(result),1);self.assertEqual(result[0]['decision'],'deferred')
        self.assertEqual(result[0]['wechat_short_status'],'unknown')
        self.assertNotIn('last_checked_at',rows[0])
    def test_only_formal_short_changes_status(self):
        rows=[dict(self.o[0],wechat_short_status='unknown',sent_status='unknown')]
        for kind,evidence in [('website','page'),('verified','note'),('wechat_short','')]:
            h=[dict(self.o[0],events=[{'kind':kind,'date':'2026-09-07','evidence':evidence}])]
            self.assertEqual(carry_followups(rows,h,'2026-09-08T09:00:00+08:00')[0]['wechat_short_status'],'unknown')
        h=[dict(self.o[0],events=[{'kind':'wechat_short','date':'2026-09-08','evidence':'formal.txt','sha256':'fixture'}])]
        r=carry_followups(rows,h,'2026-09-08T09:00:00+08:00')[0]
        self.assertEqual(r['wechat_short_status'],'confirmed-formal-short');self.assertEqual(r['sent_status'],'unknown')
    def test_render_not_daily_issue(self):
        page=render_collection(self.d)
        self.assertIn('历史精选',page);self.assertIn('2026-09-08T09:00',page)
        self.assertNotIn('本期重点',page);self.assertIn('noindex,nofollow',page)

if __name__=='__main__': unittest.main()
