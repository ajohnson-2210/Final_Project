import random

import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_f_ALGORITHM_40 = '''INIT s1 = []
s2 = []

FUNCTION enqueue(x):
    s1.push(x)

FUNCTION dequeue():
    IF s2 is empty:
        WHILE s1 not empty:
            s2.push(s1.pop())

    RETURN s2.pop()
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def _compile(processed_source: str) -> str:
    parsed = AJParserFacade().parse(processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return compiled.source_code


def test_source_f40_recovers_connected_two_list_outer_state_as_neutral_class():
    result = _process(source_f_ALGORITHM_40)

    assert "CLASS unnamed_class" in result.processed_source
    assert "PROPERTY s1 AS LIST" in result.processed_source
    assert "PROPERTY s2 AS LIST" in result.processed_source
    assert "CONSTRUCTOR ACCEPTS()" in result.processed_source
    assert "PROPERTY THIS.s1 <- EMPTY LIST" in result.processed_source
    assert "PROPERTY THIS.s2 <- EMPTY LIST" in result.processed_source
    assert "METHOD enqueue ACCEPTS(x)" in result.processed_source
    assert "METHOD dequeue ACCEPTS()" in result.processed_source
    assert "APPEND x TO THIS.s1" in result.processed_source
    assert "APPEND THIS.s1.pop() TO THIS.s2" in result.processed_source
    assert "RETURN THIS.s2.pop()" in result.processed_source
    assert [item.rule for item in result.transformations].count("GC218") == 1

    python_source = _compile(result.processed_source)
    assert "class unnamed_class:" in python_source
    assert "self.s1 = []" in python_source
    assert "self.s2 = []" in python_source

    namespace = {}
    exec(python_source, namespace)
    Queue = namespace["unnamed_class"]
    queue = Queue()
    queue.enqueue("A")
    queue.enqueue("B")
    queue.enqueue("C")
    assert queue.dequeue() == "A"
    assert queue.dequeue() == "B"
    queue.enqueue("D")
    assert queue.dequeue() == "C"
    assert queue.dequeue() == "D"
    with pytest.raises(IndexError):
        queue.dequeue()


def test_gc218_is_not_hardcoded_to_queue_or_state_names():
    source = '''left = []
right = []
FUNCTION add(value):
    left.append(value)
FUNCTION take():
    IF right is empty:
        WHILE left not empty:
            right.append(left.pop())
    RETURN right.pop()
'''
    result = _process(source)
    assert "PROPERTY left AS LIST" in result.processed_source
    assert "PROPERTY right AS LIST" in result.processed_source
    assert "METHOD add ACCEPTS(value)" in result.processed_source
    assert "METHOD take ACCEPTS()" in result.processed_source
    assert any(item.rule == "GC218" for item in result.transformations)


def test_gc218_audit_reports_source_proven_connected_multi_list_recovery():
    result = _process(source_f_ALGORITHM_40)
    entries = [
        item for item in result.to_dict()["transformations"]
        if item["branch"] == "EVIDENCED_CONNECTED_MULTI_LIST_CONSTRUCTOR"
    ]
    assert len(entries) == 1
    assert entries[0]["rule_family"] == "STATEFUL_ADT_STRUCTURE"
    assert entries[0]["confidence"] == "source_proven"
    assert entries[0]["semantic_change"] is False


def test_gc218_refuses_disconnected_state_operation_graph():
    source = '''a = []
b = []
FUNCTION put_a(x):
    a.append(x)
FUNCTION take_a():
    RETURN a.pop()
FUNCTION put_b(x):
    b.append(x)
FUNCTION take_b():
    RETURN b.pop()
'''
    result = _process(source)
    assert not any(item.rule == "GC218" for item in result.transformations)


def test_gc218_refuses_without_cross_state_destructive_transfer():
    source = '''a = []
b = []
FUNCTION add(x):
    a.append(x)
    b.append(x)
FUNCTION take():
    IF a is not empty:
        RETURN a.pop()
    RETURN b.pop()
'''
    result = _process(source)
    assert not any(item.rule == "GC218" for item in result.transformations)


def test_gc218_refuses_unknown_call_escape():
    source = source_f_ALGORITHM_40.replace(
        "    s1.push(x)",
        "    inspect(s1)\n    s1.push(x)",
    )
    result = _process(source)
    assert not any(item.rule == "GC218" for item in result.transformations)


def test_gc218_refuses_direct_state_rebinding_or_indexed_write():
    rebinding = _process(source_f_ALGORITHM_40.replace(
        "    s1.push(x)",
        "    s1 = []\n    s1.push(x)",
    ))
    assert not any(item.rule == "GC218" for item in rebinding.transformations)

    indexed = _process(source_f_ALGORITHM_40.replace(
        "    s1.push(x)",
        "    s1[0] = x\n    s1.push(x)",
    ))
    assert not any(item.rule == "GC218" for item in indexed.transformations)


def test_gc218_refuses_parameter_shadowing_state():
    result = _process(source_f_ALGORITHM_40.replace("FUNCTION enqueue(x):", "FUNCTION enqueue(s1):"))
    assert not any(item.rule == "GC218" for item in result.transformations)


def test_gc218_refuses_unrelated_non_list_initial_state():
    source = source_f_ALGORITHM_40.replace("s2 = []", "s2 = []\ncount = 0")
    result = _process(source)
    assert not any(item.rule == "GC218" for item in result.transformations)


def test_gc218_does_not_take_over_source_f37_counted_list_shape():
    source = '''INIT stack = []
size = 0
FUNCTION push(x):
    stack.append(x)
    size++
FUNCTION pop():
    IF size > 0:
        size--
        RETURN stack.pop()
    ELSE:
        ERROR
FUNCTION peek():
    IF size > 0:
        RETURN stack[size-1]
    ELSE:
        ERROR
'''
    result = _process(source)
    rules = [item.rule for item in result.transformations]
    assert "GC216" in rules
    assert "GC218" not in rules


def test_source_f40_randomised_behaviour_matches_reference_fifo_and_preserves_underflow():
    result = _process(source_f_ALGORITHM_40)
    python_source = _compile(result.processed_source)
    namespace = {}
    exec(python_source, namespace)
    Queue = namespace["unnamed_class"]

    rng = random.Random(24038155)
    for _ in range(100):
        actual = Queue()
        reference = []
        for _ in range(50):
            if not reference or rng.random() < 0.62:
                value = rng.randrange(10000)
                actual.enqueue(value)
                reference.append(value)
            else:
                assert actual.dequeue() == reference.pop(0)

            actual_fifo = list(reversed(actual.s2)) + actual.s1
            assert actual_fifo == reference

        while reference:
            assert actual.dequeue() == reference.pop(0)
        with pytest.raises(IndexError):
            actual.dequeue()
