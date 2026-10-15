from itertools import product

import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_f_ALGORITHM_45 = """INPUT A, B (same dimensions R x C)

INIT result as R x C matrix

FOR i from 0 to R-1:
    FOR j from 0 to C-1:
        result[i][j] = A[i][j] + B[i][j]

RETURN result
"""


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def _compile(source: str):
    result = _process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return result, compiled.source_code


def test_source_f45_exact_source_recovers_rectangular_shape_and_matrix_allocation():
    result, python_source = _compile(source_f_ALGORITHM_45)

    canonical = result.processed_source
    assert "FUNCTION unnamed_function ACCEPTS(A, B)" in canonical
    assert "result <- CALL create_matrix(LENGTH OF A, LENGTH OF A[0], NONE)" in canonical
    assert "FOR i <- IN RANGE 0 TO (LENGTH OF A-1) + 1 DO" in canonical
    assert "FOR j <- IN RANGE 0 TO (LENGTH OF A[0]-1) + 1 DO" in canonical
    assert "result[i][j] <- A[i][j] + B[i][j]" in canonical
    assert "ACCEPTS(A, B, R, C)" not in canonical

    gc223 = [item for item in result.transformations if item.rule == "GC223"]
    assert len(gc223) == 3
    audit = [
        item for item in result.to_dict()["transformations"]
        if item["branch"] == "EVIDENCED_RECTANGULAR_MATRIX_ALLOCATION"
    ]
    assert len(audit) == 3
    assert all(item["rule_family"] == "SHAPE_ANNOTATION" for item in audit)
    assert all(item["confidence"] == "source_proven" for item in audit)
    assert all(item["semantic_change"] is False for item in audit)

    assert "def unnamed_function(A, B):" in python_source
    assert "result = [[None for _ in range(len(A[0]))] for _ in range(len(A))]" in python_source
    assert "for i in range(0, len(A)):" in python_source
    assert "for j in range(0, len(A[0])):" in python_source
    assert "result[i][j] = (A[i][j] + B[i][j])" in python_source


def test_source_f45_generated_python_matches_elementwise_addition_for_rectangles():
    _, python_source = _compile(source_f_ALGORITHM_45)
    namespace = {}
    exec(python_source, namespace)
    fn = namespace["unnamed_function"]

    for rows in range(1, 6):
        for cols in range(1, 6):
            A = [[(r * cols) + c - 5 for c in range(cols)] for r in range(rows)]
            B = [[10 - (r * cols) - c for c in range(cols)] for r in range(rows)]
            expected = [
                [A[r][c] + B[r][c] for c in range(cols)]
                for r in range(rows)
            ]
            assert fn(A, B) == expected


@pytest.mark.parametrize(
    "source",
    [
        # No explicit same-dimensions annotation.
        """INPUT A, B
INIT result as R x C matrix
FOR i from 0 to R-1:
    FOR j from 0 to C-1:
        result[i][j] = A[i][j] + B[i][j]
RETURN result
""",
        # A dimension is independently supplied.
        """INPUT A, B (same dimensions R x C)
INPUT R
INIT result as R x C matrix
FOR i from 0 to R-1:
    FOR j from 0 to C-1:
        result[i][j] = A[i][j] + B[i][j]
RETURN result
""",
        # The column bound does not match the annotated C dimension.
        """INPUT A, B (same dimensions R x C)
INIT result as R x C matrix
FOR i from 0 to R-1:
    FOR j from 0 to R-1:
        result[i][j] = A[i][j] + B[i][j]
RETURN result
""",
        # Fill would be observable because the write is conditional.
        """INPUT A, B (same dimensions R x C)
INIT result as R x C matrix
FOR i from 0 to R-1:
    FOR j from 0 to C-1:
        IF A[i][j] > 0:
            result[i][j] = A[i][j] + B[i][j]
RETURN result
""",
        # The target is not returned as the result of the algorithm.
        """INPUT A, B (same dimensions R x C)
INIT result as R x C matrix
FOR i from 0 to R-1:
    FOR j from 0 to C-1:
        result[i][j] = A[i][j] + B[i][j]
RETURN A
""",
    ],
)
def test_gc223_refuses_missing_ambiguous_or_observable_shape_recovery(source):
    result = _process(source)
    assert not any(item.rule == "GC223" for item in result.transformations)


def test_gc223_is_not_a_general_rectangular_dimension_identifier_substitution():
    source = """INPUT A, B (same dimensions R x C)
INIT result as R x C matrix
FOR i from 0 to R-1:
    FOR j from 0 to C-1:
        result[i][j] = A[i][j] + B[i][j]
OUTPUT R
RETURN result
"""
    result = _process(source)
    assert any(item.rule == "GC223" for item in result.transformations)
    # Only allocation and matching loop bounds are recovered. Unrelated uses
    # remain visible rather than being silently reinterpreted.
    assert "OUTPUT R" in result.processed_source
