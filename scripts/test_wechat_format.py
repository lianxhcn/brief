"""Task 10 独立正反例：隔离数据，不改正式期次，不联网。"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from test_editorial_rules import fixture
from editorial_rules import check_editorial, core_items
from build_local_draft import daily_issue
from render_wechat import render_daily, title_line
from validate_issue import validate_wechat, validate_schema
from wechat_format import item_heading, short_authors
from website_citations import website_citation

ROOT = Path(__file__).resolve().parents[1]


def sample():
    issue = fixture()
    issue.update(issue_id='fixture-only', title='隔离测试')
    for category, item in core_items(issue):
        item['title'] = {'papers': 'AER：论文测试', 'tools': 'R：工具测试', 'lianxh_posts': '新推文测试'}[category]
        item['catalog'] = dict(section={'papers': 'research-frontier', 'tools': 'methods-tools',
                                       'lianxh_posts': 'lianxh-new'}[category],
                               software=[], methods=[], fields=[], tags=[])
    return issue


def add(issue, category):
    item = copy.deepcopy(issue[category][0])
    item['id'] += '-two'
    item['title'] += '第二条'
    for key in ('url', 'homepage_url', 'doi_url'):
        if item.get(key):
            item[key] += '-two'
    issue[category].append(item)


def conference():
    return dict(id='meeting', title='测试征稿', priority='core', topic='已核验主题',
                organizer_or_journal='测试主办方', deadline='2026-10-15',
                official_url='https://example.org/call', retrieved_date='2026-09-05',
                page_note='已审核说明', catalog=dict(section='academic-updates', software=[], methods=[], fields=[], tags=[]))


class WechatTests(unittest.TestCase):
    def validate(self, issue, text=None, legacy=False):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / (issue['date'] + '.txt')
            p.write_text(render_daily(issue) if text is None else text, encoding='utf-8')
            errors = []
            validate_wechat(issue, p.parent, errors, legacy=legacy)
            return errors

    def assert_valid(self, issue):
        before = copy.deepcopy(issue)
        errors = []
        validate_schema(issue, Path('isolated-fixture.json'), errors)
        self.assertEqual(errors, [])
        self.assertEqual(self.validate(issue), [])
        self.assertEqual(issue, before)

    def test_compositions_and_priority(self):
        for posts, papers, tools in ((1, 1, 1), (1, 2, 1), (2, 2, 1), (1, 2, 2)):
            with self.subTest(posts=posts, papers=papers, tools=tools):
                issue = sample()
                for count, category in ((posts, 'lianxh_posts'), (papers, 'papers'), (tools, 'tools')):
                    if count == 2:
                        add(issue, category)
                self.assert_valid(issue)
                self.assertTrue(render_daily(issue).split('\n\n')[1].startswith('✍️ 01｜新推文：'))

    def test_optional_conference_fallback_and_resource(self):
        issue = sample()
        issue['conference_calls'] = [conference()]
        self.assert_valid(issue)
        self.assertIn('📅 04｜会议征稿：测试征稿', render_daily(issue))
        self.assertIn('主题或范围：已核验主题；截止日期：2026-10-15', render_daily(issue))
        resource = copy.deepcopy(issue['lianxh_posts'][0])
        resource.update(id='resource', title='数据档案', url='https://example.org/resource',
                        catalog=dict(section='methods-tools', software=[], methods=[], fields=[], tags=[]))
        issue['research_resources'] = [resource]
        self.assert_valid(issue)
        self.assertIn('📦 04｜资源：数据档案', render_daily(issue))
        self.assertIn('📅 05｜会议征稿：测试征稿', render_daily(issue))

    def test_no_pdf_and_unreliable_pdf(self):
        for mode in ('absent', 'not-public', 'no-evidence'):
            issue = sample()
            paper = issue['papers'][0]
            if mode == 'absent':
                del paper['pdf_url'], paper['pdf_version'], paper['bibliography']['pdf']
            elif mode == 'not-public':
                paper['bibliography']['pdf']['public_access'] = False
            else:
                del paper['bibliography']['pdf']['retrieved_date']
            self.assert_valid(issue)
            self.assertNotIn('PDF', render_daily(issue))

    def test_citation_status_authors_and_main_title(self):
        for status in ('published', 'forthcoming'):
            issue = sample()
            paper = issue['papers'][0]
            paper['publication_status'] = status
            m = paper['bibliography']
            m.update(publication_status=status, authors=['Alpha, A.', 'Beta, B.', 'Gamma, C.', 'Delta, D.'],
                     title='Main title: Subtitle', main_title='Main title')
            self.assert_valid(issue)
            text = render_daily(issue)
            self.assertIn('引文：Alpha et al. (2026). Main title. AER', text)
            self.assertNotIn('Subtitle', text)
            self.assertEqual('forthcoming' in text, status == 'forthcoming')
            self.assertIn('Main title: Subtitle', website_citation(paper))
        self.assertEqual(short_authors(['van der Meer, A.', 'Smith-Jones, B.']), 'van der Meer & Smith-Jones')
        self.assertEqual(short_authors(['A, X.', 'B, Y.', 'C, Z.']), 'A, B & C')
        for authors in (['First Last'], ['Last First'], [], [{'family': 'Name'}]):
            with self.assertRaises(ValueError):
                short_authors(authors)

    def test_source_prefix_and_labels(self):
        issue = sample()
        self.assertIn('📰 02｜论文 · AER：论文测试', render_daily(issue))
        self.assertIn('📦 03｜软件 · R：工具测试', render_daily(issue))
        for host, label in (('cran.r-project.org', 'CRAN'), ('pypi.org', 'PyPI'), ('github.com', 'GitHub'),
                            ('unknown.example', '主页')):
            with self.subTest(host=host):
                issue['tools'][0]['url'] = 'https://' + host + '/package'
                self.assert_valid(issue)
                self.assertIn(label + '： https://' + host + '/package ', render_daily(issue))
        self.assertEqual(item_heading('tools', dict(title='Stata：命令测试', ecosystem='Stata'), 1), '📦 01｜命令 · Stata：命令测试')
        self.assertEqual(item_heading('lianxh_posts', dict(title='标题', source_name='连享会'), 1), '✍️ 01｜新推文：标题')
        self.assertEqual(item_heading('research_resources', dict(title='QJE：标题', url='https://qje.example'), 1), '📦 01｜资源：QJE：标题')
        self.assertEqual(item_heading('papers', dict(title='其他：标题', journal='American Economic Review'), 1), '📰 01｜论文 · AER：其他：标题')
        self.assertEqual(item_heading('conference_calls', dict(title='机构：征稿', source_name='机构'), 1), '📅 01｜会议征稿 · 机构：征稿')

    def test_extended_excluded_and_every_leak_rejected(self):
        issue = sample()
        extended = dict(id='extended', priority='extended', title='扩展独有标题', url='https://example.org/extended',
                        homepage_url='https://example.org/home-extended', pdf_url='https://example.org/ext.pdf',
                        doi_url='https://doi.org/10.1000/extended', replication_url='https://example.org/ext-code')
        issue['research_resources'] = [extended]
        text = render_daily(issue)
        self.assertEqual(self.validate(issue, text), [])
        for key in ('title', 'url', 'homepage_url', 'pdf_url', 'doi_url', 'replication_url'):
            self.assertTrue(self.validate(issue, text.replace('提要测试', extended[key], 1)), key)

    def test_negative_format_mutations(self):
        issue = sample()
        text = render_daily(issue)
        mutations = {
            'old-title': text.replace('📙', '📰', 1),
            'old-summary': text.replace('提要测试', '提要：提要测试', 1),
            'abstract-prefix': text.replace('提要测试', '摘要：提要测试', 1),
            'intro-prefix': text.replace('提要测试', '简介：提要测试', 1),
            'old-cta': text.replace('🌐 更多内容', '本期详版'),
            'markdown': text.replace('阅读全文： https://example.org/post ', '[阅读全文](https://example.org/post)'),
            'html': text.replace('提要测试', '<b>提要测试</b>', 1),
            'no-left': text.replace('： https://', '：https://', 1),
            'double-left': text.replace('： https://', '：  https://', 1),
            'no-right': text.replace('/post \n', '/post\n'),
            'double-right': text.replace('/post \n', '/post  \n'),
            'punctuation': text.replace('/post \n', '/post。 \n'),
            'blank-lines': text.replace('\n\n', '\n\n\n', 1),
            'internal-blank': text.replace('\n引文：', '\n\n引文：'),
            'separator': text.replace('——', '——\n——'),
            'cta-twice': text + text.split('\n')[-2] + '\n',
            'missing-main-title': text.replace('Paper. AER.', 'AER.'),
            'illegal-emoji': text.replace('📦', '🍀'),
            'sequence': text.replace('02｜', '04｜'),
            'missing-core': text.replace(text.split('\n\n')[2] + '\n\n', ''),
            'duplicate-core': text.replace('——', text.split('\n\n')[1] + '\n\n——'),
            'wrong-cta': text.replace('/20260905/', '/20260906/'),
            'extra-doi': text.replace('引文：', 'DOI： https://doi.org/10.1/test \n引文：'),
            'course': text.replace('提要测试', '课程报名 https://www.lianxh.cn/KC.html ', 1),
        }
        for label, output in mutations.items():
            with self.subTest(case=label):
                self.assertTrue(self.validate(issue, output), label)

    def test_too_few_many_and_duplicate_ids(self):
        base = sample()
        text = render_daily(base)
        small = copy.deepcopy(base)
        small['lianxh_posts'] = []
        large = copy.deepcopy(base)
        large['lianxh_posts'] *= 4
        for issue in (small, large):
            self.assertTrue(self.validate(issue, text))
            with self.assertRaises(ValueError):
                render_daily(issue)
        duplicate = copy.deepcopy(base)
        duplicate['tools'][0]['id'] = duplicate['papers'][0]['id']
        self.assertTrue(self.validate(duplicate))

    def test_old_limits_not_applied(self):
        issue = sample()
        issue['lianxh_posts'][0]['wechat_summary'] = '已编辑研究介绍。' * 400
        self.assertGreater(len(render_daily(issue)), 2200)
        self.assert_valid(issue)

    def test_independent_rejection_of_formatted_but_forbidden_input(self):
        for summary in ('主页： https://example.org/extra ', '提要：测试', '最新课程', '测试🌼'):
            issue = sample()
            issue['lianxh_posts'][0]['wechat_summary'] = summary
            # 输入与 renderer 完全一致也不能通过 URL 计数、前缀、推广或 Emoji 检查。
            self.assertTrue(self.validate(issue), summary)
        issue = sample()
        issue['lianxh_posts'][0]['url'] = 'https://www.lianxh.cn/details/1900.html'
        self.assertTrue(self.validate(issue))

    def test_historical_fingerprint_cannot_mask_changes(self):
        issue = json.loads((ROOT / 'content/issues/2026-09-05.json').read_text(encoding='utf-8'))
        old = (ROOT / 'publish/wechat/2026-09-05.txt').read_text(encoding='utf-8')
        self.assertTrue(self.validate(issue, old + '改动', legacy=True))
        issue['title'] += '改动'
        self.assertTrue(self.validate(issue, old, legacy=True))

    def test_new_v2_cannot_opt_into_legacy(self):
        issue = sample()
        self.assertTrue(self.validate(issue, legacy=True))

    def test_metadata_failure_and_drift(self):
        issue = sample()
        issue['papers'][0]['bibliography']['authors'] = ['Unstructured Name']
        with self.assertRaises(ValueError):
            render_daily(issue)
        for field in ('source', 'publication_status'):
            issue = sample()
            issue['papers'][0]['bibliography'][field] = 'wrong'
            with self.assertRaises(ValueError):
                render_daily(issue)

    def test_builder_five_categories(self):
        issue = sample()
        resource = copy.deepcopy(issue['lianxh_posts'][0])
        resource.update(id='resource', title='资源', url='https://example.org/resource')
        items = [('paper', issue['papers'][0]), ('tool', issue['tools'][0]), ('post', issue['lianxh_posts'][0]),
                 ('resource', resource), ('conference', conference())]
        ledger = [dict(kind=kind, core_or_extended='core', payload=item) for kind, item in items]
        before = copy.deepcopy(ledger)
        built = daily_issue('2026-09-05', ledger)
        self.assertEqual(check_editorial(built), [])
        self.assertEqual(len(core_items(built)), 5)
        self.assertEqual(self.validate(built), [])
        self.assertEqual(ledger, before)

    def test_real_preview_and_historical_opt_in(self):
        issue = json.loads((ROOT / 'content/issues/2026-09-05.json').read_text(encoding='utf-8'))
        self.assertEqual(len(core_items(issue)), 3)
        self.assertEqual(self.validate(issue), [])
        self.assertNotIn(issue['lianxh_posts'][0]['title'], render_daily(issue))
        old = (ROOT / 'publish/wechat/2026-09-05.txt').read_text(encoding='utf-8')
        self.assertTrue(self.validate(issue, old))
        self.assertEqual(self.validate(issue, old, legacy=True), [])



if __name__ == '__main__':
    unittest.main()
