from aj_parser import AJParserFacade, MemberCallNode
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def parse(source: str):
    result = AJParserFacade().parse(source)
    assert result.success, result.error
    return result


def member_calls(ast):
    def walk(node):
        yield node
        for child in node.children():
            yield from walk(child)
    return [node for node in walk(ast) if isinstance(node, MemberCallNode)]


def compile_source(source: str):
    parsed = parse(source)
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.errors
    return parsed, compiled.source_code


def test_dictionary_evidence_is_cleared_by_later_list_reassignment():
    parsed, python = compile_source('''FUNCTION demo ACCEPTS(key)
    x <- EMPTY DICTIONARY
    x <- EMPTY LIST
    RETURN x.GET(key)
ENDFUNCTION
''')
    call = member_calls(parsed.ast)[0]
    assert call.resolved_intrinsic is None
    assert 'return x.GET(key)' in python
    assert 'return x[key]' not in python


def test_later_dictionary_assignment_establishes_get_intrinsic():
    parsed, python = compile_source('''FUNCTION demo ACCEPTS(key)
    x <- EMPTY LIST
    x <- EMPTY DICTIONARY
    RETURN x.GET(key)
ENDFUNCTION
''')
    call = member_calls(parsed.ast)[0]
    assert call.resolved_intrinsic == 'DICTIONARY_GET'
    assert 'return x[key]' in python


def test_one_sided_if_dictionary_assignment_does_not_escape_branch():
    parsed, _ = compile_source('''FUNCTION demo ACCEPTS(flag, key)
    x <- EMPTY LIST
    IF flag THEN
        x <- EMPTY DICTIONARY
    ENDIF
    RETURN x.GET(key)
ENDFUNCTION
''')
    assert member_calls(parsed.ast)[0].resolved_intrinsic is None


def test_all_if_paths_dictionary_assignment_establishes_post_join_evidence():
    parsed, python = compile_source('''FUNCTION demo ACCEPTS(flag, key)
    IF flag THEN
        x <- EMPTY DICTIONARY
    ELSE
        x <- EMPTY DICTIONARY
    ENDIF
    RETURN x.GET(key)
ENDFUNCTION
''')
    assert member_calls(parsed.ast)[0].resolved_intrinsic == 'DICTIONARY_GET'
    assert 'return x[key]' in python


def test_loop_body_only_dictionary_assignment_does_not_escape_zero_iteration_loop():
    parsed, _ = compile_source('''FUNCTION demo ACCEPTS(flag, key)
    x <- EMPTY LIST
    WHILE flag DO
        x <- EMPTY DICTIONARY
        flag <- BOOLEAN(FALSE)
    ENDWHILE
    RETURN x.GET(key)
ENDFUNCTION
''')
    assert member_calls(parsed.ast)[0].resolved_intrinsic is None


def test_loop_can_destroy_preexisting_dictionary_certainty():
    parsed, _ = compile_source('''FUNCTION demo ACCEPTS(values, key)
    x <- EMPTY DICTIONARY
    FOR EACH item IN values DO
        x <- EMPTY LIST
    ENDFOR
    RETURN x.GET(key)
ENDFUNCTION
''')
    assert member_calls(parsed.ast)[0].resolved_intrinsic is None


def test_nested_function_inherits_unshadowed_enclosing_dictionary_evidence():
    parsed, python = compile_source('''FUNCTION outer ACCEPTS(key)
    x <- EMPTY DICTIONARY
    FUNCTION inner ACCEPTS()
        RETURN x.GET(key)
    ENDFUNCTION
    RETURN NONE
ENDFUNCTION
''')
    call = member_calls(parsed.ast)[0]
    assert call.resolved_intrinsic == 'DICTIONARY_GET'
    assert 'return x[key]' in python


def test_nested_parameter_shadows_enclosing_dictionary_evidence():
    parsed, python = compile_source('''FUNCTION outer ACCEPTS(key)
    x <- EMPTY DICTIONARY
    FUNCTION inner ACCEPTS(x)
        RETURN x.GET(key)
    ENDFUNCTION
    RETURN NONE
ENDFUNCTION
''')
    call = member_calls(parsed.ast)[0]
    assert call.resolved_intrinsic is None
    assert 'return x.GET(key)' in python


def test_break_branch_does_not_pollute_dictionary_get_later_in_loop_body():
    parsed, python = compile_source('''FUNCTION demo ACCEPTS(values, flag, key)
    x <- EMPTY LIST
    FOR EACH item IN values DO
        IF flag THEN
            x <- EMPTY LIST
            BREAK
        ELSE
            x <- EMPTY DICTIONARY
        ENDIF
        OUTPUT x.GET(key, NONE)
    ENDFOR
    RETURN NONE
ENDFUNCTION
''')
    call = member_calls(parsed.ast)[0]
    assert call.resolved_intrinsic == 'DICTIONARY_GET'
    assert 'print(x.get(key, None))' in python


def test_continue_branch_does_not_pollute_dictionary_get_later_in_loop_body():
    parsed, python = compile_source('''FUNCTION demo ACCEPTS(values, flag, key)
    x <- EMPTY LIST
    FOR EACH item IN values DO
        IF flag THEN
            x <- EMPTY LIST
            CONTINUE
        ELSE
            x <- EMPTY DICTIONARY
        ENDIF
        OUTPUT x.GET(key, NONE)
    ENDFOR
    RETURN NONE
ENDFUNCTION
''')
    call = member_calls(parsed.ast)[0]
    assert call.resolved_intrinsic == 'DICTIONARY_GET'
    assert 'print(x.get(key, None))' in python
