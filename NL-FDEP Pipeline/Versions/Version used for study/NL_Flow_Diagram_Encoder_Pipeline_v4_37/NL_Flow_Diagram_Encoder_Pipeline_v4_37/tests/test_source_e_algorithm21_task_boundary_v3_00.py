import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from corpus_evaluator import ExampleSectionAdapter
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor
from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler


def test_source_e_algorithm21_heading_is_not_part_of_previous_source():
    text = '''21. Create a process that determines whether a number is even or odd
FUNCTION IS_EVEN(n)
  IF n MOD 2 == 0 THEN
    RETURN TRUE
  ELSE
    RETURN FALSE
  END IF
END FUNCTION
22. Design a procedure that computes the factorial of a positive integer
FUNCTION FACTORIAL(n)
  IF n == 0 OR n == 1 THEN
    RETURN 1
  ELSE
    RETURN n * FACTORIAL(n - 1)
  END IF
END FUNCTION
'''
    examples = ExampleSectionAdapter().extract(text, 'source_e')
    assert len(examples) == 2
    assert examples[0].task_number == 1
    assert examples[0].source.endswith('END FUNCTION')
    assert '22. Design' not in examples[0].source

    result = PseudocodeProfileProcessor().process(
        examples[0].source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    namespace = {}
    exec(compiled.source_code, namespace)
    assert namespace['IS_EVEN'](4) is True
    assert namespace['IS_EVEN'](5) is False
