"""C-28/U-19：作者边界、日期精度与统一卡片回归检查。"""
import unittest
from unittest.mock import patch
from website_citations import catalog_citation
from build_catalog_pages import card

class CitationCards(unittest.TestCase):
    def render(self, authors, **fields):
        metadata = dict(authors=authors,year=2026,title='Original title',source='Journal of Finance')
        with patch('website_citations.bibliography_metadata',return_value=metadata):
            return catalog_citation(dict(publication_status='published',**fields),'2026-10-15')
    def test_authors_and_abbreviation(self):
        self.assertIn('A; B; C (2026)',self.render(['A','B','C']))
        four=self.render(['A','B','C','D'])
        self.assertIn('A et al.',four)
        self.assertNotIn('; B',four)
        self.assertIn('JF.',four)
    def test_dates_do_not_invent_precision(self):
        partial=self.render(['A'],published_date='2026-10')
        self.assertIn('发表日期：2026-10 · 收录日期：2026-10-15',partial)
        self.assertIn('发表日期：待核',self.render(['A']))
    def test_working_paper_and_escaping(self):
        m=dict(authors=['<A>'],year=2026,title='Title & method',source='NBER')
        with patch('website_citations.bibliography_metadata',return_value=m):
            text=catalog_citation(dict(publication_status='working-paper',published_date='2026-10-12'))
        self.assertIn('Working paper',text)
        self.assertIn('提交/版本日期',text)
        self.assertIn('&lt;A&gt;',text)
        self.assertIn('收录日期：待核',text)
    def test_history_and_daily_use_same_metadata(self):
        e=dict(id='test',date='2026-09-01',title='中文标题',note='摘要',catalog=dict(tags=[],software=[],methods=[],fields=[]),paper_metadata='<p>verified citation</p>')
        self.assertIn('verified citation',card(e))
        self.assertIn('verified citation',card(dict(e,history_slug='history')))

class CourseBanners(unittest.TestCase):
    def test_dimensions_and_text_fallback(self):
        from website_promotions import render_home_promotion
        from datetime import date
        item=dict(id='reviewed',title='课程',url='https://www.lianxh.cn/details/1940.html',
                  dates=['2026-11-28'],course_start_date='2026-11-28',course_end_date='2026-11-28',
                  status='confirmed',review_status='approved',reviewed_date='2026-10-15',
                  source_url='https://www.lianxh.cn/details/1940.html',evidence='official',
                  links=[dict(url='https://www.lianxh.cn/details/1940.html',availability='confirmed')],
                  poster='https://example.org/banner.png',poster_width=1500,poster_height=400)
        text_item=dict(item,id='text-only');text_item.pop('poster')
        config=dict(approved_courses=[item,text_item])
        text=render_home_promotion(config,date(2026,10,15))
        self.assertIn('width="1500" height="400"',text)
        self.assertIn('course-mobile-card',text)
        self.assertIn('2026-11-28',text)
        self.assertIn('details/1940.html',text)
        self.assertIn('course-text-card',text)

if __name__=='__main__': unittest.main()
