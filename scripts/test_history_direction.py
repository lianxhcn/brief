"""发布后更正不能反向破坏旧期次；普通重复仍须拦截。"""
import json
import tempfile
import unittest
from pathlib import Path
from validate_issue import validate_history


class HistoryDirectionTests(unittest.TestCase):
    def test_later_issue_does_not_rewrite_earlier_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            old=dict(date='2026-09-18', tools=[dict(id='tool-v1', name='example', ecosystem='R', url='https://example.org/tool')])
            new=dict(date='2026-09-27', tools=[dict(id='tool-v2', name='example', ecosystem='R', url='https://example.org/tool')])
            a=root/'2026-09-18.json';b=root/'2026-09-27.json'
            a.write_text(json.dumps(old),encoding='utf-8');b.write_text(json.dumps(new),encoding='utf-8')
            errors=[];validate_history(old,a,root,errors)
            self.assertEqual(errors,[])
            # 新期次没有重要变更证据时，仍不能重复推送。
            errors=[];validate_history(new,b,root,errors)
            self.assertTrue(any('14 天内出现相同成果' in e for e in errors))
