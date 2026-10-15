from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def compile_source(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    return compiled.source_code


def test_breaking_branch_does_not_pollute_later_loop_body_state():
    python = compile_source('''FUNCTION demo ACCEPTS(values, flag)
    x <- EMPTY LIST
    FOR EACH item IN values DO
        IF flag THEN
            x <- EMPTY LIST
            BREAK
        ELSE
            x <- EMPTY SET
        ENDIF
        APPEND item TO x
    ENDFOR
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(item)' in python
    namespace = {}
    exec(python, namespace)
    assert namespace['demo']([1], False) == {1}
    assert namespace['demo']([1], True) == []


def test_continuing_branch_does_not_pollute_later_iteration_body_state():
    python = compile_source('''FUNCTION demo ACCEPTS(values, flag)
    x <- EMPTY LIST
    FOR EACH item IN values DO
        IF flag THEN
            x <- EMPTY LIST
            CONTINUE
        ELSE
            x <- EMPTY SET
        ENDIF
        APPEND item TO x
    ENDFOR
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(item)' in python


def test_break_exit_state_participates_in_post_loop_merge():
    python = compile_source('''FUNCTION demo ACCEPTS(values)
    x <- EMPTY SET
    FOR EACH item IN values DO
        x <- EMPTY LIST
        BREAK
    ENDFOR
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    # Empty input leaves x as SET; non-empty input breaks with x as LIST, so
    # SET backing is not definite after the loop.
    assert 'x.append(1)' in python
    assert 'x.add(1)' not in python


def test_break_exit_preserves_set_when_zero_and_break_paths_agree():
    python = compile_source('''FUNCTION demo ACCEPTS(values)
    x <- EMPTY SET
    FOR EACH item IN values DO
        x <- EMPTY SET
        BREAK
    ENDFOR
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(1)' in python


def test_continue_state_participates_conservatively_in_post_loop_merge():
    python = compile_source('''FUNCTION demo ACCEPTS(values)
    x <- EMPTY SET
    FOR EACH item IN values DO
        x <- EMPTY LIST
        CONTINUE
    ENDFOR
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    assert 'x.append(1)' in python
    assert 'x.add(1)' not in python


def test_nested_loop_break_is_recorded_by_innermost_loop_only():
    python = compile_source('''FUNCTION demo ACCEPTS(outer_values, inner_values)
    x <- EMPTY SET
    FOR EACH outer IN outer_values DO
        FOR EACH inner IN inner_values DO
            x <- EMPTY LIST
            BREAK
        ENDFOR
        x <- EMPTY SET
    ENDFOR
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    # Inner BREAK must not be treated as an exit from the outer loop. Every
    # outer-body fallthrough restores SET, and zero outer iterations also SET.
    assert 'x.add(1)' in python
