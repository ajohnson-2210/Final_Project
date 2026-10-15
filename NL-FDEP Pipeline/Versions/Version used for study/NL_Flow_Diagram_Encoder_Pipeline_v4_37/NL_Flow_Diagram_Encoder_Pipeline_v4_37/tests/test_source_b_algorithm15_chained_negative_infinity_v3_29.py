import math

import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def compile_source(processed_source: str) -> str:
    parsed = AJParserFacade().parse(processed_source)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(
        FlowDiagramEncoder().encode(parsed.ast)
    ).source_code


def test_source_b_algorithm15_exact_chain_reuses_negative_infinity_recovery():
    source = '''FUNCTION secondLargest(arr):
    largest ← second ← -INFINITY
    FOR each num IN arr:
        IF num > largest THEN
            second ← largest
            largest ← num
        ELSE IF num > second AND num ≠ largest THEN
            second ← num
    RETURN second
'''
    result = process(source)

    assert "second <- CALL negative_infinity()" in result.processed_source
    assert "largest <- second" in result.processed_source
    assert "second <- -INFINITY" not in result.processed_source
    assert sum(t.rule == "GC079" for t in result.transformations) == 1
    assert sum(t.rule == "GC151" for t in result.transformations) == 1

    compiled = compile_source(result.processed_source)
    assert "second = float('-inf')" in compiled
    assert "largest = second" in compiled

    namespace = {}
    exec(compiled, namespace)
    second_largest = namespace["secondLargest"]
    assert second_largest([3, 1, 2]) == 2
    assert second_largest([9, 4, 7, 3]) == 7
    assert second_largest([-5, -2, -9, -3]) == -3
    assert math.isinf(second_largest([5, 5])) and second_largest([5, 5]) < 0


@pytest.mark.parametrize(
    "surface",
    ["NEGATIVE_INFINITY", "negative_infinity", "Negative_Infinity", "-infinity", "- infinity"],
)
def test_chained_assignment_accepts_only_existing_gc151_negative_infinity_surfaces(surface):
    source = f'''FUNCTION choose ACCEPTS(value)
    first <- second <- {surface}
    RETURN second
ENDFUNCTION
'''
    result = process(source)
    assert "second <- CALL negative_infinity()" in result.processed_source
    assert "first <- second" in result.processed_source
    assert sum(t.rule == "GC079" for t in result.transformations) == 1
    assert sum(t.rule == "GC151" for t in result.transformations) == 1


def test_chained_assignment_does_not_reclassify_positive_infinity_identifier():
    source = '''FUNCTION keep ACCEPTS(INFINITY)
    first <- second <- INFINITY
    RETURN first
ENDFUNCTION
'''
    result = process(source)
    assert "second <- INFINITY" in result.processed_source
    assert "CALL negative_infinity()" not in result.processed_source
    assert sum(t.rule == "GC079" for t in result.transformations) == 1
    assert all(t.rule != "GC151" for t in result.transformations)


def test_chained_assignment_does_not_reclassify_member_named_negative_infinity():
    source = '''FUNCTION keep ACCEPTS(config)
    first <- second <- config.NEGATIVE_INFINITY
    RETURN first
ENDFUNCTION
'''
    result = process(source)
    assert "second <- config.NEGATIVE_INFINITY" in result.processed_source
    assert "CALL negative_infinity()" not in result.processed_source
    assert sum(t.rule == "GC079" for t in result.transformations) == 1
    assert all(t.rule != "GC151" for t in result.transformations)
