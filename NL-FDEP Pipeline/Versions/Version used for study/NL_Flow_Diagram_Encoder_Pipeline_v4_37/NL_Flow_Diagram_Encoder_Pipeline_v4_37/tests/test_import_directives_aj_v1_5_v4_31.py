from contextlib import redirect_stdout
from io import StringIO

from aj_parser import AJParserFacade, CommentNode, ImportDirectiveNode
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def parse_strict(source: str):
    processed = PseudocodeProfileProcessor().process(source, PseudocodeProfile.AJ_DIALECT_STRICT)
    parsed = AJParserFacade().parse(processed.processed_source)
    assert parsed.success, parsed.error
    return parsed


def compile_strict(source: str) -> str:
    parsed = parse_strict(source)
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    return compiled.source_code


def run_strict(source: str) -> list[str]:
    code = compile_strict(source)
    stream = StringIO()
    namespace = {}
    with redirect_stdout(stream):
        exec(code, namespace)
    return stream.getvalue().splitlines()


def test_exact_comment_import_forms_become_dedicated_nodes_and_lower_to_python():
    source = '''COMMENT import decimal
COMMENT import collections AS coll
COMMENT from math import sqrt
COMMENT from math import floor, ceil
COMMENT from statistics import *
'''
    parsed = parse_strict(source)
    assert all(isinstance(node, ImportDirectiveNode) for node in parsed.ast.body)
    code = compile_strict(source)
    assert 'import decimal' in code
    assert 'import collections as coll' in code
    assert 'from math import sqrt' in code
    assert 'from math import floor, ceil' in code
    assert 'from statistics import *' in code


def test_import_directives_bind_explicit_module_aliases_and_from_import_names():
    parse_strict(
        'COMMENT import decimal\n'
        'module_value <- decimal\n'
        'COMMENT import collections AS coll\n'
        'alias_value <- coll\n'
        'COMMENT from math import pi\n'
        'constant_value <- pi\n'
    )


def test_near_miss_comment_text_remains_non_executable_comment():
    source = '''COMMENT import string later if needed
COMMENT this code may import math
COMMENT from * import math
'''
    parsed = parse_strict(source)
    assert all(isinstance(node, CommentNode) for node in parsed.ast.body)
    assert not any(isinstance(node, ImportDirectiveNode) for node in parsed.ast.body)
    code = compile_strict(source)
    assert '# import string later if needed' in code
    assert '# this code may import math' in code
    assert '# from * import math' in code


def test_string_punctuation_adapter_requires_no_algorithm_specific_rule():
    source = '''COMMENT import string
character <- STRING("!")
result <- character IN string_method_punctuation
OUTPUT result
'''
    code = compile_strict(source)
    assert 'import string' in code
    assert 'string.punctuation' in code
    assert 'string_method_punctuation' not in code
    assert run_strict(source) == ['True']


def test_algorithm5_style_source_now_matches_reference_behaviour():
    source = '''COMMENT import string

string1 <- STRING("This /_@!^*%<>is &*;:'a sentence, that has punctuation!")
string2 <- EMPTY LIST
FOR EACH character IN string1 DO
    APPEND character TO string2
ENDFOR
x <- EMPTY LIST
FOR EACH s IN string2 DO
    filtered_chars <- EMPTY LIST
    FOR EACH char IN s DO
        IF char NOT IN string_method_punctuation THEN
            APPEND char TO filtered_chars
        ENDIF
    ENDFOR
    APPEND JOIN(filtered_chars, EMPTY STRING) TO x
ENDFOR
final <- JOIN(x, EMPTY STRING)
OUTPUT final
'''
    assert run_strict(source) == ['This is a sentence that has punctuation']


def test_algorithm7_style_source_now_matches_reference_behaviour():
    source = '''COMMENT import string

string1 <- STRING("This is a sentence!")
string2 <- EMPTY LIST
FOR EACH character IN string1 DO
    APPEND character TO string2
ENDFOR
x <- EMPTY LIST
FOR EACH s IN string2 DO
    filtered_chars <- EMPTY LIST
    FOR EACH char IN s DO
        IF char NOT IN string_method_punctuation THEN
            APPEND char TO filtered_chars
        ENDIF
    ENDFOR
    APPEND JOIN(filtered_chars, EMPTY STRING) TO x
ENDFOR
word <- EMPTY STRING
words <- EMPTY LIST
flag <- BOOLEAN(TRUE)
delimiter <- STRING(" ")
WHILE flag DO
    TRY
        element <- x.pop(0)
        IF element != delimiter THEN
            word <- word + element
        ELSE
            APPEND word TO words
            word <- EMPTY STRING
        ENDIF
    CATCH
        APPEND word TO words
        flag <- BOOLEAN(FALSE)
    ENDTRY
ENDWHILE
OUTPUT words
'''
    assert run_strict(source) == ["['This', 'is', 'a', 'sentence']"]


def test_import_directive_is_preserved_as_import_flow_operation():
    parsed = parse_strict('COMMENT import string\nOUTPUT STRING("ok")\n')
    flow = FlowDiagramEncoder().encode(parsed.ast).to_dict()
    body = flow['structured_program']['body']
    assert body[0]['kind'] == 'ImportDirectiveNode'
    assert body[0]['directive_type'] == 'IMPORT'
    assert body[0]['module'] == 'string'
    import_nodes = [node for node in flow['nodes'].values() if node['node_type'] == 'IMPORT']
    assert import_nodes


def test_wildcard_import_is_rejected_inside_function_scope():
    result = AJParserFacade().parse(
        'FUNCTION demo ACCEPTS()\n'
        'COMMENT from math import *\n'
        'RETURN 1\n'
        'ENDFUNCTION\n'
    )
    assert not result.success
    assert 'Wildcard' in (result.error or '')
