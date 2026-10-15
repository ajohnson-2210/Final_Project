import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC160AbstractStackPreservationV380Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source: str):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_explicit_empty_stack_preserves_stack_abstraction(self):
        source = '''FUNCTION operate ACCEPTS(value)
    stack <- empty stack
    stack.push(value)
    RETURN stack.pop()
ENDFUNCTION
'''
        result = self.process(source)
        canonical = result.processed_source
        self.assertIn('stack <- CALL create_stack()', canonical)
        self.assertIn('CALL PUSH(value, stack)', canonical)
        self.assertIn('RETURN CALL POP(stack)', canonical)
        self.assertNotIn('stack <- EMPTY LIST', canonical)
        self.assertNotIn('APPEND value TO stack', canonical)

        parsed = AJParserFacade().parse(canonical)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        namespace = {}
        exec(compiled.source_code, namespace)
        self.assertEqual(value := 17, namespace['operate'](value))
        self.assertIn('stack = []', compiled.source_code)
        self.assertIn('stack.append(value)', compiled.source_code)
        self.assertIn('return stack.pop(-1)', compiled.source_code)

    def test_explicit_stack_empty_predicates_remain_abstract(self):
        source = '''FUNCTION drain ACCEPTS()
    source <- EMPTY STACK
    destination <- EMPTY STACK
    WHILE source IS NOT empty DO
        destination.push(source.pop())
    ENDWHILE
    IF destination IS empty THEN
        RETURN NONE
    ENDIF
    RETURN destination.pop()
ENDFUNCTION
'''
        result = self.process(source)
        canonical = result.processed_source
        self.assertIn('WHILE NOT CALL stack_is_empty(source) DO', canonical)
        self.assertIn('IF CALL stack_is_empty(destination) THEN', canonical)
        self.assertIn('CALL PUSH(CALL POP(source), destination)', canonical)
        self.assertNotIn('LENGTH OF source', canonical)
        self.assertNotIn('LENGTH OF destination', canonical)

    def test_explicit_empty_list_remains_list_backed(self):
        source = '''FUNCTION add ACCEPTS(value)
    items <- EMPTY LIST
    PUSH value TO items
    RETURN items
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn('items <- EMPTY LIST', result.processed_source)
        self.assertIn('APPEND value TO items', result.processed_source)
        self.assertNotIn('CALL create_stack()', result.processed_source)

    def test_source_c_class_stack_properties_are_not_typed_as_lists(self):
        source = '''CLASS QueueUsingStacks:
    stack1 = empty stack (for enqueue)
    stack2 = empty stack (for dequeue)

    FUNCTION enqueue(item):
        stack1.push(item)

    FUNCTION dequeue():
        IF stack2 IS empty:
            WHILE stack1 IS NOT empty:
                stack2.push(stack1.pop())
        IF stack2 IS empty:
            RETURN NULL
        RETURN stack2.pop()
'''
        result = self.process(source)
        canonical = result.processed_source
        self.assertIn('PROPERTY stack1', canonical)
        self.assertIn('PROPERTY stack2', canonical)
        self.assertNotIn('PROPERTY stack1 AS LIST', canonical)
        self.assertNotIn('PROPERTY stack2 AS LIST', canonical)
        self.assertIn('PROPERTY THIS.stack1 <- CALL create_stack()', canonical)
        self.assertIn('PROPERTY THIS.stack2 <- CALL create_stack()', canonical)
        self.assertIn('CALL PUSH(item, THIS.stack1)', canonical)
        self.assertIn('CALL PUSH(CALL POP(THIS.stack1), THIS.stack2)', canonical)
        self.assertIn('IF CALL stack_is_empty(THIS.stack2) THEN', canonical)

        parsed = AJParserFacade().parse(canonical)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        namespace = {}
        exec(compiled.source_code, namespace)
        queue = namespace['QueueUsingStacks']()
        queue.enqueue('A')
        queue.enqueue('B')
        self.assertEqual('A', queue.dequeue())
        self.assertEqual('B', queue.dequeue())
        self.assertIsNone(queue.dequeue())


if __name__ == '__main__':
    unittest.main()
