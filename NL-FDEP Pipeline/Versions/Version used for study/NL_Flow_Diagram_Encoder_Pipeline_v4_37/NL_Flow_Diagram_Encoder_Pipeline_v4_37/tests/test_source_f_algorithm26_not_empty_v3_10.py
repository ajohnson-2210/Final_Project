from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_f_26 = '''INPUT root

IF root == null:
    RETURN []

queue = [root]
result = []

WHILE queue not empty:
    levelSize = length(queue)
    currentLevel = []

    FOR _ from 0 to levelSize-1:
        node = queue.pop(0)
        currentLevel.append(node.value)

        IF node.left:
            queue.append(node.left)

        IF node.right:
            queue.append(node.right)

    result.append(currentLevel)

RETURN result
'''


def test_exact_source_f_26_uses_only_omitted_is_empty_predicate_recovery():
    result = PseudocodeProfileProcessor().process(
        source_f_26,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )
    assert 'WHILE LENGTH OF queue > 0 DO' in result.processed_source
    assert sum(item.rule == 'GC211' for item in result.transformations) == 1

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    assert 'while (len(queue) > 0):' in compiled.source_code
    assert 'node = queue.pop(0)' in compiled.source_code
    assert 'currentLevel.append(node.value)' in compiled.source_code
    assert 'queue.append(node.left)' in compiled.source_code
    assert 'queue.append(node.right)' in compiled.source_code
    assert 'result.append(currentLevel)' in compiled.source_code
