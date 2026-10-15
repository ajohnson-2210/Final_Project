import contextlib
import io
from pathlib import Path

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


CANONICAL_HANOI = '''FUNCTION unnamed_function ACCEPTS(N)
    FUNCTION Hanoi ACCEPTS(Discs, Source, Auxiliary, Destination)
        IF Discs == 1 THEN
            OUTPUT STRING("Move disk from {Source} to {Destination}")
        ELSE
            CALL Hanoi(Discs - 1, Source, Destination, Auxiliary)

            OUTPUT STRING("Move disk from {Source} to {Destination}")

            CALL Hanoi(Discs - 1, Auxiliary, Source, Destination)
        ENDIF
    ENDFUNCTION

    CALL Hanoi(N, STRING("A"), STRING("B"), STRING("C"))
ENDFUNCTION'''


RAW_HANOI = '''BEGIN
    INPUT N

    FUNCTION Hanoi(Discs, Source, Auxiliary, Destination)
        IF Discs = 1 THEN
            OUTPUT "Move disk from", Source, "to", Destination
        ELSE
            Hanoi(Discs-1, Source, Destination, Auxiliary)

            OUTPUT "Move disk from", Source, "to", Destination

            Hanoi(Discs-1, Auxiliary, Source, Destination)
        ENDIF
    END FUNCTION

    Hanoi(N, "A", "B", "C")
END
'''


def _compile(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast)).source_code


def test_v12_spec_formally_adds_nested_functions_but_not_callbacks():
    spec = Path('docs/AJ_24038155_Dialect_v1_2.md').read_text()
    assert 'nested/local function declarations' in spec
    assert 'does **not** add callbacks' in spec
    assert 'first-class function values' in spec
    assert 'must not hoist' in spec


def test_parser_and_compiler_preserve_nested_function_scope():
    python_source = _compile(CANONICAL_HANOI)
    assert '\ndef unnamed_function(N):\n' in python_source
    assert '\n    def Hanoi(Discs, Source, Auxiliary, Destination):\n' in python_source
    assert '\ndef Hanoi(Discs, Source, Auxiliary, Destination):\n' not in python_source
    assert "\n    Hanoi(N, 'A', 'B', 'C')" in python_source


def test_nested_hanoi_executes_inside_outer_function():
    python_source = _compile(CANONICAL_HANOI)
    namespace = {}
    exec(python_source, namespace)
    assert 'Hanoi' not in namespace
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        namespace['unnamed_function'](2)
    assert output.getvalue().splitlines() == [
        'Move disk from A to B',
        'Move disk from A to C',
        'Move disk from B to C',
    ]


def test_gc170_uses_v12_nested_function_and_external_n():
    result = PseudocodeProfileProcessor().process(
        RAW_HANOI,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )
    assert result.processed_source == CANONICAL_HANOI
    assert any(t.rule == 'GC170' for t in result.transformations)
    assert 'INPUT(' not in result.processed_source
    assert 'integer_value' not in result.processed_source
    assert 'Enter N' not in result.processed_source

    python_source = _compile(result.processed_source)
    assert '\ndef unnamed_function(N):\n' in python_source
    assert '\n    def Hanoi(Discs, Source, Auxiliary, Destination):\n' in python_source
    assert 'input(' not in python_source
    assert '= int(' not in python_source
    assert ('print(f\"Move disk from {Source} to {Destination}\")' in python_source or "print(f'Move disk from {Source} to {Destination}')" in python_source)
