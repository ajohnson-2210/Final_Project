import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_e_ALGORITHM_47 = '''FUNCTION UPDATE_INVENTORY(purchases, deliveries)
  inventory = []
  FOR item IN purchases
    IF item IN inventory THEN
      inventory[item] -= purchases[item]
    ELSE
      inventory[item] = -purchases[item]
    END IF
  END FOR
  FOR item IN deliveries
    IF item IN inventory THEN
      inventory[item] += deliveries[item]
    ELSE
      inventory[item] = deliveries[item]
    END IF
  END FOR
  RETURN inventory
END FUNCTION
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def _compile(processed_source: str) -> str:
    parsed = AJParserFacade().parse(processed_source)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast)).source_code


def test_source_e_algorithm47_preserves_explicit_empty_list_despite_later_keyed_access():
    processed = _process(source_e_ALGORITHM_47)

    assert "inventory <- EMPTY LIST" in processed.processed_source
    assert "inventory <- EMPTY DICTIONARY" not in processed.processed_source
    assert "inventory[item] <- -purchases[item]" in processed.processed_source
    assert "inventory[item] <- deliveries[item]" in processed.processed_source

    python_source = _compile(processed.processed_source)
    assert "inventory = []" in python_source
    assert "inventory = {}" not in python_source

    namespace = {}
    exec(python_source, namespace)
    with pytest.raises(TypeError):
        namespace["UPDATE_INVENTORY"](
            {"item1": 10, "item2": 20},
            {"item1": 5, "item3": 15},
        )
