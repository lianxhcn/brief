import unittest
from website_content import inline_code
from build_catalog_pages import public_issues, entries, card
from render_issue_pages import render_page
from public_history import collections, render_collection

class ReadabilityTests(unittest.TestCase):
    def test_code_is_safe(self):
        self.assertEqual(inline_code('安装 `ssc install xtbfkbreak`'), '安装 <code>ssc install xtbfkbreak</code>')
        self.assertEqual(inline_code('<script>`<b>`'), '&lt;script&gt;<code>&lt;b&gt;</code>')

    def test_revision_notes_stay_internal(self):
        for issue in public_issues():
            if issue.get('revision_note'): self.assertNotIn(issue['revision_note'], render_page(issue))
        for slug, data in collections():
            page=render_collection(data)
            self.assertNotIn(data['revision_note'],page)
            self.assertNotIn('发送群消息',page)

    def test_command_formatting_in_all_views(self):
        pages=''.join(render_page(i) for i in public_issues())
        catalogs=''.join(card(i) for i in entries(public_issues()))
        history=''.join(render_collection(d) for _,d in collections())
        for text in (pages,catalogs,history):
            self.assertIn('<code>ssc install xtbfkbreak</code>',text)
            self.assertIn('<code>ssc install lwdid</code>',text)
