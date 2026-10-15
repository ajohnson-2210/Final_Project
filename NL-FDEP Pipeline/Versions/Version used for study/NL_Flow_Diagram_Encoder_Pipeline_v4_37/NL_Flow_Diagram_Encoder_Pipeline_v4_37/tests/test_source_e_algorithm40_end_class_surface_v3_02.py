from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''CLASS QUEUE
  stack1 = []
  stack2 = []

  FUNCTION ENQUEUE(element)
    stack1.push(element)

  FUNCTION DEQUEUE()
    IF stack2 IS EMPTY THEN
      WHILE stack1 IS NOT EMPTY
        stack2.push(stack1.pop())
      END WHILE
    END IF
    RETURN stack2.pop()

END CLASS
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_source_e_algorithm40_end_class_surface_reaches_existing_class_recovery():
    result = _process(SOURCE)

    assert "END CLASS" not in result.processed_source.upper()
    assert result.processed_source.rstrip().endswith("ENDCLASS")
    assert "PROPERTY stack1 AS LIST" in result.processed_source
    assert "PROPERTY stack2 AS LIST" in result.processed_source
    assert "METHOD ENQUEUE ACCEPTS(element)" in result.processed_source
    assert "APPEND element TO THIS.stack1" in result.processed_source
    assert "APPEND THIS.stack1.pop() TO THIS.stack2" in result.processed_source

    rules = [item.rule for item in result.transformations]
    assert "GC205" in rules
    assert "GC202" in rules
    assert "GC203" in rules

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success

    namespace = {}
    exec(compiled.source_code, namespace)
    queue = namespace["QUEUE"]()
    queue.ENQUEUE(1)
    queue.ENQUEUE(2)
    queue.ENQUEUE(3)
    assert queue.DEQUEUE() == 1
    assert queue.DEQUEUE() == 2
    assert queue.DEQUEUE() == 3
