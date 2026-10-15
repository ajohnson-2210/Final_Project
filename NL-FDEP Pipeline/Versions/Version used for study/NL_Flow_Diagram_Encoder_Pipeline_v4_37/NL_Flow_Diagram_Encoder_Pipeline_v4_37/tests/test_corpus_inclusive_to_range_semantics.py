from collections import Counter, defaultdict
import os
from pathlib import Path

import pytest

from corpus_evaluator import HashHeadingAdapter
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


EXPECTED_GC176_COUNTS = {
    "source_a": 7,
    "source_b_source_b_4.6": 17,
    "source_c": 20,
    "source_d": 9,
    "source_e": 20,
    "source_f_3.6_Plus": 18,
}

EXPECTED_AFFECTED_ALGORITHMS = {
    "source_a": {12, 20, 22, 25, 28},
    "source_b_source_b_4.6": {8, 9, 12, 20, 25, 27, 28, 41, 44, 45, 46},
    "source_c": {8, 9, 12, 20, 22, 25, 26, 27, 28, 41, 45, 46},
    "source_d": {8, 12, 22, 25, 26, 27, 28, 41, 44},
    "source_e": {9, 12, 13, 20, 25, 26, 27, 28, 41, 42, 45, 46},
    "source_f_3.6_Plus": {8, 9, 12, 20, 22, 25, 26, 27, 28, 41, 45, 46, 50},
}


def test_corpus_inclusive_to_endpoints_are_adjusted_once():
    """All 92 audited ascending inclusive-TO misses use the generic rule."""
    root = os.environ.get("AJ_RESEARCH_CORPUS_DIR")
    if not root:
        pytest.skip("study corpus is external; set AJ_RESEARCH_CORPUS_DIR to run this integration test")
    corpus_root = Path(root)
    if not corpus_root.is_dir():
        pytest.skip(f"external study corpus directory not found: {corpus_root}")
    processor = PseudocodeProfileProcessor()
    adapter = HashHeadingAdapter()

    counts = Counter()
    affected = defaultdict(set)
    residual = []
    implicit_descending = []
    explicit_descending = []

    for path in sorted(corpus_root.glob("*.txt")):
        model = path.stem
        examples = adapter.extract(path.read_text(encoding="utf-8"), model)
        assert len(examples) == 50

        for example in examples:
            result = processor.process(
                example.source,
                PseudocodeProfile.GENERIC_COMPATIBILITY,
            )

            for transformation in result.transformations:
                if transformation.rule == "GC176":
                    counts[model] += 1
                    affected[model].add(example.task_number)
                elif transformation.rule == "GC177":
                    implicit_descending.append((model, example.task_number))
                    affected[model].add(example.task_number)
                elif transformation.rule == "GC178":
                    explicit_descending.append((model, example.task_number))

            for line in result.processed_source.splitlines():
                stripped = line.strip()
                if (
                    stripped.startswith("FOR ")
                    and " IN RANGE " in stripped
                    and " TO " in stripped
                    and " STEP -1 " not in stripped
                    and "+ 1 DO" not in stripped
                    and "+ 1)" not in stripped
                ):
                    residual.append((model, example.task_number, stripped))

    assert dict(counts) == EXPECTED_GC176_COUNTS
    assert implicit_descending == [("source_e", 13)]
    assert sorted(explicit_descending) == [
        ("source_a", 13),
        ("source_b_source_b_4.6", 13),
        ("source_c", 13),
    ]
    # 91 ascending ranges use GC176; the 92nd previously identified case is
    # source_e Algorithm 13, whose explicit last-index -> zero endpoints require a
    # negative step and are handled by GC177 rather than the ascending rule.
    assert sum(counts.values()) == 91
    assert {model: set(items) for model, items in affected.items()} == EXPECTED_AFFECTED_ALGORITHMS
    assert residual == []
