import pytest

from aj_parser import AJParserFacade


def parse(source: str):
    return AJParserFacade().parse(source)


def assert_static_fail(source: str, needle: str):
    result = parse(source)
    assert not result.success
    assert needle in (result.error or "")


def test_reassignment_to_typed_parameter_rejects_explicit_incompatible_value():
    assert_static_fail(
        """FUNCTION f ACCEPTS(x AS INTEGER)\nx <- STRING(\"bad\")\nRETURN x\nENDFUNCTION\n""",
        "expects INTEGER, found STRING",
    )


def test_numeric_declared_parameter_accepts_other_explicit_numeric_type():
    result = parse(
        """FUNCTION f ACCEPTS(x AS FLOAT)\nx <- INTEGER(1)\nRETURN x\nENDFUNCTION\n"""
    )
    assert result.success, result.error


def test_unknown_value_does_not_trigger_declared_type_guessing():
    result = parse(
        """FUNCTION f ACCEPTS(x AS INTEGER, y)\nx <- y\nRETURN x\nENDFUNCTION\n"""
    )
    assert result.success, result.error


def test_typed_property_assignment_rejects_explicit_incompatible_value():
    assert_static_fail(
        """CLASS Demo\nPROPERTY value AS INTEGER\nCONSTRUCTOR ACCEPTS()\nPROPERTY THIS.value <- STRING(\"bad\")\nENDCONSTRUCTOR\nENDCLASS\n""",
        "property Demo.value expects INTEGER, found STRING",
    )


def test_typed_free_function_argument_rejects_explicit_incompatible_value():
    assert_static_fail(
        """FUNCTION f ACCEPTS(x AS INTEGER)\nRETURN x\nENDFUNCTION\nFUNCTION g ACCEPTS()\nRETURN CALL f(STRING(\"bad\"))\nENDFUNCTION\n""",
        "function 'f' expects INTEGER, found STRING",
    )


def test_external_function_signature_remains_unknown():
    result = parse(
        """FUNCTION g ACCEPTS()\nRETURN CALL external_helper(STRING(\"value\"))\nENDFUNCTION\n"""
    )
    assert result.success, result.error


def test_this_method_typed_argument_rejects_explicit_incompatible_value():
    assert_static_fail(
        """CLASS Demo\nMETHOD f ACCEPTS(x AS INTEGER)\nRETURN x\nENDMETHOD\nMETHOD g ACCEPTS()\nRETURN THIS.f(STRING(\"bad\"))\nENDMETHOD\nENDCLASS\n""",
        "method Demo.f expects INTEGER, found STRING",
    )


def test_explicitly_typed_class_receiver_method_argument_is_checked():
    assert_static_fail(
        """CLASS Demo\nMETHOD f ACCEPTS(x AS INTEGER)\nRETURN x\nENDMETHOD\nENDCLASS\nFUNCTION use ACCEPTS(d AS Demo)\nRETURN d.f(STRING(\"bad\"))\nENDFUNCTION\n""",
        "method Demo.f expects INTEGER, found STRING",
    )


def test_typed_property_chain_supplies_argument_type_evidence():
    assert_static_fail(
        """CLASS Child\nMETHOD take ACCEPTS(x AS INTEGER)\nRETURN x\nENDMETHOD\nENDCLASS\nCLASS Parent\nPROPERTY child AS Child\nPROPERTY text AS STRING\nMETHOD run ACCEPTS()\nRETURN THIS.child.take(THIS.text)\nENDMETHOD\nENDCLASS\n""",
        "method Child.take expects INTEGER, found STRING",
    )


def test_nested_local_assignment_shadows_outer_typed_parameter():
    result = parse(
        """FUNCTION outer ACCEPTS(x AS INTEGER)\nFUNCTION inner ACCEPTS()\nx <- STRING(\"local\")\nRETURN x\nENDFUNCTION\nRETURN x\nENDFUNCTION\n"""
    )
    assert result.success, result.error


def test_nested_parameter_shadows_outer_typed_parameter():
    result = parse(
        """FUNCTION outer ACCEPTS(x AS INTEGER)\nFUNCTION inner ACCEPTS(x AS STRING)\nx <- STRING(\"ok\")\nRETURN x\nENDFUNCTION\nRETURN x\nENDFUNCTION\n"""
    )
    assert result.success, result.error
