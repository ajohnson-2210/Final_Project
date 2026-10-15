import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_b_ALGORITHM_28 = '''FUNCTION slidingWindowMax(arr, k):
    result ← []
    deque ← []   // stores indices
    FOR i FROM 0 TO length(arr) - 1:
        WHILE deque not empty AND deque.front < i - k + 1:
            REMOVE front of deque
        WHILE deque not empty AND arr[deque.back] < arr[i]:
            REMOVE back of deque
        APPEND i TO back of deque
        IF i >= k - 1 THEN APPEND arr[deque.front] TO result
    RETURN result
'''


class source_bAlgorithm28GeneralDequeTests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()
        self.parser = AJParserFacade()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def compile_aj(self, source):
        parsed = self.parser.parse(source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        return compiled.source_code

    def test_exact_study_case_uses_general_list_backed_deque_recovery(self):
        result = self.process(source_b_ALGORITHM_28)

        self.assertIn("LENGTH OF deque > 0", result.processed_source)
        self.assertIn("deque[0]", result.processed_source)
        self.assertIn("deque[-1]", result.processed_source)
        self.assertIn("REMOVE FIRST ITEM FROM deque", result.processed_source)
        self.assertIn("REMOVE LAST ITEM FROM deque", result.processed_source)
        self.assertIn("APPEND i TO deque", result.processed_source)
        self.assertNotIn("deque.front", result.processed_source)
        self.assertNotIn("deque.back", result.processed_source)

        gc136 = [t for t in result.transformations if t.rule == "GC136"]
        self.assertTrue(gc136)

        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        self.assertIn("deque.pop(0)", compiled.source_code)
        self.assertIn("deque.pop()", compiled.source_code)
        self.assertIn("deque.append(i)", compiled.source_code)
        self.assertIn("arr[deque[(-1)]]", compiled.source_code)
        self.assertIn("result.append(arr[deque[0]])", compiled.source_code)

    def test_gc136_does_not_require_sliding_window_names(self):
        source = '''FUNCTION consume ACCEPTS(items)
    deque <- EMPTY LIST
    APPEND 3 TO back of deque
    IF deque not empty THEN
        value <- deque.back
        REMOVE back of deque
    ENDIF
    RETURN value
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn("APPEND 3 TO deque", result.processed_source)
        self.assertIn("LENGTH OF deque > 0", result.processed_source)
        self.assertIn("value <- deque[-1]", result.processed_source)
        self.assertIn("REMOVE LAST ITEM FROM deque", result.processed_source)
        self.assertTrue(any(t.rule == "GC136" for t in result.transformations))
        parsed = self.parser.parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("Identifier 'value' is read before declaration or assignment", parsed.error)

    def test_gc136_requires_explicit_list_backing(self):
        source = '''FUNCTION inspect ACCEPTS(deque)
    IF deque not empty THEN
        RETURN deque.back
    ENDIF
    RETURN 0
ENDFUNCTION
'''
        result = self.process(source)
        rules = [t.rule for t in result.transformations]
        self.assertNotIn("GC136", rules)
        # v3.10 GC211 handles only the generic omitted-IS empty predicate.
        self.assertIn("GC211", rules)
        self.assertIn("LENGTH OF deque > 0", result.processed_source)
        # Without explicit list/deque backing, deque-specific member recovery
        # remains outside GC136 and therefore untouched.
        self.assertIn("deque.back", result.processed_source)

    def test_existing_flattened_deque_spellings_remain_supported(self):
        source = '''FUNCTION f ACCEPTS(value)
    deque <- EMPTY LIST
    APPEND value TO back of deque
    IF deque not empty THEN
        front <- deque_front
        back <- deque_back
    ENDIF
    RETURN back
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn("front <- deque[0]", result.processed_source)
        self.assertIn("back <- deque[-1]", result.processed_source)
        parsed = self.parser.parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("Identifier 'back' is read before declaration or assignment", parsed.error)

    def test_negative_and_length_minus_one_index_forms_both_parse_and_compile(self):
        short_source = '''FUNCTION getBack ACCEPTS(deque)
    RETURN deque[-1]
ENDFUNCTION
'''
        explicit_source = '''FUNCTION getBack ACCEPTS(deque)
    RETURN deque[LENGTH OF deque - 1]
ENDFUNCTION
'''
        short_python = self.compile_aj(short_source)
        explicit_python = self.compile_aj(explicit_source)
        self.assertIn("return deque[(-1)]", short_python)
        self.assertIn("return deque[(len(deque) - 1)]", explicit_python)

    def test_nested_index_forms_are_behaviourally_equivalent(self):
        short_source = '''FUNCTION getValue ACCEPTS(arr, deque)
    RETURN arr[deque[-1]]
ENDFUNCTION
'''
        explicit_source = '''FUNCTION getValue ACCEPTS(arr, deque)
    RETURN arr[deque[LENGTH OF deque - 1]]
ENDFUNCTION
'''
        short_python = self.compile_aj(short_source)
        explicit_python = self.compile_aj(explicit_source)

        short_ns = {}
        explicit_ns = {}
        exec(short_python, short_ns)
        exec(explicit_python, explicit_ns)
        arr = [10, 20, 30, 40]
        deque = [1, 3]
        self.assertEqual(40, short_ns["getValue"](arr, deque))
        self.assertEqual(40, explicit_ns["getValue"](arr, deque))
        self.assertEqual(
            short_ns["getValue"](arr, deque),
            explicit_ns["getValue"](arr, deque),
        )


if __name__ == "__main__":
    unittest.main()
