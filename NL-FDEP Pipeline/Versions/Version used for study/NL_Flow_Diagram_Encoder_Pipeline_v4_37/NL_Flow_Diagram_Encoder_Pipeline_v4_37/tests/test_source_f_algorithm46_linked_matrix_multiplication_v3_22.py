import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_f_ALGORITHM_46 = """INPUT A (M x N), B (N x P)

INIT C as M x P matrix

FOR i from 0 to M-1:
    FOR j from 0 to P-1:
        sum = 0

        FOR k from 0 to N-1:
            sum += A[i][k] * B[k][j]

        C[i][j] = sum

RETURN C
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


def test_source_f46_exact_source_recovers_linked_dimensions_and_output_allocation():
    result, python_source = _compile(source_f_ALGORITHM_46)

    canonical = result.processed_source
    assert "FUNCTION unnamed_function ACCEPTS(A, B)" in canonical
    assert "C <- CALL create_matrix(LENGTH OF A, LENGTH OF B[0], NONE)" in canonical
    assert "FOR i <- IN RANGE 0 TO (LENGTH OF A-1) + 1 DO" in canonical
    assert "FOR j <- IN RANGE 0 TO (LENGTH OF B[0]-1) + 1 DO" in canonical
    assert "FOR k <- IN RANGE 0 TO (LENGTH OF B-1) + 1 DO" in canonical
    assert "sum <- sum + A[i][k] * B[k][j]" in canonical
    assert "C[i][j] <- sum" in canonical
    assert "ACCEPTS(A, B, M, N, P)" not in canonical

    gc224 = [item for item in result.transformations if item.rule == "GC224"]
    assert len(gc224) == 4
    audit = [
        item for item in result.to_dict()["transformations"]
        if item["branch"] == "EVIDENCED_LINKED_MATRIX_MULTIPLICATION_DIMENSIONS"
    ]
    assert len(audit) == 4
    assert all(item["rule_family"] == "SHAPE_ANNOTATION" for item in audit)
    assert all(item["confidence"] == "source_proven" for item in audit)
    assert all(item["semantic_change"] is False for item in audit)

    assert "def unnamed_function(A, B):" in python_source
    assert "C = [[None for _ in range(len(B[0]))] for _ in range(len(A))]" in python_source
    assert "for i in range(0, len(A)):" in python_source
    assert "for j in range(0, len(B[0])):" in python_source
    assert "for k in range(0, len(B)):" in python_source
    assert "sum = (sum + (A[i][k] * B[k][j]))" in python_source
    assert "C[i][j] = sum" in python_source


def test_source_f46_generated_python_matches_independent_matrix_multiplication_reference():
    _, python_source = _compile(source_f_ALGORITHM_46)
    namespace = {}
    exec(python_source, namespace)
    fn = namespace["unnamed_function"]

    checked = 0
    for m in range(0, 5):
        for n in range(1, 5):
            for p in range(0, 5):
                A = [
                    [((r + 1) * (k + 2)) - 5 for k in range(n)]
                    for r in range(m)
                ]
                B = [
                    [((k + 3) - (c * 2)) for c in range(p)]
                    for k in range(n)
                ]
                expected = [
                    [
                        sum(A[i][k] * B[k][j] for k in range(n))
                        for j in range(p)
                    ]
                    for i in range(m)
                ]
                assert fn(A, B) == expected
                checked += 1

    assert checked == 100


@pytest.mark.parametrize(
    "source",
    [
        # The two annotations do not share the same inner dimension symbol.
        """INPUT A (M x N), B (Q x P)
INIT C as M x P matrix
FOR i from 0 to M-1:
    FOR j from 0 to P-1:
        sum = 0
        FOR k from 0 to N-1:
            sum += A[i][k] * B[k][j]
        C[i][j] = sum
RETURN C
""",
        # A dimension is independently supplied and is therefore runtime state.
        """INPUT A (M x N), B (N x P)
INPUT N
INIT C as M x P matrix
FOR i from 0 to M-1:
    FOR j from 0 to P-1:
        sum = 0
        FOR k from 0 to N-1:
            sum += A[i][k] * B[k][j]
        C[i][j] = sum
RETURN C
""",
        # Result dimensions do not match M x P.
        """INPUT A (M x N), B (N x P)
INIT C as M x N matrix
FOR i from 0 to M-1:
    FOR j from 0 to P-1:
        sum = 0
        FOR k from 0 to N-1:
            sum += A[i][k] * B[k][j]
        C[i][j] = sum
RETURN C
""",
        # Inner loop does not traverse the shared N dimension.
        """INPUT A (M x N), B (N x P)
INIT C as M x P matrix
FOR i from 0 to M-1:
    FOR j from 0 to P-1:
        sum = 0
        FOR k from 0 to P-1:
            sum += A[i][k] * B[k][j]
        C[i][j] = sum
RETURN C
""",
        # Multiplication relation has been changed.
        """INPUT A (M x N), B (N x P)
INIT C as M x P matrix
FOR i from 0 to M-1:
    FOR j from 0 to P-1:
        sum = 0
        FOR k from 0 to N-1:
            sum += A[i][k] * B[j][k]
        C[i][j] = sum
RETURN C
""",
        # Output fill could become observable because the write is conditional.
        """INPUT A (M x N), B (N x P)
INIT C as M x P matrix
FOR i from 0 to M-1:
    FOR j from 0 to P-1:
        sum = 0
        FOR k from 0 to N-1:
            sum += A[i][k] * B[k][j]
        IF sum > 0:
            C[i][j] = sum
RETURN C
""",
        # Dimension symbol escapes its guarded shape positions.
        """INPUT A (M x N), B (N x P)
INIT C as M x P matrix
FOR i from 0 to M-1:
    FOR j from 0 to P-1:
        sum = 0
        FOR k from 0 to N-1:
            sum += A[i][k] * B[k][j]
        C[i][j] = sum
OUTPUT N
RETURN C
""",
    ],
)
def test_gc224_refuses_ambiguous_or_semantically_different_shapes(source):
    result = _process(source)
    assert not any(item.rule == "GC224" for item in result.transformations)


def test_gc224_does_not_take_over_source_f45_same_dimensions_recovery():
    source = """INPUT A, B (same dimensions R x C)
INIT result as R x C matrix
FOR i from 0 to R-1:
    FOR j from 0 to C-1:
        result[i][j] = A[i][j] + B[i][j]
RETURN result
"""
    result = _process(source)
    assert any(item.rule == "GC223" for item in result.transformations)
    assert not any(item.rule == "GC224" for item in result.transformations)


def test_gc224_explicit_zero_initialiser_remains_zero_filled():
    source = source_f_ALGORITHM_46.replace(
        "INIT C as M x P matrix",
        "INIT C as M x P matrix initialized with 0",
    )
    result, python_source = _compile(source)
    canonical = result.processed_source
    assert "C <- CALL create_matrix(LENGTH OF A, LENGTH OF B[0], 0)" in canonical
    assert "C = [[0 for _ in range(len(B[0]))] for _ in range(len(A))]" in python_source


def test_gc224_unspecified_matrix_fill_is_none_not_zero():
    result, python_source = _compile(source_f_ALGORITHM_46)
    canonical = result.processed_source
    assert "C <- CALL create_matrix(LENGTH OF A, LENGTH OF B[0], NONE)" in canonical
    assert "create_matrix(LENGTH OF A, LENGTH OF B[0], 0)" not in canonical
    assert "C = [[None for _ in range(len(B[0]))] for _ in range(len(A))]" in python_source
