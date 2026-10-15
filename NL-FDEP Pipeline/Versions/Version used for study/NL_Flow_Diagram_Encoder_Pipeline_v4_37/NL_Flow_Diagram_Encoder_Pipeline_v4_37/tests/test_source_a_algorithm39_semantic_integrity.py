from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm39():
    # This fixture intentionally mirrors the *stored lossy corpus text*.
    # Literal ``?`` here is source-corruption evidence, not AJ syntax and not
    # a canonical alternative to ``<-``.  The compatibility recovery must
    # remove/resolve it before the AJ parser boundary.
    return '''BEGIN
    INPUT Head

    Slow ? Head
    Fast ? Head

    WHILE Fast ? NULL AND Fast.Next ? NULL
        Slow ? Slow.Next
        Fast ? Fast.Next.Next

        IF Slow = Fast THEN
            OUTPUT "Cycle Detected"
            STOP
        ENDIF
    ENDWHILE

    OUTPUT "No Cycle"
END
'''


def test_source_a_algorithm39_uses_structured_head_parameter_and_preserves_floyd_procedure():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm39(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    expected = '''FUNCTION unnamed_function ACCEPTS(Head)
    Slow <- Head
    Fast <- Head

    WHILE Fast != NULL AND Fast.Next != NULL DO
        Slow <- Slow.Next
        Fast <- Fast.Next.Next

        IF Slow == Fast THEN
            OUTPUT STRING("Cycle Detected")
            RETURN
        ENDIF
    ENDWHILE

    OUTPUT STRING("No Cycle")
ENDFUNCTION'''
    assert result.processed_source == expected
    assert "?" not in result.processed_source

    # No fabricated linked-list construction, text input, or opaque NULL call.
    assert "INPUT(STRING" not in result.processed_source
    assert "Head_Key" not in result.processed_source
    assert "lookup_inferred_linked_node" not in result.processed_source
    assert "CALL NULL()" not in result.processed_source
    assert "CALL quit()" not in result.processed_source

    # Preserve the model-authored Floyd state transitions exactly.
    assert "Slow <- Slow.Next" in result.processed_source
    assert "Fast <- Fast.Next.Next" in result.processed_source
    assert "IF Slow == Fast THEN" in result.processed_source
    assert "RETURN" in result.processed_source

    # The audit trail must not record transient STRING-input or NULL-call
    # conversions that are later reversed.
    assert all(t.rule != "GC096" for t in result.transformations)
    assert all("CALL NULL()" not in t.target for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error

    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "def unnamed_function(Head):" in compiled.source_code
    assert "Slow = Slow.Next" in compiled.source_code
    assert "Fast = Fast.Next.Next" in compiled.source_code
    assert "Fast is not None" in compiled.source_code
    assert "Fast.Next is not None" in compiled.source_code
    assert "return" in compiled.source_code
    assert "quit()" not in compiled.source_code
    assert "lookup_inferred_linked_node" not in compiled.source_code
    assert "InferredNode" not in compiled.source_code
    assert "import random" not in compiled.source_code


def test_explicit_null_assignment_stays_null_in_canonical_aj_and_lowers_to_python_none():
    source = "account <- NULL\n"
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    assert result.processed_source == source.rstrip("\n")

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "account = None" in compiled.source_code
    assert "account = NULL" not in compiled.source_code
