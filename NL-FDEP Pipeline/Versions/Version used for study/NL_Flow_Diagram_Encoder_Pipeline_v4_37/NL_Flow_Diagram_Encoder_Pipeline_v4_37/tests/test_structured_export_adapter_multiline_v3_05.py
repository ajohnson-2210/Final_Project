import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from corpus_evaluator import StructuredExportAdapter


class StructuredExportAdapterMultilineV305Tests(unittest.TestCase):
    def test_motivating_split_sentence_occurrence_preserves_multiline_indentation(self):
        text = '''# Split Sentence into Words

INPUT sentence

words = []
current = ""

FOR each char in sentence:
    IF char is space:
        IF current != "":
            words.append(current)
            current = ""
    ELSE:
        current += char

IF current != "":
    words.append(current)

RETURN words

# Sort Words Alphabetically

INPUT wordList
FOR i from 0 to length(wordList)-1:
    OUTPUT wordList[i]
'''
        examples = StructuredExportAdapter().extract(text, 'source_f')
        self.assertEqual(len(examples), 2)
        first = examples[0]
        self.assertEqual(first.title, 'Split Sentence into Words')
        self.assertEqual(first.task_number, 1)
        self.assertIn('FOR each char in sentence:\n    IF char is space:', first.source)
        self.assertIn('        IF current != "":', first.source)
        self.assertIn('    ELSE:\n        current += char', first.source)
        self.assertIn('\nIF current != "":\n    words.append(current)\n\nRETURN words', first.source)
        self.assertNotIn('# Sort Words Alphabetically', first.source)
        self.assertEqual(examples[1].title, 'Sort Words Alphabetically')

    def test_nested_function_and_input_do_not_start_new_structured_items(self):
        text = '''# Outer Task
FUNCTION outer(x):
    INPUT y
    FUNCTION inner(z):
        RETURN z
    RETURN inner(x)

# Next Task
INPUT n
RETURN n
'''
        examples = StructuredExportAdapter().extract(text, 'source_f')
        self.assertEqual(len(examples), 2)
        self.assertIn('    INPUT y', examples[0].source)
        self.assertIn('    FUNCTION inner(z):', examples[0].source)
        self.assertEqual(examples[1].title, 'Next Task')

    def test_structured_format_preserves_blank_lines_and_relative_indent(self):
        text = '# Task\n\nINPUT x\n\nIF x:\n    OUTPUT x\n\nRETURN x\n'
        example = StructuredExportAdapter().extract(text, 'source_f')[0]
        self.assertEqual(
            example.source,
            'INPUT x\n\nIF x:\n    OUTPUT x\n\nRETURN x',
        )

    def test_legacy_format_without_hash_heading_still_uses_fallback(self):
        text = 'Legacy title\nINPUT x\nx = x + 1\n\nNext title\nINPUT y\nRETURN y\n'
        examples = StructuredExportAdapter().extract(text, 'source_f')
        self.assertEqual(len(examples), 2)
        self.assertEqual(examples[0].title, 'Legacy title')
        self.assertEqual(examples[0].source, 'INPUT x x = x + 1')
        self.assertEqual(examples[1].title, 'Next title')
        self.assertEqual(examples[1].source, 'INPUT y RETURN y')

    def test_indented_hash_comment_is_not_a_structured_boundary(self):
        text = '''# Task One
INPUT x
    # internal note
OUTPUT x
# Task Two
INPUT y
OUTPUT y
'''
        examples = StructuredExportAdapter().extract(text, 'source_f')
        self.assertEqual(len(examples), 2)
        self.assertIn('    # internal note', examples[0].source)


if __name__ == '__main__':
    unittest.main()
