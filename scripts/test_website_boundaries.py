"""网站元数据与失败保持边界的额外回归。"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import discover_courses
from website_citations import format_myapa, website_citation

ROOT = Path(__file__).resolve().parents[1]

class WebsiteBoundaryTests(unittest.TestCase):
    def test_one_two_authors_and_working_paper_sources(self):
        for source in ('arXiv', 'NBER Working Paper No. 1'):
            for authors in (['A, X.'], ['A, X.', 'B, Y.']):
                value = format_myapa(dict(authors=authors, year=2026, title='Complete title: A subtitle', source=source))
                self.assertIn(source, value)
                self.assertIn('Complete title: A subtitle', value)
                self.assertEqual('&amp;' in value, len(authors) == 2)

    def test_citation_drift_rejected(self):
        issue = json.loads((ROOT / 'content/issues/2026-09-05.json').read_text(encoding='utf-8'))
        for field in ('citation', 'doi_url', 'pdf_url'):
            item = dict(issue['papers'][0])
            item[field] = 'changed'
            with self.assertRaises(ValueError):
                website_citation(item)

    def test_failed_fetch_preserves_candidates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / 'ops-local/promotion-candidates.json'
            output.parent.mkdir()
            output.write_text('previous reviewed candidates', encoding='utf-8')
            with patch.object(discover_courses, 'ROOT', root), patch('sys.argv', ['discover_courses.py']), patch.object(discover_courses, 'urlopen', side_effect=OSError('offline')), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(discover_courses.main(), 1)
            self.assertEqual(output.read_text(encoding='utf-8'), 'previous reviewed candidates')

if __name__ == '__main__':
    unittest.main()
