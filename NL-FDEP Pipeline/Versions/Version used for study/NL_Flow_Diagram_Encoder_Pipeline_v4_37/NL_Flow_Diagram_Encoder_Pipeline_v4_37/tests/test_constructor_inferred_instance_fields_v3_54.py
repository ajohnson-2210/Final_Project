from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def compile_aj(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    return compiled.source_code


def test_direct_constructor_assignments_referenced_by_methods_become_instance_fields():
    source = '''CLASS Counter
    CONSTRUCTOR ACCEPTS()
        count <- 0
        label <- STRING("ready")
    ENDCONSTRUCTOR
    METHOD bump ACCEPTS()
        count <- count + 1
        RETURN count
    ENDMETHOD
    METHOD mark ACCEPTS()
        label <- label + STRING("!")
        RETURN label
    ENDMETHOD
ENDCLASS
'''
    python_source = compile_aj(source)
    assert "self.count = 0" in python_source
    assert "self.label = 'ready'" in python_source
    assert "self.count = (self.count + 1)" in python_source
    assert "self.label = (self.label + '!'" in python_source or "self.label = (self.label + '!)" in python_source
    assert "return self.label" in python_source

    namespace = {}
    exec(python_source, namespace)
    counter = namespace["Counter"]()
    assert counter.bump() == 1
    assert counter.mark() == "ready!"


def test_constructor_only_temporary_stays_local():
    source = '''CLASS Box
    CONSTRUCTOR ACCEPTS()
        scratch <- 7
        value <- 3
    ENDCONSTRUCTOR
    METHOD bump ACCEPTS()
        value <- value + 1
        RETURN value
    ENDMETHOD
ENDCLASS
'''
    python_source = compile_aj(source)
    assert "scratch = 7" in python_source
    assert "self.scratch" not in python_source
    assert "self.value = 3" in python_source
    assert "self.value = (self.value + 1)" in python_source
    assert "return self.value" in python_source


def test_method_parameter_shadows_an_inferred_field_in_that_method():
    source = '''CLASS Box
    CONSTRUCTOR ACCEPTS()
        value <- 3
    ENDCONSTRUCTOR
    METHOD bump ACCEPTS()
        value <- value + 1
        RETURN value
    ENDMETHOD
    METHOD echo ACCEPTS(value)
        RETURN value
    ENDMETHOD
ENDCLASS
'''
    python_source = compile_aj(source)
    assert "self.value = 3" in python_source
    assert "def echo(self, value):" in python_source
    echo_body = python_source.split("def echo(self, value):", 1)[1]
    assert "return value" in echo_body
    assert "return self.value" not in echo_body


def test_nested_constructor_assignment_is_not_promoted_by_direct_assignment_rule():
    source = '''CLASS Box
    CONSTRUCTOR ACCEPTS(flag)
        IF flag THEN
            hidden <- 1
        ENDIF
    ENDCONSTRUCTOR
    METHOD bump ACCEPTS()
        hidden <- hidden + 1
        RETURN hidden
    ENDMETHOD
ENDCLASS
'''
    python_source = compile_aj(source)
    assert "self.hidden" not in python_source
    assert "hidden = 1" in python_source
    assert "return hidden" in python_source


def test_explicit_property_and_this_semantics_remain_unchanged():
    source = '''CLASS Box
    PROPERTY value AS INTEGER
    CONSTRUCTOR ACCEPTS(value AS INTEGER)
        PROPERTY THIS.value <- value
    ENDCONSTRUCTOR
    METHOD get ACCEPTS()
        RETURN THIS.value
    ENDMETHOD
ENDCLASS
'''
    python_source = compile_aj(source)
    assert "self.value = value" in python_source
    assert "return self.value" in python_source
