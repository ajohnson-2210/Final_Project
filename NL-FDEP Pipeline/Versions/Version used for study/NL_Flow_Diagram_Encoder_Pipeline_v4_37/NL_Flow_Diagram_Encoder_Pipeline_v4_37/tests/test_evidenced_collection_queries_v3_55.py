from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def rules(result):
    return [t.rule for t in result.transformations]


def test_gc045_to_gc048_refuse_unproven_receivers():
    source = """FUNCTION inspect ACCEPTS(obj)
    a <- obj.size()
    b <- obj.front()
    c <- obj.back()
    d <- obj.isEmpty()
    RETURN a
ENDFUNCTION
"""
    result = process(source)
    assert "obj.size()" in result.processed_source
    assert "obj.front()" in result.processed_source
    assert "obj.back()" in result.processed_source
    assert "obj.isEmpty()" in result.processed_source
    assert not ({"GC045", "GC046", "GC047", "GC048"} & set(rules(result)))


def test_gc045_to_gc048_accept_explicit_list_evidence():
    source = """FUNCTION inspect ACCEPTS()
    items <- EMPTY LIST
    a <- items.size()
    b <- items.front()
    c <- items.back()
    d <- items.isEmpty()
    RETURN a
ENDFUNCTION
"""
    result = process(source)
    assert "a <- LENGTH OF items" in result.processed_source
    assert "b <- items[0]" in result.processed_source
    assert "c <- items[-1]" in result.processed_source
    assert "d <- LENGTH OF items == 0" in result.processed_source
    assert {"GC045", "GC046", "GC047", "GC048"}.issubset(set(rules(result)))


def test_query_capabilities_remain_kind_specific():
    source = """FUNCTION inspect ACCEPTS()
    queue <- EMPTY QUEUE
    stack <- EMPTY STACK
    a <- queue.front()
    b <- queue.back()
    c <- stack.front()
    d <- stack.back()
    RETURN a
ENDFUNCTION
"""
    result = process(source)
    assert "a <- queue[0]" in result.processed_source
    assert "queue.back()" in result.processed_source
    assert "stack.front()" in result.processed_source
    assert "d <- stack[-1]" in result.processed_source


def test_constructor_member_collection_evidence_is_readable_by_sibling_methods():
    source = """CLASS Holder
    CONSTRUCTOR ACCEPTS()
        self.items <- Stack()
    ENDCONSTRUCTOR
    METHOD Empty ACCEPTS()
        RETURN self.items.isEmpty()
    ENDMETHOD
ENDCLASS
"""
    result = process(source)
    assert "RETURN LENGTH OF self.items == 0" in result.processed_source
    assert "GC048" in rules(result)


def test_constructor_this_member_collection_evidence_is_readable_by_sibling_methods():
    source = """CLASS Holder
    CONSTRUCTOR ACCEPTS()
        THIS.items <- EMPTY LIST
    ENDCONSTRUCTOR
    METHOD First ACCEPTS()
        RETURN THIS.items.front()
    ENDMETHOD
ENDCLASS
"""
    result = process(source)
    assert "RETURN THIS.items[0]" in result.processed_source
    assert "GC046" in rules(result)


def test_constructor_local_collection_evidence_is_not_promoted_to_class_scope():
    source = """CLASS Holder
    CONSTRUCTOR ACCEPTS()
        items <- Stack()
    ENDCONSTRUCTOR
    METHOD Empty ACCEPTS()
        RETURN items.isEmpty()
    ENDMETHOD
ENDCLASS
"""
    result = process(source)
    assert "RETURN items.isEmpty()" in result.processed_source
    assert "GC048" not in rules(result)


def test_method_local_rebind_invalidates_inherited_member_evidence_only_in_that_method():
    source = """CLASS Holder
    CONSTRUCTOR ACCEPTS()
        self.items <- Stack()
    ENDCONSTRUCTOR
    METHOD Rebound ACCEPTS(replacement)
        self.items <- replacement
        RETURN self.items.isEmpty()
    ENDMETHOD
    METHOD StillStack ACCEPTS()
        RETURN self.items.isEmpty()
    ENDMETHOD
ENDCLASS
"""
    result = process(source)
    lines = result.processed_source.splitlines()
    assert "        RETURN self.items.isEmpty()" in lines
    assert "        RETURN LENGTH OF self.items == 0" in lines
    assert rules(result).count("GC048") == 1


def test_constructor_member_evidence_does_not_leak_to_another_class():
    source = """CLASS First
    CONSTRUCTOR ACCEPTS()
        self.items <- Stack()
    ENDCONSTRUCTOR
ENDCLASS
CLASS Second
    METHOD Empty ACCEPTS()
        RETURN self.items.isEmpty()
    ENDMETHOD
ENDCLASS
"""
    result = process(source)
    assert "RETURN self.items.isEmpty()" in result.processed_source
    assert "GC048" not in rules(result)


def test_later_constructor_does_not_forward_prove_earlier_method():
    source = """CLASS Holder
    METHOD Empty ACCEPTS()
        RETURN self.items.isEmpty()
    ENDMETHOD
    CONSTRUCTOR ACCEPTS()
        self.items <- Stack()
    ENDCONSTRUCTOR
ENDCLASS
"""
    result = process(source)
    assert "RETURN self.items.isEmpty()" in result.processed_source
    assert "GC048" not in rules(result)
