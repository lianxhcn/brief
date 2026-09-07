"""新版编辑约束的正反例测试，无网络、无文件写入。"""
import copy
import unittest
from build_local_draft import daily_issue
from editorial_rules import check_editorial, uses_v2
from render_wechat import render_daily, title_line

def fixture():
    common = dict(priority="core", title="示例", wechat_summary="提要测试",
                  page_note="说明", retrieved_date="2026-09-05")
    paper = dict(common, id="paper-one", journal="American Economic Review",
                 publication_status="published", published_date="2026-08",
                 citation="Author (2026). Paper. AER.", doi_url="https://doi.org/10.1/test",
                 homepage_url="https://example.org/paper", pdf_url="https://example.org/paper.pdf",
                 pdf_version="作者稿", bibliography=dict(
                     authors=["Author, A."], year=2026, title="Paper",
                     source="American Economic Review", publication_status="published",
                     pdf=dict(url="https://example.org/paper.pdf", public_access=True,
                              source_url="https://example.org/paper", retrieved_date="2026-09-05",
                              version="作者稿")))
    tool = dict(common, id="tool-one", ecosystem="R", name="tool", version="1.0",
                release_date="2026-08-21", source_url="https://example.org/tool",
                url="https://example.org/tool")
    return dict(date="2026-09-05", status="draft", issue_type="daily", editorial_version=2,
                papers=[paper], tools=[tool], lianxh_posts=[dict(common, id="post-one", url="https://example.org/post")])

class EditorialTests(unittest.TestCase):
    def test_valid_and_separate_lines(self):
        issue = fixture()
        self.assertEqual(check_editorial(issue), [])
        lines = render_daily(issue).splitlines()
        self.assertEqual(lines[0], "📙 连享会 · 快讯 | 2026.09.05")
        self.assertIn("提要测试", lines)
        self.assertIn("引文：Author (2026). Paper. AER.", lines)

    def test_missing_formal_software_pdf(self):
        for category, field in [("papers", "publication_status"), ("tools", "version"), ("papers", "homepage_url")]:
            issue = fixture()
            del issue[category][0][field]
            self.assertTrue(check_editorial(issue))

    def test_working_paper_does_not_count_as_formal(self):
        issue = fixture()
        issue["papers"][0]["publication_status"] = "working-paper"
        self.assertTrue(check_editorial(issue))

    def test_too_few_or_many(self):
        issue = fixture()
        issue["lianxh_posts"] = []
        self.assertTrue(check_editorial(issue))
        issue = fixture()
        issue["lianxh_posts"] *= 4
        with self.assertRaises(ValueError):
            render_daily(issue)

    def test_conference_optional_but_counted(self):
        issue = fixture()
        issue["conference_calls"] = [issue["lianxh_posts"].pop()]
        self.assertEqual(check_editorial(issue), [])

    def test_future_release_rejected(self):
        issue = fixture()
        issue["tools"][0]["release_date"] = "2026-09-06"
        self.assertTrue(check_editorial(issue))

    def test_published_v2_and_legacy(self):
        issue = fixture()
        issue["status"] = "published"
        self.assertTrue(uses_v2(issue))
        del issue["editorial_version"]
        self.assertFalse(uses_v2(issue))
        self.assertEqual(title_line(issue), "连享会快讯 · 2026.09.05")

    def test_mixed_builder(self):
        issue = fixture()
        ledger = [{"kind": kind, "core_or_extended": "core", "payload": issue[category][0]}
                  for kind, category in [("paper", "papers"), ("tool", "tools"), ("post", "lianxh_posts")]]
        self.assertEqual(len(daily_issue("2026-09-05", ledger)["papers"]), 1)

if __name__ == "__main__":
    unittest.main()
