from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''FUNCTION TOWER_OF_HANOI(N)
  FUNCTION MOVE(n, from_rod, to_rod, aux_rod)
    IF n == 1 THEN
      PRINT("Move disk 1 from rod " + from_rod + " to rod " + to_rod)
    ELSE
      MOVE(n - 1, from_rod, aux_rod, to_rod)
      PRINT("Move disk " + n + " from rod " + from_rod + " to rod " + to_rod)
      MOVE(n - 1, aux_rod, to_rod, from_rod)
    END IF
  END FUNCTION
  MOVE(N, "A", "C", "B")
END FUNCTION
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_source_e_algorithm43_uses_output_without_inserting_typecast(capsys):
    result = _process(SOURCE)

    assert 'OUTPUT STRING("Move disk 1 from rod ") + from_rod + STRING(" to rod ") + to_rod' in result.processed_source
    assert 'OUTPUT STRING("Move disk ") + n + STRING(" from rod ") + from_rod + STRING(" to rod ") + to_rod' in result.processed_source
    assert 'CALL to_string' not in result.processed_source
    assert 'CALL PRINT' not in result.processed_source
    assert sum(item.rule == 'GC206' for item in result.transformations) == 2

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    assert 'print(f"Move disk {n} from rod {from_rod} to rod {to_rod}")' in compiled.source_code
    assert 'str(n)' not in compiled.source_code

    namespace = {}
    exec(compiled.source_code, namespace)
    namespace['TOWER_OF_HANOI'](2)
    assert capsys.readouterr().out.splitlines() == [
        'Move disk 1 from rod A to rod B',
        'Move disk 2 from rod A to rod C',
        'Move disk 1 from rod B to rod C',
    ]
