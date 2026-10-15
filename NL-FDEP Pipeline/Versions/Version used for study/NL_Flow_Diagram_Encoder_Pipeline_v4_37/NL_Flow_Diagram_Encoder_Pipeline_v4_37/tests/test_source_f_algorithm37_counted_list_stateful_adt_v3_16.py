import random

import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_f_ALGORITHM_37 = '''INIT stack = []
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


def test_source_f37_recovers_counted_list_outer_state_as_neutral_class():
    result = _process(source_f_ALGORITHM_37)

    assert "CLASS unnamed_class" in result.processed_source
    assert "PROPERTY stack AS LIST" in result.processed_source
    assert "PROPERTY size AS INTEGER" in result.processed_source
    assert "CONSTRUCTOR ACCEPTS()" in result.processed_source
    assert "PROPERTY THIS.stack <- EMPTY LIST" in result.processed_source
    assert "PROPERTY THIS.size <- 0" in result.processed_source
    assert "METHOD push ACCEPTS(x)" in result.processed_source
    assert "METHOD pop ACCEPTS()" in result.processed_source
    assert "METHOD peek ACCEPTS()" in result.processed_source
    assert "APPEND x TO THIS.stack" in result.processed_source
    assert "THIS.size <- THIS.size + 1" in result.processed_source
    assert "THIS.size <- THIS.size - 1" in result.processed_source
    assert "RETURN THIS.stack.pop()" in result.processed_source
    assert "RETURN THIS.stack[THIS.size-1]" in result.processed_source
    assert result.processed_source.count('RAISE STRING("ERROR")') == 2

    assert [item.rule for item in result.transformations].count("GC216") == 1
    assert [item.rule for item in result.transformations].count("GC217") == 2

    python_source = _compile(result.processed_source)
    assert "class unnamed_class:" in python_source
    assert "def __init__(self):" in python_source
    assert "self.stack = []" in python_source
    assert "self.size = 0" in python_source
    assert "raise Exception('ERROR')" in python_source

    namespace = {}
    exec(python_source, namespace)
    Stack = namespace["unnamed_class"]
    stack = Stack()
    stack.push("a")
    stack.push("b")
    assert stack.peek() == "b"
    assert stack.pop() == "b"
    assert stack.pop() == "a"
    assert stack.size == 0
    assert stack.stack == []
    with pytest.raises(Exception, match="ERROR"):
        stack.pop()
    with pytest.raises(Exception, match="ERROR"):
        stack.peek()


def test_gc216_is_not_hardcoded_to_stack_size_or_operation_names():
    source = '''INIT items = []
count = 0
FUNCTION add(value):
    items.append(value)
    count++
FUNCTION take():
    IF count > 0:
        count--
        RETURN items.pop()
    ELSE:
        ERROR
FUNCTION top():
    IF count > 0:
        RETURN items[count-1]
    ELSE:
        ERROR
'''
    result = _process(source)
    assert "PROPERTY items AS LIST" in result.processed_source
    assert "PROPERTY count AS INTEGER" in result.processed_source
    assert "METHOD add ACCEPTS(value)" in result.processed_source
    assert "METHOD take ACCEPTS()" in result.processed_source
    assert "METHOD top ACCEPTS()" in result.processed_source
    assert any(item.rule == "GC216" for item in result.transformations)


def test_gc216_audit_reports_source_proven_structural_recovery():
    result = _process(source_f_ALGORITHM_37)
    entries = [
        item for item in result.to_dict()["transformations"]
        if item["branch"] == "EVIDENCED_COUNTED_LIST_CONSTRUCTOR"
    ]
    assert len(entries) == 1
    assert entries[0]["rule_family"] == "STATEFUL_ADT_STRUCTURE"
    assert entries[0]["confidence"] == "source_proven"
    assert entries[0]["semantic_change"] is False


def test_gc217_audit_reports_explicit_error_signal_recovery():
    result = _process(source_f_ALGORITHM_37)
    entries = [
        item for item in result.to_dict()["transformations"]
        if item["branch"] == "STANDALONE_ERROR_RAISE"
    ]
    assert len(entries) == 2
    assert all(item["rule_family"] == "ERROR_SIGNAL" for item in entries)
    assert all(item["semantic_change"] is False for item in entries)


def test_gc217_is_statement_position_only_and_preserves_existing_return_error_policy():
    source = '''FUNCTION check ACCEPTS(flag)
    IF flag THEN
        ERROR
    ELSE
        RETURN ERROR
    ENDIF
