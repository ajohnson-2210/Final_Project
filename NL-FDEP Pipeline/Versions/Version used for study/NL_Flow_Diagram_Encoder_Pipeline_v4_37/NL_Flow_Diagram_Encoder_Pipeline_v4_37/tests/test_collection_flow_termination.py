from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def compile_source(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    return compiled.source_code


def test_returning_if_branch_does_not_pollute_continuing_set_state():
    python = compile_source('''FUNCTION demo ACCEPTS(flag)
    x <- EMPTY LIST
    IF flag THEN
        RETURN NONE
    ELSE
        x <- EMPTY SET
    ENDIF
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(1)' in python
    namespace = {}
    exec(python, namespace)
    assert namespace['demo'](False) == {1}
    assert namespace['demo'](True) is None


def test_raising_if_branch_does_not_pollute_continuing_set_state():
    python = compile_source('''FUNCTION demo ACCEPTS(flag)
    x <- EMPTY LIST
    IF flag THEN
        RAISE STRING("stop")
    ELSE
        x <- EMPTY SET
    ENDIF
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(1)' in python


def test_nested_all_terminating_branch_is_excluded_from_outer_merge():
    python = compile_source('''FUNCTION demo ACCEPTS(a, b)
    x <- EMPTY LIST
    IF a THEN
        IF b THEN
            RETURN NONE
        ELSE
            RAISE STRING("stop")
        ENDIF
    ELSE
        x <- EMPTY SET
    ENDIF
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(1)' in python


def test_try_catch_does_not_include_pre_try_state_when_both_paths_set():
    python = compile_source('''FUNCTION demo ACCEPTS(flag)
    x <- EMPTY LIST
    TRY
        IF flag THEN
            RAISE STRING("boom")
        ENDIF
        x <- EMPTY SET
    CATCH error
        x <- EMPTY SET
    ENDTRY
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(1)' in python
    namespace = {}
    exec(python, namespace)
    assert namespace['demo'](False) == {1}
    assert namespace['demo'](True) == {1}


def test_returning_try_path_leaves_catch_as_only_post_try_state():
    python = compile_source('''FUNCTION demo ACCEPTS(flag)
    x <- EMPTY LIST
    TRY
        IF flag THEN
            RETURN NONE
        ENDIF
        RAISE STRING("boom")
    CATCH error
        x <- EMPTY SET
    ENDTRY
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(1)' in python


def test_always_returning_while_body_cannot_destroy_zero_iteration_state():
    python = compile_source('''FUNCTION demo ACCEPTS(flag)
    x <- EMPTY SET
    WHILE flag DO
        x <- EMPTY LIST
        RETURN NONE
    ENDWHILE
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(1)' in python


def test_always_returning_foreach_body_cannot_destroy_zero_iteration_state():
    python = compile_source('''FUNCTION demo ACCEPTS(values)
    x <- EMPTY SET
    FOR EACH item IN values DO
        x <- EMPTY LIST
        RETURN NONE
    ENDFOR
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(1)' in python


def test_always_returning_range_body_cannot_destroy_zero_iteration_state():
    python = compile_source('''FUNCTION demo ACCEPTS(limit)
    x <- EMPTY SET
    FOR i <- IN RANGE 0 TO limit DO
        x <- EMPTY LIST
        RETURN NONE
    ENDFOR
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
''')
    assert 'x.add(1)' in python
