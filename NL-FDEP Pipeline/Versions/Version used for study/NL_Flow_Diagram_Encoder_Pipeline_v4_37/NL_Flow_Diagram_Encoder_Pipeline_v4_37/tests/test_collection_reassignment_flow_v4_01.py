from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def _compile(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    return compiled.source_code


def test_set_then_list_reassignment_changes_append_lowering_in_source_order():
    source = '''FUNCTION reset ACCEPTS()
    result <- EMPTY SET
    APPEND 1 TO result
    result <- EMPTY LIST
    APPEND 2 TO result
    RETURN result
ENDFUNCTION
'''
    python = _compile(source)
    assert 'result = set()\n    result.add(1)' in python
    assert 'result = []\n    result.append(2)' in python
    assert 'result = []\n    result.add(2)' not in python


def test_list_then_set_reassignment_changes_append_lowering_in_source_order():
    source = '''FUNCTION reset ACCEPTS()
    result <- EMPTY LIST
    APPEND 1 TO result
    result <- EMPTY SET
    APPEND 2 TO result
    RETURN result
ENDFUNCTION
'''
    python = _compile(source)
    assert 'result = []\n    result.append(1)' in python
    assert 'result = set()\n    result.add(2)' in python


def test_future_set_assignment_does_not_retroactively_change_earlier_append():
    source = '''FUNCTION reset ACCEPTS()
    result <- EMPTY LIST
    APPEND 1 TO result
    result <- EMPTY SET
    RETURN result
ENDFUNCTION
'''
    python = _compile(source)
    assert 'result = []\n    result.append(1)' in python
    assert 'result = []\n    result.add(1)' not in python


def test_explicit_conversion_reassignment_updates_collection_representation():
    source = '''FUNCTION reset ACCEPTS(values)
    result <- CALL to_set(values)
    APPEND 1 TO result
    result <- CALL to_list(result)
    APPEND 2 TO result
    RETURN result
ENDFUNCTION
'''
    python = _compile(source)
    assert 'result = set(values)\n    result.add(1)' in python
    assert 'result = list(result)\n    result.append(2)' in python


def test_if_branches_that_all_assign_set_preserve_set_evidence_after_if():
    source = '''FUNCTION choose ACCEPTS(flag)
    IF flag THEN
        result <- EMPTY SET
    ELSE
        result <- EMPTY SET
    ENDIF
    APPEND 1 TO result
    RETURN result
ENDFUNCTION
'''
    python = _compile(source)
    assert 'result.add(1)' in python


def test_mixed_if_collection_representations_do_not_invent_set_after_if():
    source = '''FUNCTION choose ACCEPTS(flag)
    IF flag THEN
        result <- EMPTY SET
    ELSE
        result <- EMPTY LIST
    ENDIF
    APPEND 1 TO result
    RETURN result
ENDFUNCTION
'''
    python = _compile(source)
    assert 'result.append(1)' in python
    assert 'result.add(1)' not in python
