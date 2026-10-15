from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor
from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def _compile(canonical: str) -> str:
    parsed = AJParserFacade().parse(canonical)
    assert parsed.success, parsed.error
    flow = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(flow)
    assert compiled.success, compiled.error
    return compiled.source_code


def test_unknown_push_preserves_push_abstraction_but_compiler_may_use_append():
    source = '''FUNCTION add ACCEPTS(item, container)
    PUSH item TO container
    RETURN container
ENDFUNCTION
'''
    result = _process(source)
    assert 'CALL PUSH(item, container)' in result.processed_source
    assert 'APPEND item TO container' not in result.processed_source

    python = _compile(result.processed_source)
    assert 'container.append(item)' in python


def test_explicit_list_backing_still_justifies_append_canonical_form():
    source = '''FUNCTION add ACCEPTS(item)
    container <- EMPTY LIST
    PUSH item TO container
    RETURN container
ENDFUNCTION
'''
    result = _process(source)
    assert 'APPEND item TO container' in result.processed_source
    assert 'CALL PUSH(item, container)' not in result.processed_source

    python = _compile(result.processed_source)
    assert 'container.append(item)' in python


def test_explicit_stack_backing_still_preserves_stack_abstraction():
    source = '''FUNCTION add ACCEPTS(item)
    container <- EMPTY STACK
    PUSH item TO container
    RETURN container
ENDFUNCTION
'''
    result = _process(source)
    assert 'container <- CALL create_stack()' in result.processed_source
    assert 'CALL PUSH(item, container)' in result.processed_source
    assert 'APPEND item TO container' not in result.processed_source

    python = _compile(result.processed_source)
    assert 'container = []' in python
    assert 'container.append(item)' in python
