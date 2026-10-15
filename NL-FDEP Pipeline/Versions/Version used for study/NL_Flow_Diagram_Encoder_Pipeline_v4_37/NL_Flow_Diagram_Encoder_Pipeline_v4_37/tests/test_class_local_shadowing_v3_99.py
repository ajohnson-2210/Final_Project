from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def _compile(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    return compiled.source_code


def test_method_assignment_shadows_same_named_explicit_property():
    source = '''CLASS Demo
    PROPERTY value AS INTEGER

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.value <- 1
    ENDCONSTRUCTOR

    METHOD local_test ACCEPTS()
        value <- 5
        RETURN value
    ENDMETHOD
ENDCLASS
'''
    python = _compile(source)
    assert 'self.value = 1' in python
    assert 'def local_test(self):\n        value = 5\n        return value' in python
    assert 'def local_test(self):\n        self.value = 5' not in python


def test_explicit_this_property_access_remains_instance_state():
    source = '''CLASS Demo
    PROPERTY value AS INTEGER

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.value <- 1
    ENDCONSTRUCTOR

    METHOD read ACCEPTS()
        RETURN THIS.value
    ENDMETHOD
ENDCLASS
'''
    python = _compile(source)
    assert 'def read(self):\n        return self.value' in python


def test_constructor_unqualified_collision_is_local_when_property_is_explicit():
    source = '''CLASS Demo
    PROPERTY value AS INTEGER

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.value <- 1
        value <- 5
    ENDCONSTRUCTOR

    METHOD read ACCEPTS()
        RETURN THIS.value
    ENDMETHOD
ENDCLASS
'''
    python = _compile(source)
    assert 'self.value = 1' in python
    assert '\n        value = 5\n' in python
    assert 'self.value = 5' not in python


def test_nested_helper_assignment_shadows_same_named_property():
    source = '''CLASS Demo
    PROPERTY value AS INTEGER

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.value <- 1
    ENDCONSTRUCTOR

    METHOD local_test ACCEPTS()
        FUNCTION helper ACCEPTS()
            value <- 5
            RETURN value
        ENDFUNCTION
        RETURN CALL helper()
    ENDMETHOD
ENDCLASS
'''
    python = _compile(source)
    assert 'def helper():\n            value = 5\n            return value' in python
    assert 'def helper():\n            self.value = 5' not in python
