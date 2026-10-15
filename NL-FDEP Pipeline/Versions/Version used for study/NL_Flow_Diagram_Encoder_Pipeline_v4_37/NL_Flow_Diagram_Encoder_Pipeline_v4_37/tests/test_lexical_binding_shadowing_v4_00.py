from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def _compile(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    return compiled.source_code


def test_foreach_variable_shadows_same_named_explicit_property():
    source = '''CLASS Demo
    PROPERTY item AS INTEGER

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.item <- 0
    ENDCONSTRUCTOR

    METHOD total ACCEPTS(values)
        FOR EACH item IN values DO
            OUTPUT item
        ENDFOR
        RETURN THIS.item
    ENDMETHOD
ENDCLASS
'''
    python = _compile(source)
    assert 'for item in values:' in python
    assert 'for self.item in values:' not in python
    assert 'return self.item' in python


def test_range_variable_shadows_same_named_explicit_property():
    source = '''CLASS Demo
    PROPERTY i AS INTEGER

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.i <- 99
    ENDCONSTRUCTOR

    METHOD total ACCEPTS(limit)
        FOR i <- IN RANGE 0 TO limit DO
            OUTPUT i
        ENDFOR
        RETURN THIS.i
    ENDMETHOD
ENDCLASS
'''
    python = _compile(source)
    assert 'for i in range(0, limit):' in python
    assert 'for self.i in range' not in python
    assert 'return self.i' in python


def test_named_catch_variable_shadows_same_named_explicit_property():
    source = '''CLASS Demo
    PROPERTY error AS STRING

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.error <- STRING("saved")
    ENDCONSTRUCTOR

    METHOD run ACCEPTS()
        TRY
            RAISE STRING("boom")
        CATCH error
            OUTPUT error
        ENDTRY
        RETURN THIS.error
    ENDMETHOD
ENDCLASS
'''
    python = _compile(source)
    assert 'except Exception as error:' in python
    assert 'except Exception as self.error:' not in python
    assert 'print(error)' in python
    assert 'return self.error' in python


def test_nested_foreach_binding_shadows_enclosing_set_representation_hint():
    source = '''FUNCTION outer ACCEPTS(values)
    item <- EMPTY SET
    FUNCTION inner ACCEPTS(values)
        FOR EACH item IN values DO
            APPEND 1 TO item
        ENDFOR
    ENDFUNCTION
    RETURN item
ENDFUNCTION
'''
    python = _compile(source)
    assert 'item = set()' in python
    assert 'for item in values:' in python
    assert 'item.append(1)' in python
    assert 'item.add(1)' not in python


def test_nested_function_declaration_shadows_same_named_property():
    source = '''CLASS Demo
    PROPERTY helper AS INTEGER

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.helper <- 7
    ENDCONSTRUCTOR

    METHOD local_test ACCEPTS()
        FUNCTION helper ACCEPTS()
            RETURN 1
        ENDFUNCTION
        RETURN helper
    ENDMETHOD
ENDCLASS
'''
    python = _compile(source)
    assert 'def helper():' in python
    assert 'return helper' in python
    assert 'return self.helper' not in python
