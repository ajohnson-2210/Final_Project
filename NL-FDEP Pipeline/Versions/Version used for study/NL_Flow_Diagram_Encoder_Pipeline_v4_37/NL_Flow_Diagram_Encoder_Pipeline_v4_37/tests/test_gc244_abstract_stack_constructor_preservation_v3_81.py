from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def compile_source(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return compiled.source_code


def test_exact_stack_constructor_preserves_stack_abstraction_in_class_state():
    source = """CLASS Holder:
    CONSTRUCTOR():
        self.items = Stack()
    PROCEDURE Add(value):
        self.items.push(value)
    FUNCTION Remove():
        RETURN self.items.pop()
"""
    result = process(source)
    canonical = result.processed_source
    assert any(t.rule == "GC244" for t in result.transformations)
    assert "self.items <- CALL create_stack()" in canonical
    assert "CALL PUSH(value, self.items)" in canonical
    assert "RETURN CALL POP(self.items)" in canonical
    assert "EMPTY LIST" not in canonical
    assert "APPEND value TO self.items" not in canonical

    python_source = compile_source(canonical)
    assert "self.items = []" in python_source
    assert "self.items.append(value)" in python_source
    assert "return self.items.pop(-1)" in python_source


def test_explicit_stack_constructor_plus_empty_query_preserves_stack_abstraction():
    source = """CLASS Holder:
    CONSTRUCTOR():
        self.items = Stack()
    FUNCTION Empty():
        RETURN self.items.isEmpty()
"""
    result = process(source)
    canonical = result.processed_source
    assert any(t.rule == "GC244" for t in result.transformations)
    assert "self.items <- CALL create_stack()" in canonical
    assert "RETURN CALL stack_is_empty(self.items)" in canonical
    assert "EMPTY LIST" not in canonical

    python_source = compile_source(canonical)
    assert "self.items = []" in python_source
    assert "return (len(self.items) == 0)" in python_source


def test_explicit_list_constructor_is_not_reclassified_as_stack():
    source = """CLASS Holder:
    CONSTRUCTOR():
        self.items = []
    PROCEDURE Add(value):
        self.items.append(value)
"""
    result = process(source)
    assert all(t.rule != "GC244" for t in result.transformations)
    assert "CALL create_stack()" not in result.processed_source
