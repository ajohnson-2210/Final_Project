from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def _compile(canonical: str) -> str:
    parsed = AJParserFacade().parse(canonical)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast)).source_code


def test_explicit_null_remains_textually_null_in_canonical_aj():
    source = '''FUNCTION inspect ACCEPTS(root)
    IF root IS NULL THEN
        RETURN NULL
    ENDIF
    IF root.left IS NOT NULL THEN
        RETURN root.left
    ENDIF
    marker <- NULL
    RETURN marker
ENDFUNCTION
'''
    result = _process(source)
    canonical = result.processed_source

    assert 'IF root == NULL THEN' in canonical
    assert 'IF root.left != NULL THEN' in canonical
    assert 'RETURN NULL' in canonical
    assert 'marker <- NULL' in canonical
    assert 'CALL NULL()' not in canonical
    assert 'NONE' not in canonical

    python = _compile(canonical)
    assert 'root is None' in python
    assert 'root.left is not None' in python
    assert 'return None' in python
    assert 'marker = None' in python


def test_native_none_spellings_still_canonicalise_to_none_literal():
    result = _process('''FUNCTION demo ACCEPTS(value)
    IF value == None THEN
        RETURN none
    ENDIF
    RETURN NONE
ENDFUNCTION
''')
    canonical = result.processed_source
    assert 'None' not in canonical
    assert 'none' not in canonical
    assert canonical.count('NONE') == 3

    python = _compile(canonical)
    assert 'value is None' in python
    assert python.count('return None') == 2


def test_explicit_legacy_call_null_remains_accepted_and_compiles_to_none():
    canonical = '''FUNCTION demo ACCEPTS()
    RETURN CALL NULL()
ENDFUNCTION
'''
    python = _compile(canonical)
    assert 'return None' in python


def test_quoted_null_text_is_not_rewritten():
    result = _process('''FUNCTION demo ACCEPTS()
    OUTPUT STRING("NULL")
ENDFUNCTION
''')
    assert 'STRING("NULL")' in result.processed_source
