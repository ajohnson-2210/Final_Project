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


source_d_40 = '''CLASS QueueUsingStacks:
    CONSTRUCTOR():
        self.stack_in = Stack()
        self.stack_out = Stack()

    PROCEDURE Enqueue(item):
        self.stack_in.push(item)

    FUNCTION Dequeue():
        IF self.stack_out.isEmpty() THEN
            WHILE NOT self.stack_in.isEmpty() DO
                self.stack_out.push(self.stack_in.pop())
            END WHILE
        END IF

        IF self.stack_out.isEmpty() THEN RETURN "Queue Empty"
        RETURN self.stack_out.pop()
'''


def test_gc244_recovers_exact_source_d40_and_executes_fifo_behaviour():
    result = process(source_d_40)
    assert any(t.rule == "GC244" for t in result.transformations)
    assert "self.stack_in <- CALL create_stack()" in result.processed_source
    assert "self.stack_out <- CALL create_stack()" in result.processed_source
    assert "CALL PUSH(item, self.stack_in)" in result.processed_source
    assert "IF CALL stack_is_empty(self.stack_out) THEN" in result.processed_source
    assert "WHILE NOT CALL stack_is_empty(self.stack_in) DO" in result.processed_source
    assert "CALL PUSH(CALL POP(self.stack_in), self.stack_out)" in result.processed_source
    assert "RETURN CALL POP(self.stack_out)" in result.processed_source
    assert "EMPTY LIST" not in result.processed_source

    python_source = compile_source(result.processed_source)
    assert "self.stack_in = []" in python_source
    assert "self.stack_out = []" in python_source
    assert "temp = self.stack_in.pop(-1)" in python_source
    assert "self.stack_out.append(temp)" in python_source

    namespace = {}
    exec(python_source, namespace)
    queue = namespace["QueueUsingStacks"]()
    queue.Enqueue("A")
    queue.Enqueue("B")
    queue.Enqueue("C")
    assert queue.Dequeue() == "A"
    assert queue.Dequeue() == "B"
    queue.Enqueue("D")
    assert queue.Dequeue() == "C"
    assert queue.Dequeue() == "D"
    assert queue.Dequeue() == "Queue Empty"


def test_gc244_refuses_local_stack_constructor_outside_class_state():
    source = '''FUNCTION make ACCEPTS()
    stack <- Stack()
    stack.push(1)
    RETURN stack
ENDFUNCTION
'''
    result = process(source)
    assert all(t.rule != "GC244" for t in result.transformations)
    assert "stack <- CALL Stack()" in result.processed_source


def test_gc244_refuses_stack_constructor_with_arguments():
    source = '''CLASS Holder:
    CONSTRUCTOR():
        self.stack = Stack(10)
    PROCEDURE Add(value):
        self.stack.push(value)
'''
    result = process(source)
    assert all(t.rule != "GC244" for t in result.transformations)
    assert "self.stack <- CALL Stack(10)" in result.processed_source


def test_gc244_refuses_constructor_member_without_stack_usage_evidence():
    source = '''CLASS Holder:
    CONSTRUCTOR():
        self.stack = Stack()
    FUNCTION Get():
        RETURN self.stack
'''
    result = process(source)
    assert all(t.rule != "GC244" for t in result.transformations)
    assert "self.stack <- CALL Stack()" in result.processed_source


def test_gc244_refuses_member_that_is_rebound_after_initialisation():
    source = '''CLASS Holder:
    CONSTRUCTOR():
        self.stack = Stack()
    PROCEDURE Reset():
        self.stack = replacement
    PROCEDURE Add(value):
        self.stack.push(value)
'''
    result = process(source)
    assert all(t.rule != "GC244" for t in result.transformations)
    assert "self.stack <- CALL Stack()" in result.processed_source
    assert "self.stack <- replacement" in result.processed_source
