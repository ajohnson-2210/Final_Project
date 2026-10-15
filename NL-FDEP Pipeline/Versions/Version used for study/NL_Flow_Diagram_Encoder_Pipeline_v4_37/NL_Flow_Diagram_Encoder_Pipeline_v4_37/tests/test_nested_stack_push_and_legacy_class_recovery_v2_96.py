import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class NestedStackPushAndLegacyClassRecoveryV296Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_balanced_nested_push_requires_explicit_stack_backing_evidence(self):
        source = '''FUNCTION transfer ACCEPTS()
    source <- empty stack
    destination <- empty stack
    destination.push(source.pop())
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn("CALL PUSH(CALL POP(source), destination)", result.processed_source)
        self.assertIn("GC202", [item.rule for item in result.transformations])

    def test_balanced_nested_push_without_collection_evidence_is_not_reclassified(self):
        source = '''FUNCTION relay ACCEPTS(source, destination)
    destination.push(source.pop())
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn("destination.push(source.pop())", result.processed_source)
        self.assertNotIn("GC202", [item.rule for item in result.transformations])

    def test_simple_push_remains_on_existing_gc037_path(self):
        source = '''FUNCTION addOne ACCEPTS()
    values <- empty stack
    values.push(7)
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn("CALL PUSH(7, values)", result.processed_source)
        rules = [item.rule for item in result.transformations]
        self.assertIn("GC037", rules)
        self.assertNotIn("GC202", rules)

    def test_generic_explicit_stateful_class_becomes_frozen_aj_class_grammar(self):
        source = '''CLASS TwinStore:
    left = empty stack
    right = empty stack

    FUNCTION add(value):
        left.push(value)

    FUNCTION move():
        right.push(left.pop())

    FUNCTION take():
        RETURN right.pop()
'''
        result = self.process(source)
        self.assertIn("CLASS TwinStore", result.processed_source)
        self.assertIn("PROPERTY left", result.processed_source)
        self.assertIn("PROPERTY right", result.processed_source)
        self.assertNotIn("PROPERTY left AS LIST", result.processed_source)
        self.assertNotIn("PROPERTY right AS LIST", result.processed_source)
        self.assertIn("CONSTRUCTOR ACCEPTS()", result.processed_source)
        self.assertIn("PROPERTY THIS.left <- CALL create_stack()", result.processed_source)
        self.assertIn("PROPERTY THIS.right <- CALL create_stack()", result.processed_source)
        self.assertIn("METHOD add ACCEPTS(value)", result.processed_source)
        self.assertIn("CALL PUSH(CALL POP(THIS.left), THIS.right)", result.processed_source)
        self.assertTrue(result.processed_source.rstrip().endswith("ENDCLASS"))
        rules = [item.rule for item in result.transformations]
        self.assertIn("GC202", rules)
        self.assertIn("GC203", rules)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        namespace = {}
        exec(compiled.source_code, namespace)
        store = namespace["TwinStore"]()
        store.add("x")
        store.move()
        self.assertEqual("x", store.take())

    def test_existing_endclass_is_canonicalised_without_duplication(self):
        source = '''CLASS Counter:
    count = 0
    FUNCTION increment():
        count = count + 1
    FUNCTION value():
        RETURN count
ENDCLASS
'''
        result = self.process(source)
        self.assertEqual(1, result.processed_source.upper().split().count("ENDCLASS"))
        self.assertIn("PROPERTY count", result.processed_source)
        self.assertIn("PROPERTY THIS.count <- 0", result.processed_source)
        self.assertIn("THIS.count <- THIS.count + 1", result.processed_source)
        self.assertIn("RETURN THIS.count", result.processed_source)
        self.assertIn("GC203", [item.rule for item in result.transformations])

    def test_indexed_write_to_empty_list_state_preserves_array_growth_boundary(self):
        source = '''CLASS SlotStore:
    data = empty list
    index = 0
    FUNCTION store(value):
        data[index] = value
ENDCLASS
'''
        result = self.process(source)
        self.assertNotIn("GC203", [item.rule for item in result.transformations])
        self.assertNotIn("PROPERTY data AS LIST", result.processed_source)
        self.assertIn("data[index] <- value", result.processed_source)

    def test_external_initializer_is_not_invented_into_constructor_state(self):
        source = '''CLASS CapacityHolder:
    capacity = given capacity
    FUNCTION current():
        RETURN capacity
ENDCLASS
'''
        result = self.process(source)
        self.assertNotIn("GC203", [item.rule for item in result.transformations])
        self.assertNotIn("PROPERTY capacity", result.processed_source)


if __name__ == "__main__":
    unittest.main()
