from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm47():
    return '''BEGIN
    INPUT Inventory
    INPUT TransactionType
    INPUT Item
    INPUT Quantity

    IF TransactionType = "Purchase" THEN
        Inventory[Item] ← Inventory[Item] - Quantity

    ELSE IF TransactionType = "Delivery" THEN
        Inventory[Item] ← Inventory[Item] + Quantity
    ENDIF

    OUTPUT Inventory
END
'''


def test_source_a_algorithm47_uses_neutral_wrapper_and_preserves_inventory_updates():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm47(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    expected = '''FUNCTION unnamed_function ACCEPTS(Inventory, TransactionType, Item, Quantity)
    IF TransactionType == STRING("Purchase") THEN
        Inventory[Item] <- Inventory[Item] - Quantity
    ELSE IF TransactionType == STRING("Delivery") THEN
        Inventory[Item] <- Inventory[Item] + Quantity
    ENDIF

    OUTPUT Inventory
ENDFUNCTION'''
    assert result.processed_source == expected
    assert any(t.rule == "GC172" for t in result.transformations)
    assert all(t.rule != "GC096" for t in result.transformations)
    assert "FUNCTION PROCESS" not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error

    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "def unnamed_function(Inventory, TransactionType, Item, Quantity):" in compiled.source_code
    assert "if (TransactionType == 'Purchase'):" in compiled.source_code
    assert "Inventory[Item] = (Inventory[Item] - Quantity)" in compiled.source_code
    assert "elif (TransactionType == 'Delivery'):" in compiled.source_code
    assert "Inventory[Item] = (Inventory[Item] + Quantity)" in compiled.source_code
    assert "print(Inventory)" in compiled.source_code


def test_source_a_algorithm47_does_not_invent_unstated_validation_or_inventory_rules():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm47(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    upper = result.processed_source.upper()
    for forbidden in (
        "INSUFFICIENT STOCK",
        "ITEM NOT",
        "NEGATIVE",
        "RAISE",
        "VALIDATE",
        "DEFAULT",
    ):
        assert forbidden not in upper
