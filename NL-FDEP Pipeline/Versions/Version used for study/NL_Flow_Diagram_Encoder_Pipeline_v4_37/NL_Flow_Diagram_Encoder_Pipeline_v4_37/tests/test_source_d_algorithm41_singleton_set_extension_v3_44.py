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
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return compiled.source_code


source_d_41 = '''FUNCTION SolveNQueens(N):
    board = N x N grid initialized to 0
    solutions = empty List

    PROCEDURE Backtrack(row, cols, diag1, diag2):
        IF row == N THEN
            APPEND Copy(board) TO solutions
            RETURN
        END IF

        FOR col FROM 0 TO N - 1 DO
            IF col IN cols OR (row - col) IN diag1 OR (row + col) IN diag2 THEN
                CONTINUE
            END IF

            board[row][col] = 1
            Backtrack(row + 1, cols + {col}, diag1 + {row - col}, diag2 + {row + col})
            board[row][col] = 0 // Backtrack
        END FOR
    END PROCEDURE

    Backtrack(0, empty Set, empty Set, empty Set)
    RETURN solutions
END FUNCTION
'''


def test_gc245_recovers_exact_source_d41_singleton_set_extensions_only():
    result = process(source_d_41)
    assert any(t.rule == "GC245" for t in result.transformations)
    assert "cols + {col}" not in result.processed_source
    assert "diag1 + {row - col}" not in result.processed_source
    assert "diag2 + {row + col}" not in result.processed_source
    assert (
        "CALL to_set(CALL to_list(cols) + CALL list_value(col))"
        in result.processed_source
    )
    assert (
        "CALL to_set(CALL to_list(diag1) + CALL list_value(row - col))"
        in result.processed_source
    )
    assert (
        "CALL to_set(CALL to_list(diag2) + CALL list_value(row + col))"
        in result.processed_source
    )
    # GC245 remains isolated, but later approved GC246 may now resolve the
    # previously visible board-allocation boundary.  The two rules must compose
    # without changing GC245's set-extension representation.
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_gc245_minimal_evidenced_extension_parses_compiles_and_is_non_mutating():
    source = '''FUNCTION extend ACCEPTS(values, item)
    RETURN values + {item}
ENDFUNCTION
CALL extend(EMPTY SET, 1)
'''
    result = process(source)
    assert any(t.rule == "GC245" for t in result.transformations)
    assert (
        "RETURN CALL to_set(CALL to_list(values) + CALL list_value(item))"
        in result.processed_source
    )
    python_source = compile_source(result.processed_source)
    namespace = {}
    exec(python_source, namespace)
    original = {1, 2}
    extended = namespace["extend"](original, 3)
    assert extended == {1, 2, 3}
    assert original == {1, 2}


def test_gc245_refuses_without_empty_set_call_evidence():
    source = '''FUNCTION extend ACCEPTS(values, item)
    RETURN values + {item}
ENDFUNCTION
CALL extend(existing, 1)
'''
    result = process(source)
    assert all(t.rule != "GC245" for t in result.transformations)
    assert "values + {item}" in result.processed_source


def test_gc245_refuses_multi_member_and_dictionary_braces():
    multi = '''FUNCTION extend ACCEPTS(values, a, b)
    RETURN values + {a, b}
ENDFUNCTION
CALL extend(EMPTY SET, 1, 2)
'''
    dictionary = '''FUNCTION extend ACCEPTS(values, key, value)
    RETURN values + {key: value}
ENDFUNCTION
CALL extend(EMPTY SET, 1, 2)
'''
    for source in (multi, dictionary):
        result = process(source)
        assert all(t.rule != "GC245" for t in result.transformations)


def test_gc245_evidence_is_parameter_position_and_routine_specific():
    source = '''FUNCTION first ACCEPTS(values, item)
    RETURN values + {item}
ENDFUNCTION
FUNCTION second ACCEPTS(values, item)
    RETURN values + {item}
ENDFUNCTION
CALL first(EMPTY SET, 1)
CALL second(existing, 2)
'''
    result = process(source)
    assert sum(t.rule == "GC245" for t in result.transformations) == 1
    assert (
        "RETURN CALL to_set(CALL to_list(values) + CALL list_value(item))"
        in result.processed_source
    )
    # The second routine remains unresolved because its matching call supplies
    # no explicit EMPTY SET evidence.
    assert result.processed_source.count("values + {item}") == 1
