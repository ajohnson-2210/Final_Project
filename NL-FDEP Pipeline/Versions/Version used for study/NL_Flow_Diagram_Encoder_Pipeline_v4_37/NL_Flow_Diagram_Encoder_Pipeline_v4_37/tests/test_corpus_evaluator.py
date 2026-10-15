import os
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from corpus_evaluator import (
    TextExportAdapter,
    ExampleSectionAdapter,
    HashHeadingAdapter,
    NumberedSectionAdapter,
    StructuredExportAdapter,
)


# Research corpus data is deliberately external to the implementation package.
# Set AJ_RESEARCH_CORPUS_DIR when running study-level integration checks.
DATA = Path(os.environ.get('AJ_RESEARCH_CORPUS_DIR', '')) if os.environ.get('AJ_RESEARCH_CORPUS_DIR') else None


class CorpusAdapterTests(unittest.TestCase):
    @unittest.skipUnless(DATA is not None and DATA.is_dir(), "external study corpus not configured")
    def test_external_hash_corpora_extract_fifty_each(self):
        for filename in (
            'source_a.txt',
            'source_b_source_b_4.6.txt',
            'source_c.txt',
            'source_e.txt',
            'source_f_3.6_Plus.txt',
            'source_d.txt',
        ):
            text = (DATA / filename).read_text(encoding='utf-8-sig')
            examples = HashHeadingAdapter().extract(text, filename)
            self.assertEqual(len(examples), 50, filename)

    def test_numbered_adapter_extracts_numbered_sections(self):
        text = (
            '1. First task\nBEGIN\nOUTPUT 1\nEND\n\n'
            '2. Second task\ntext\nBEGIN\nOUTPUT 2\nEND\n'
        )
        examples = NumberedSectionAdapter().extract(text, 'Numbered')
        self.assertEqual(len(examples), 2)
        self.assertEqual(examples[0].task_number, 1)
        self.assertEqual(examples[0].title, 'First task')
        self.assertTrue(examples[0].source.startswith('BEGIN'))
        self.assertEqual(examples[1].task_number, 2)
        self.assertNotIn('\ntext\n', f"\n{examples[1].source}\n".lower())

    def test_source_e_adapter_extracts_function_sections_without_examples(self):
        text = (
            '1. First task\n'
            'FUNCTION FIRST()\nRETURN 1\nEND FUNCTION\n'
            'Example:\nFIRST()\nreturns 1\n\n'
            '2. Second task\n'
            'FUNCTION SECOND()\nRETURN 2\nEND FUNCTION\n'
            'Example:\nSECOND()\nreturns 2\n'
        )
        examples = ExampleSectionAdapter().extract(text, 'source_e')
        self.assertEqual(len(examples), 2)
        self.assertTrue(examples[0].source.startswith('FUNCTION FIRST'))
        self.assertNotIn('Example:', examples[0].source)
        self.assertTrue(examples[1].source.startswith('FUNCTION SECOND'))

    def test_source_f_adapter_extracts_compressed_bodies(self):
        text = (
            '# First task\n'
            'INPUT x\n'
            'x = x + 1\n\n'
            '# Drone Coordination\n'
            'INPUT drones\n'
            'RETURN drones\n'
        )
        examples = StructuredExportAdapter().extract(text, 'source_f')
        self.assertEqual(len(examples), 2)
        self.assertIn('Drone Coordination', examples[-1].title)
        self.assertTrue(examples[-1].source.startswith('INPUT drones'))

    def test_source_d_txt_adapter_extracts_plaintext_sections(self):
        text = (
            '1. Determine whether two strings are anagrams\n'
            'PlaintextFUNCTION AreAnagrams(a, b)\nRETURN TRUE\nEND FUNCTION\n\n'
            '2. Return a value\n'
            'PlaintextFUNCTION Value()\nRETURN 2\nEND FUNCTION\n'
        )
        examples = TextExportAdapter().extract(text, 'source_d')
        self.assertEqual(len(examples), 2)
        self.assertTrue(examples[0].source.startswith('FUNCTION AreAnagrams'))
        self.assertTrue(examples[1].source.startswith('FUNCTION Value'))


if __name__ == '__main__':
    unittest.main()
