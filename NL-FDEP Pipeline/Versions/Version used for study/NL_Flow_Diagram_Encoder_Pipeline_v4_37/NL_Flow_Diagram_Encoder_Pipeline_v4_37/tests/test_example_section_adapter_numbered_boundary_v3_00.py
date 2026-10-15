import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from corpus_evaluator import ExampleSectionAdapter


def test_numbered_heading_between_functions_starts_next_item_without_blank_line():
    text = (
        '7. First task\n'
        'FUNCTION FIRST()\nRETURN 7\nEND FUNCTION\n'
        '8. Second task\n'
        'FUNCTION SECOND()\nRETURN 8\nEND FUNCTION\n'
    )
    examples = ExampleSectionAdapter().extract(text, 'source_e')
    assert len(examples) == 2
    assert examples[0].source == 'FUNCTION FIRST()\nRETURN 7\nEND FUNCTION'
    assert examples[1].source == 'FUNCTION SECOND()\nRETURN 8\nEND FUNCTION'


def test_decimal_literal_is_not_mistaken_for_task_heading():
    text = (
        '1. Decimal task\n'
        'FUNCTION VALUE()\n'
        '  x = 22.5\n'
        '  RETURN x\n'
        'END FUNCTION\n'
        '2. Next task\n'
        'FUNCTION NEXT()\nRETURN 2\nEND FUNCTION\n'
    )
    examples = ExampleSectionAdapter().extract(text, 'source_e')
    assert '22.5' in examples[0].source


def test_numbered_text_inside_string_or_comment_is_not_a_heading():
    text = (
        '1. Text task\n'
        'FUNCTION TEXT()\n'
        '  s = "22. not a heading"\n'
        '  // 23. also not a heading\n'
        '  RETURN s\n'
        'END FUNCTION\n'
        '2. Next task\n'
        'FUNCTION NEXT()\nRETURN 2\nEND FUNCTION\n'
    )
    examples = ExampleSectionAdapter().extract(text, 'source_e')
    assert '22. not a heading' in examples[0].source
    assert '23. also not a heading' in examples[0].source


def test_example_marker_still_truncates_before_example_content():
    text = (
        '1. First task\n'
        'FUNCTION FIRST()\nRETURN 1\nEND FUNCTION\n'
        'Example:\nFIRST()\nreturns 1\n\n'
        '2. Second task\n'
        'FUNCTION SECOND()\nRETURN 2\nEND FUNCTION\n'
    )
    examples = ExampleSectionAdapter().extract(text, 'source_e')
    assert 'Example:' not in examples[0].source
