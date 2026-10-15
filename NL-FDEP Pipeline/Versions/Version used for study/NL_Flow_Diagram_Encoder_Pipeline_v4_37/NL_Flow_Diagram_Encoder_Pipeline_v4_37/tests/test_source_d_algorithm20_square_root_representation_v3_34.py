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


def test_gc233_free_square_root_maps_to_aj_exp_and_python_power():
    source = '''FUNCTION root ACCEPTS(n)
    result <- SQUARE_ROOT(n)
    RETURN result
ENDFUNCTION
'''
    result = process(source)

    assert any(t.rule == "GC233" for t in result.transformations)
    assert "result <- (n EXP 0.5)" in result.processed_source

    compiled = compile_source(result.processed_source)
    assert "result = (n ** 0.5)" in compiled
    namespace = {}
    exec(compiled, namespace)
    assert namespace["root"](9) == 3.0
    assert namespace["root"](2) == pytest.approx(2 ** 0.5)


def test_source_d_algorithm20_recovers_square_root_but_preserves_float_range_boundary():
    source = '''FUNCTION FindDivisors(n):
    divisors = empty List
    FOR i FROM 1 TO SQUARE_ROOT(n) DO
        IF n MOD i == 0 THEN
            APPEND i TO divisors
            IF i != (n DIV i) THEN
                APPEND (n DIV i) TO divisors
            END IF
        END IF
    END FOR
    RETURN divisors
END FUNCTION
'''
    result = process(source)

    assert any(t.rule == "GC233" for t in result.transformations)
    assert "SQUARE_ROOT" not in result.processed_source
    assert "EXP 0.5" in result.processed_source

    compiled = compile_source(result.processed_source)
    assert "** 0.5" in compiled
    assert "int(" not in compiled
    assert "floor(" not in compiled

    namespace = {}
    exec(compiled, namespace)
    with pytest.raises(TypeError):
        namespace["FindDivisors"](12)


def test_gc233_refuses_declarations_member_calls_and_wrong_arity():
    declaration = process('''FUNCTION SQUARE_ROOT(n):
    RETURN n
END FUNCTION
''')
    member = process('''FUNCTION f(obj, n):
    RETURN obj.SQUARE_ROOT(n)
END FUNCTION
''')
    zero = process('''FUNCTION f():
    RETURN SQUARE_ROOT()
END FUNCTION
''')
    multi = process('''FUNCTION f(a, b):
    RETURN SQUARE_ROOT(a, b)
END FUNCTION
''')

    assert all(t.rule != "GC233" for t in declaration.transformations)
    assert "FUNCTION SQUARE_ROOT ACCEPTS(n)" in declaration.processed_source

    for result in (member, zero, multi):
        assert all(t.rule != "GC233" for t in result.transformations)


def test_gc233_ignores_quoted_text():
    result = process('''FUNCTION f():
    value = "SQUARE_ROOT(n)"
    RETURN value
END FUNCTION
''')
    assert all(t.rule != "GC233" for t in result.transformations)
