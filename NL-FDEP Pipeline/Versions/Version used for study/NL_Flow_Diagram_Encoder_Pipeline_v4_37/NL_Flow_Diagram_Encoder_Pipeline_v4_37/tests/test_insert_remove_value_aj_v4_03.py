import pytest

from aj_parser import AJLexer, AJParserFacade, TokenType
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def parse(source: str):
    return AJParserFacade().parse(source)


def compile_source(source: str):
    result = parse(source)
    assert result.success, result.error or result.report.pretty()
    diagram = FlowDiagramEncoder().encode(result.ast)
    compilation = AJPythonCompiler().compile(diagram)
    assert compilation.success, compilation.message
    return diagram, compilation.source_code


def test_insert_is_first_class_aj_statement_and_compiles_to_list_insert():
    diagram, python = compile_source('''
FUNCTION demo ACCEPTS()
    values <- EMPTY LIST
    INSERT INTEGER(7) INTO values AT INTEGER(0)
    RETURN values
ENDFUNCTION
''')
    statements = diagram.to_dict()['structured_program']['body'][0]['body']['statements']
    assert statements[1]['kind'] == 'InsertNode'
    assert statements[1]['value']['value'] == 7
    assert statements[1]['index']['value'] == 0
    assert 'values.insert(0, 7)' in python


def test_remove_specific_value_is_first_class_statement_for_list_and_set():
    _, list_python = compile_source('''
FUNCTION demo ACCEPTS()
    values <- LIST [INTEGER(1), INTEGER(2)]
    REMOVE INTEGER(1) FROM values
    RETURN values
ENDFUNCTION
''')
    assert 'values.remove(1)' in list_python

    _, set_python = compile_source('''
FUNCTION demo ACCEPTS()
    values <- EMPTY SET
    APPEND INTEGER(1) TO values
    REMOVE INTEGER(1) FROM values
    RETURN values
ENDFUNCTION
''')
    assert 'values.add(1)' in set_python
    assert 'values.remove(1)' in set_python


def test_remove_first_last_phrases_keep_precedence_over_specific_remove_keyword():
    tokens = AJLexer().tokenise('''
REMOVE FIRST ITEM FROM values
REMOVE LAST ITEM FROM values
REMOVE INTEGER(1) FROM values
''')
    keywords = [token.value for token in tokens if token.type == TokenType.KEYWORD]
    assert keywords[:2] == ['REMOVE FIRST ITEM FROM', 'REMOVE LAST ITEM FROM']
    contextual = [token.value.upper() for token in tokens if token.type == TokenType.IDENT]
    assert 'REMOVE' in contextual
    assert 'FROM' in contextual


def test_insert_requires_known_list_receiver_and_integer_index():
    bad_receiver = parse('''
FUNCTION demo ACCEPTS()
    values <- EMPTY SET
    INSERT INTEGER(1) INTO values AT INTEGER(0)
    RETURN values
ENDFUNCTION
''')
    assert not bad_receiver.success
    assert 'INSERT requires LIST collection, found SET' in bad_receiver.error

    bad_index = parse('''
FUNCTION demo ACCEPTS()
    values <- EMPTY LIST
    INSERT INTEGER(1) INTO values AT STRING("zero")
    RETURN values
ENDFUNCTION
''')
    assert not bad_index.success
    assert 'INSERT index must be INTEGER, found STRING' in bad_index.error


def test_insert_unknown_receiver_or_index_type_remains_uninferred():
    result = parse('''
FUNCTION demo ACCEPTS(values, position, item)
    INSERT item INTO values AT position
    RETURN values
ENDFUNCTION
''')
    assert result.success, result.error


def test_remove_specific_value_rejects_statically_incompatible_receivers_only():
    dictionary = parse('''
FUNCTION demo ACCEPTS()
    values <- EMPTY DICTIONARY
    REMOVE STRING("x") FROM values
    RETURN values
ENDFUNCTION
''')
    assert not dictionary.success
    assert 'REMOVE value requires LIST or SET collection, found DICTIONARY' in dictionary.error

    scalar = parse('''
FUNCTION demo ACCEPTS()
    values <- INTEGER(1)
    REMOVE INTEGER(1) FROM values
    RETURN values
ENDFUNCTION
''')
    assert not scalar.success
    assert 'REMOVE value requires LIST or SET collection, found INTEGER' in scalar.error

    unknown = parse('''
FUNCTION demo ACCEPTS(values, item)
    REMOVE item FROM values
    RETURN values
ENDFUNCTION
''')
    assert unknown.success, unknown.error


def test_remove_specific_value_preserves_python_missing_value_error():
    _, python = compile_source('''
FUNCTION demo ACCEPTS()
    values <- LIST [INTEGER(1)]
    REMOVE INTEGER(2) FROM values
    RETURN values
ENDFUNCTION
''')
    namespace = {}
    exec(python, namespace)
    with pytest.raises(ValueError):
        namespace['demo']()


def test_flow_diagram_labels_insert_and_specific_remove_as_processes():
    result = parse('''
values <- EMPTY LIST
INSERT INTEGER(2) INTO values AT INTEGER(0)
REMOVE INTEGER(2) FROM values
''')
    assert result.success, result.error
    document = FlowDiagramEncoder().encode(result.ast).to_dict()
    process_nodes = [node for node in document['nodes'].values() if node['node_type'] == 'PROCESS']
    labels = [node['label'] for node in process_nodes]
    assert any(label.startswith('Insert ') for label in labels)
    assert any(label.startswith('Remove ') and ' from ' in label for label in labels)


def test_insert_remove_are_contextual_keywords_not_globally_reserved_identifiers():
    result = parse('''
CLASS Demo
    METHOD Remove ACCEPTS()
        RETURN INTEGER(1)
    ENDMETHOD
    METHOD Insert ACCEPTS()
        RETURN INTEGER(2)
    ENDMETHOD
ENDCLASS
''')
    assert result.success, result.error

    assignments = parse('''
FUNCTION demo ACCEPTS()
    Remove <- INTEGER(1)
    Insert <- INTEGER(2)
    RETURN Remove + Insert
ENDFUNCTION
''')
    assert assignments.success, assignments.error
