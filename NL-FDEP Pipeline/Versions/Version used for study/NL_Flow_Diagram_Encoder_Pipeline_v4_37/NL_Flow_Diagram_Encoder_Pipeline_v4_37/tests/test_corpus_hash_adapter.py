import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from corpus_evaluator import HashHeadingAdapter


class HashHeadingAdapterTests(unittest.TestCase):
    def test_column_one_hash_starts_new_algorithm(self):
        text = "# First\nINPUT x\n  # internal note\nOUTPUT x\n\n# Second\nINPUT y\nOUTPUT y\n"
        examples = HashHeadingAdapter().extract(text, "Test")
        self.assertEqual(len(examples), 2)
        self.assertEqual(examples[0].title, "First")
        self.assertIn("# internal note", examples[0].source)
        self.assertEqual(examples[1].title, "Second")

    def test_indented_hash_is_not_a_boundary(self):
        text = "# Task\nFUNCTION f ACCEPTS()\n    # comment\n    RETURN 1\nENDFUNCTION\n"
        examples = HashHeadingAdapter().extract(text, "Test")
        self.assertEqual(len(examples), 1)


if __name__ == '__main__':
    unittest.main()
