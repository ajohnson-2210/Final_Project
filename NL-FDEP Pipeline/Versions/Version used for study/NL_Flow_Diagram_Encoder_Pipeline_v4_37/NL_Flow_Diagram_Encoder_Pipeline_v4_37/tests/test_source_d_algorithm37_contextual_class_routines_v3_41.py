from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def compile_source(processed_source: str) -> str:
    parsed = AJParserFacade().parse(processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return compiled.source_code


def test_gc241_contextual_class_procedure_and_function_become_methods_end_to_end():
    source = '''CLASS Counter:
    CONSTRUCTOR(value):
        self.value = value

    PROCEDURE Update(value):
        self.value = value

    FUNCTION Get():
        RETURN self.value
'''
    result = process(source)
    assert any(t.rule == "GC241" for t in result.transformations)
    assert "CLASS Counter" in result.processed_source
    assert "CONSTRUCTOR ACCEPTS(value)" in result.processed_source
    assert "METHOD Update ACCEPTS(value)" in result.processed_source
    assert "METHOD Get ACCEPTS()" in result.processed_source
    assert "ENDCONSTRUCTOR" in result.processed_source
    assert result.processed_source.count("ENDMETHOD") == 2
    assert result.processed_source.rstrip().endswith("ENDCLASS")
    assert "CALL ACCEPTS" not in result.processed_source
    assert all(t.rule != "GC086" for t in result.transformations)

    compiled = compile_source(result.processed_source)
    namespace = {}
    exec(compiled, namespace)
    counter = namespace["Counter"](3)
    assert counter.Get() == 3
    counter.Update(9)
    assert counter.Get() == 9


def test_gc241_recovers_source_d37_routine_structure_and_gc242_handles_later_assignment_boundary():
    source = '''CLASS Stack:
    CONSTRUCTOR(capacity):
        self.arr = Array of size capacity
        self.top_index = -1

    PROCEDURE Push(item):
        IF self.top_index == length(self.arr) - 1 THEN RETURN "Overflow Error"
        self.top_index = self.top_index + 1
        self.arr[self.top_index] = item

    FUNCTION Pop():
        IF self.top_index == -1 THEN RETURN "Underflow Error"
        item = self.arr[self.top_index]
        self.top_index = self.top_index - 1
        RETURN item

    FUNCTION Peek():
        IF self.top_index == -1 THEN RETURN "Stack Empty"
        RETURN self.arr[self.top_index]
'''
    result = process(source)
    assert any(t.rule == "GC240" for t in result.transformations)
    assert any(t.rule == "GC241" for t in result.transformations)
    assert "CONSTRUCTOR ACCEPTS(capacity)" in result.processed_source
    assert "METHOD Push ACCEPTS(item)" in result.processed_source
    assert "METHOD Pop ACCEPTS()" in result.processed_source
    assert "METHOD Peek ACCEPTS()" in result.processed_source
    assert "self.arr <- CALL create_array(capacity, NONE)" in result.processed_source
    assert any(t.rule == "GC242" for t in result.transformations)
    assert "self.arr[self.top_index] <- item" in result.processed_source
    assert "CALL ACCEPTS" not in result.processed_source
    assert all(t.rule != "GC086" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_gc241_does_not_reclassify_top_level_procedure():
    source = '''PROCEDURE Reset(value):
    RETURN value
'''
    result = process(source)
    assert all(t.rule != "GC241" for t in result.transformations)
    assert "FUNCTION Reset ACCEPTS(value)" in result.processed_source
    assert "METHOD Reset" not in result.processed_source


def test_gc241_preserves_explicit_class_and_routine_terminators_without_duplication():
    source = '''CLASS Box:
    CONSTRUCTOR(value):
        self.value = value
    END CONSTRUCTOR
    FUNCTION Get():
        RETURN self.value
    END FUNCTION
END CLASS
'''
    result = process(source)
    assert any(t.rule == "GC241" for t in result.transformations)
    assert result.processed_source.count("ENDCONSTRUCTOR") == 1
    assert result.processed_source.count("ENDMETHOD") == 1
    assert result.processed_source.count("ENDCLASS") == 1
    compile_source(result.processed_source)


def test_gc241_refuses_class_boundary_when_top_level_material_follows():
    source = '''CLASS Box:
    FUNCTION Get():
        RETURN 1
END CLASS
OUTPUT 2
'''
    result = process(source)
    assert all(t.rule != "GC241" for t in result.transformations)