ENDFUNCTION
'''
    result = _process(source)
    assert 'RAISE STRING("ERROR")' in result.processed_source
    assert 'RETURN STRING("ERROR")' in result.processed_source
    rules = [item.rule for item in result.transformations]
    assert "GC217" in rules
    assert "GC204" in rules

    assignment = _process('''FUNCTION check ACCEPTS()\n    status <- ERROR\n    RETURN status\nENDFUNCTION\n''')
    assert "status <- ERROR" in assignment.processed_source
    assert not any(item.rule == "GC217" for item in assignment.transformations)


def test_gc216_refuses_only_two_operations():
    source = source_f_ALGORITHM_37.replace(
        '''\nFUNCTION peek():\n    IF size > 0:\n        RETURN stack[size-1]\n    ELSE:\n        ERROR\n''',
        "\n",
    )
    result = _process(source)
    assert not any(item.rule == "GC216" for item in result.transformations)


def test_gc216_refuses_operation_that_does_not_share_both_state_values():
    source = source_f_ALGORITHM_37.replace(
        "FUNCTION peek():\n    IF size > 0:\n        RETURN stack[size-1]",
        "FUNCTION peek():\n    RETURN stack[0]",
    )
    result = _process(source)
    assert not any(item.rule == "GC216" for item in result.transformations)


def test_gc216_refuses_unknown_call_escape():
    source = source_f_ALGORITHM_37.replace(
        "    stack.append(x)\n    size++",
        "    inspect(stack)\n    stack.append(x)\n    size++",
    )
    result = _process(source)
    assert not any(item.rule == "GC216" for item in result.transformations)


def test_gc216_refuses_direct_list_rebinding():
    source = source_f_ALGORITHM_37.replace(
        "    stack.append(x)\n    size++",
        "    stack = []\n    stack.append(x)\n    size++",
    )
    result = _process(source)
    assert not any(item.rule == "GC216" for item in result.transformations)


def test_gc216_refuses_non_zero_counter_initialisation():
    result = _process(source_f_ALGORITHM_37.replace("size = 0", "size = 1"))
    assert not any(item.rule == "GC216" for item in result.transformations)


def test_gc216_refuses_missing_pop_or_indexed_top_evidence():
    no_pop = _process(source_f_ALGORITHM_37.replace("RETURN stack.pop()", "RETURN stack[0]"))
    assert not any(item.rule == "GC216" for item in no_pop.transformations)

    no_top = _process(source_f_ALGORITHM_37.replace("RETURN stack[size-1]", "RETURN stack[0]"))
    assert not any(item.rule == "GC216" for item in no_top.transformations)


def test_source_f37_randomised_behaviour_matches_reference_stack():
    result = _process(source_f_ALGORITHM_37)
    python_source = _compile(result.processed_source)
    namespace = {}
    exec(python_source, namespace)
    Stack = namespace["unnamed_class"]

    rng = random.Random(24038155)
    for _ in range(100):
        actual = Stack()
        reference = []
        for _ in range(50):
            roll = rng.random()
            if roll < 0.5:
                value = rng.randrange(1000)
                actual.push(value)
                reference.append(value)
            elif roll < 0.77:
                if reference:
                    assert actual.pop() == reference.pop()
                else:
                    with pytest.raises(Exception, match="ERROR"):
                        actual.pop()
            else:
                if reference:
                    assert actual.peek() == reference[-1]
                else:
                    with pytest.raises(Exception, match="ERROR"):
                        actual.peek()

            assert actual.stack == reference
            assert actual.size == len(reference)
