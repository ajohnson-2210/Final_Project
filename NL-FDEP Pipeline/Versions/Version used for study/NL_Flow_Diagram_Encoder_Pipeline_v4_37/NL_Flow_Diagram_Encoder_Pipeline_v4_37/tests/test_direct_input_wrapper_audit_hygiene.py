import os
from pathlib import Path

import pytest

from corpus_evaluator import HashHeadingAdapter
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _source_a_example(number: int):
    root = os.environ.get("AJ_RESEARCH_CORPUS_DIR")
    if not root:
        pytest.skip("study corpus is external; set AJ_RESEARCH_CORPUS_DIR to run this integration test")
    corpus = Path(root) / "source_a.txt"
    if not corpus.is_file():
        pytest.skip(f"external study corpus file not found: {corpus}")
    examples = HashHeadingAdapter().extract(corpus.read_text(encoding="utf-8"), "source_a")
    return examples[number - 1]


def test_source_a_algorithm3_binds_input_directly_to_neutral_wrapper():
    example = _source_a_example(3)
    result = PseudocodeProfileProcessor().process(
        example.source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )

    assert result.processed_source.startswith("FUNCTION unnamed_function ACCEPTS(Year)\n")
    assert "INPUT(STRING" not in result.processed_source
    assert any(t.rule == "GC173" for t in result.transformations)
    assert not any("INPUT(STRING(" in (t.target or "") for t in result.transformations)


def test_direct_wrapper_keeps_explicit_source_function_outside_generic_policy():
    source = '''INPUT N
FUNCTION Named(N)
    OUTPUT N
END FUNCTION
Named(N)'''
    result = PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )

    assert "FUNCTION Named ACCEPTS(N)" in result.processed_source
    assert "FUNCTION unnamed_function" not in result.processed_source
    assert not any(t.rule == "GC173" for t in result.transformations)
