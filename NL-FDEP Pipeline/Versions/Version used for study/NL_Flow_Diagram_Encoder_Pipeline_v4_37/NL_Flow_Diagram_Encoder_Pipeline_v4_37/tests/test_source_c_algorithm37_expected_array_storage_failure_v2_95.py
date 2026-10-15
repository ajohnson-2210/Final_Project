from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_c_ALGORITHM_37 = '''CLASS Stack:
    stackArray = empty array
    topIndex = -1

    FUNCTION push(item):
        topIndex = topIndex + 1
        stackArray[topIndex] = item

    FUNCTION pop():
        IF topIndex < 0:
            RETURN NULL // Stack underflow
        item = stackArray[topIndex]
        topIndex = topIndex - 1
        RETURN item

    FUNCTION peek():
        IF topIndex < 0:
            RETURN NULL
        RETURN stackArray[topIndex]
'''


def test_source_c_algorithm37_remains_expected_failure_without_array_growth_reconstruction():
    processed = PseudocodeProfileProcessor().process(
        source_c_ALGORITHM_37,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )

    # Structural and representational normalisation may occur, but the source's
    # indexed write must not be replaced by invented growth behaviour.
    assert "stackArray <- CALL create_array(0, NONE)" in processed.processed_source
    assert "stackArray[topIndex] <- item" in processed.processed_source
    assert "APPEND item TO stackArray" not in processed.processed_source
    assert "append(item)" not in processed.processed_source
    assert "LENGTH OF stackArray" not in processed.processed_source

    parsed = AJParserFacade().parse(processed.processed_source)
    assert not parsed.success
    assert "ENDCLASS" in parsed.error
