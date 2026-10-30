"""微信副本交付仅在临时目录验收，保留既有不同文件。"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import copy_wechat


class WechatDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='brief-wechat-delivery-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repo'
        (self.repo / 'content/issues').mkdir(parents=True)
        (self.repo / 'publish/wechat').mkdir(parents=True)
        self.destination = self.base / 'shared'
        self.root_patch = patch.object(copy_wechat, 'ROOT', self.repo)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        for day in ('2026-10-27', '2026-10-28'):
            (self.repo / 'content/issues' / (day + '.json')).write_text(
                json.dumps({'date': day, 'status': 'published'}),
                encoding='utf-8',
            )
            (self.repo / 'publish/wechat' / (day + '.txt')).write_bytes(
                ('审核稿 ' + day + '\n').encode('utf-8')
            )

    def test_exact_date_and_idempotence(self):
        first = copy_wechat.copy_wechat(
            self.destination, only_date='2026-10-28',
        )
        second = copy_wechat.copy_wechat(
            self.destination, only_date='2026-10-28',
        )
        self.assertEqual([x['file'] for x in first], ['2026-10-28.txt'])
        self.assertEqual(first[0]['status'], 'copied')
        self.assertEqual(second[0]['status'], 'unchanged')
        self.assertFalse((self.destination / '2026-10-27.txt').exists())

    def test_default_rejects_different_existing_content(self):
        self.destination.mkdir()
        old = self.destination / '2026-10-28.txt'
        old.write_bytes(b'old unreviewed material')
        with self.assertRaises(ValueError):
            copy_wechat.copy_wechat(self.destination, only_date='2026-10-28')
        self.assertEqual(old.read_bytes(), b'old unreviewed material')
        self.assertEqual(len(list(self.destination.iterdir())), 1)

    def test_revision_preserves_original_and_warning_marker(self):
        self.destination.mkdir()
        old = self.destination / '2026-10-28.txt'
        old.write_bytes(b'old unreviewed material')
        marker = self.destination / '2026-10-28-待重新审核-勿发布.txt'
        marker.write_text('旧稿不得转发', encoding='utf-8')
        first = copy_wechat.copy_wechat(
            self.destination, only_date='2026-10-28', preserve_conflicts=True,
        )[0]
        second = copy_wechat.copy_wechat(
            self.destination, only_date='2026-10-28', preserve_conflicts=True,
        )[0]
        self.assertIn('-revised-', first['file'])
        self.assertTrue(first['original_conflict']['preserved'])
        self.assertEqual(first['status'], 'copied')
        self.assertEqual(second['status'], 'unchanged')
        self.assertEqual(old.read_bytes(), b'old unreviewed material')
        self.assertEqual(marker.read_text(encoding='utf-8'), '旧稿不得转发')
        self.assertEqual(len(list(self.destination.iterdir())), 3)

    def test_missing_date_does_not_claim_delivery(self):
        with self.assertRaises(ValueError):
            copy_wechat.copy_wechat(self.destination, only_date='2026-10-31')


if __name__ == '__main__':
    unittest.main()
