import unittest
from card_text_layout import wrap_text


class Font:
    def getlength(self, text):
        return len(text)


class CardWrappingTests(unittest.TestCase):
    def test_latin_word_remains_whole(self):
        lines = wrap_text('中文说明 bootstrap 推断', Font(), 14)
        self.assertTrue(any('bootstrap' in line for line in lines))
        self.assertFalse(any(line.endswith('boots') or line.startswith('trap') for line in lines))
        self.assertTrue(all(len(line) <= 14 for line in lines))

    def test_installation_call_remains_whole(self):
        command = 'install.packages("PanelSelect")'
        lines = wrap_text('安装为 ' + command + '。', Font(), len(command) + 2)
        self.assertTrue(any(command in line for line in lines))
        self.assertEqual(''.join(lines).replace(' ', ''), ('安装为 ' + command + '。').replace(' ', ''))

    def test_question_mark_does_not_start_line(self):
        lines = wrap_text('这是需要检验的问题？', Font(), 9)
        self.assertTrue(all(line and line[0] != '？' for line in lines))
        self.assertEqual(''.join(lines), '这是需要检验的问题？')

    def test_opening_mark_is_not_left_at_end(self):
        lines = wrap_text('说明（需要核验）', Font(), 3)
        self.assertTrue(all(not line.endswith('（') for line in lines))
        self.assertTrue(all(not line.startswith('）') for line in lines))

    def test_overlong_identifier_and_blank_paragraph(self):
        lines = wrap_text('abcdefghijk\n\n中文', Font(), 4)
        self.assertEqual(lines, ['abcd', 'efgh', 'ijk', '', '中文'])

    def test_invalid_width(self):
        with self.assertRaises(ValueError):
            wrap_text('text', Font(), 0)

    def test_full_width_word_with_closing_punctuation(self):
        lines = wrap_text('abcdefghij.', Font(), 10)
        self.assertTrue(all(len(line) <= 10 for line in lines))
        self.assertTrue(all(not line.startswith('.') for line in lines))
        self.assertEqual(''.join(lines), 'abcdefghij.')


if __name__ == '__main__':
    unittest.main()
