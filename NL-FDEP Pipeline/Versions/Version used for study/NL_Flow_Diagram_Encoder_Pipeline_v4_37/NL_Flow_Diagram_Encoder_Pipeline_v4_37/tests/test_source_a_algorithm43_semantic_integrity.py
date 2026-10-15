from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm43():
    return '''BEGIN
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


def test_source_a_algorithm43_preserves_nested_hanoi_scope_and_external_input():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm43(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    expected = '''FUNCTION unnamed_function ACCEPTS(N)
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
    assert result.processed_source == expected

    assert any(t.rule == "GC170" for t in result.transformations)
    assert "INPUT(" not in result.processed_source
    assert "Enter N" not in result.processed_source
    assert "integer_value" not in result.processed_source
    assert "OUTPUT TUPLE" not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error

    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "\ndef unnamed_function(N):\n" in compiled.source_code
    assert "\n    def Hanoi(Discs, Source, Auxiliary, Destination):\n" in compiled.source_code
    assert "\ndef Hanoi(Discs, Source, Auxiliary, Destination):\n" not in compiled.source_code
    assert "Hanoi((Discs - 1), Source, Destination, Auxiliary)" in compiled.source_code
    assert "Hanoi((Discs - 1), Auxiliary, Source, Destination)" in compiled.source_code
    assert ('print(f\"Move disk from {Source} to {Destination}\")' in compiled.source_code or "print(f'Move disk from {Source} to {Destination}')" in compiled.source_code)
    assert "input(" not in compiled.source_code


def test_fstring_rendering_is_narrow_and_does_not_rewrite_arithmetic_output():
    parsed = AJParserFacade().parse("OUTPUT Left + Right")
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "print((Left + Right))" in compiled.source_code
    assert "print(f" not in compiled.source_code
