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


def source_d37_source() -> str:
    return '''CLASS Stack:
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


def test_gc242_recovers_exact_source_d37_and_executes_stack_behaviour():
    result = process(source_d37_source())
    assert any(t.rule == "GC240" for t in result.transformations)
    assert any(t.rule == "GC241" for t in result.transformations)
    assert any(t.rule == "GC242" for t in result.transformations)
    assert "self.arr[self.top_index] <- item" in result.processed_source
    assert "self.arr[self.top_index] = item" not in result.processed_source

    compiled_source = compile_source(result.processed_source)
    assert "self.arr = [None] * capacity" in compiled_source
    assert "self.arr[self.top_index] = item" in compiled_source

    namespace = {}
    exec(compiled_source, namespace)
    stack = namespace["Stack"](2)
    assert stack.Peek() == "Stack Empty"
    assert stack.Push("a") is None
    assert stack.Peek() == "a"
    assert stack.Push("b") is None
    assert stack.Push("c") == "Overflow Error"
    assert stack.Pop() == "b"
    assert stack.Pop() == "a"
    assert stack.Pop() == "Underflow Error"


def test_gc242_accepts_member_path_followed_by_index_without_touching_rhs():
    result = process('object.buffer[i] = CALL transform(value)\n')
    assert any(t.rule == "GC242" for t in result.transformations)
    assert result.processed_source.strip() == "object.buffer[i] <- CALL transform(value)"


def test_gc242_refuses_comparison_operators():
    source = '''IF object.buffer[i] == value THEN
    RETURN BOOLEAN(TRUE)
ENDIF
IF object.buffer[i] != value THEN
    RETURN BOOLEAN(FALSE)
ENDIF
'''
    result = process(source)
    assert all(t.rule != "GC242" for t in result.transformations)
    assert "object.buffer[i] == value" in result.processed_source
    assert "object.buffer[i] != value" in result.processed_source


def test_gc242_does_not_relabel_plain_or_index_only_assignments():
    result = process('value = 1\nitems[i] = value\nobject.member = value\n')
    assert all(t.rule != "GC242" for t in result.transformations)
    assert "value <- 1" in result.processed_source
    assert "items[i] <- value" in result.processed_source
    assert "object.member <- value" in result.processed_source
    assert sum(t.rule == "GC026" for t in result.transformations) == 3
