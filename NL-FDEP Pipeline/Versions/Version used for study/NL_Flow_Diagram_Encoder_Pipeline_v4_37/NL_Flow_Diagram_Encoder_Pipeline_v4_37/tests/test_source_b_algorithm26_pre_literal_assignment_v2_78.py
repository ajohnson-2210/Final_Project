import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_b_ALGORITHM_26 = '''FUNCTION levelOrder(root):
    IF root is NULL THEN RETURN []
    queue ← [root], result ← []
    WHILE queue is not empty:
        level ← [], nextQueue ← []
        FOR each node IN queue:
            APPEND node.value TO level
            IF node.left ≠ NULL THEN APPEND node.left TO nextQueue
            IF node.right ≠ NULL THEN APPEND node.right TO nextQueue
        APPEND level TO result
        queue ← nextQueue
    RETURN result
'''


class source_bAlgorithm26PreLiteralAssignmentTests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()
        self.parser = AJParserFacade()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_exact_study_case_parses_after_existing_gc078_runs_before_gc094(self):
        result = self.process(source_b_ALGORITHM_26)

        gc078 = [t for t in result.transformations if t.rule == "GC078"]
        self.assertTrue(any(
            t.source.strip() == "queue <- [root], result <- []"
            and "queue <- [root]" in t.target
            and "result <- []" in t.target
            for t in gc078
        ))

        gc094 = [t for t in result.transformations if t.rule == "GC094"]
        self.assertTrue(any(
            t.source.strip() == "queue <- [root]"
            and t.target.strip() == "queue <- LIST [root]"
            for t in gc094
        ))

        # Existing downstream GC157 represents the already-canonical LIST literal
        # as the compatibility helper call.  v2.78 does not alter that rule.
        self.assertIn("queue <- CALL list_value(root)", result.processed_source)
        self.assertNotIn("queue <- [root]", result.processed_source)

        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        self.assertIn("queue = [root]", compiled.source_code)
        self.assertIn("result = []", compiled.source_code)
        self.assertIn("for node in queue:", compiled.source_code)
        self.assertIn("nextQueue.append(node.left)", compiled.source_code)
        self.assertIn("nextQueue.append(node.right)", compiled.source_code)
        self.assertIn("result.append(level)", compiled.source_code)

    def test_pre_literal_split_exposes_non_empty_and_empty_list_rhs(self):
        source = '''FUNCTION f(a, b):
    queue <- [a, b], result <- []
    RETURN queue
'''
        result = self.process(source)
        self.assertTrue(any(
            t.rule == "GC078"
            and t.source.strip() == "queue <- [a, b], result <- []"
            for t in result.transformations
        ))
        self.assertTrue(any(
            t.rule == "GC094"
            and t.source.strip() == "queue <- [a, b]"
            for t in result.transformations
        ))
        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_commas_nested_in_calls_lists_parentheses_braces_and_strings_do_not_split(self):
        helper = self.processor.generic_processor._split_explicit_multiple_assignments_before_literals
        cases = [
            '    x <- CALL f(a, b)',
            '    x <- [a, b, c]',
            '    x <- (a, b)',
            '    x <- {a, b}',
            '    x <- STRING("hello, world")',
        ]
        for source in cases:
            with self.subTest(source=source):
                transformed, transformations = helper(source)
                self.assertEqual(source, transformed)
                self.assertEqual([], transformations)

    def test_mixed_assignment_and_non_assignment_segments_do_not_split(self):
        helper = self.processor.generic_processor._split_explicit_multiple_assignments_before_literals
        source = "    x <- 1, y + 2"
        transformed, transformations = helper(source)
        self.assertEqual(source, transformed)
        self.assertEqual([], transformations)

    def test_two_explicit_top_level_assignments_split_without_literal_dependency(self):
        helper = self.processor.generic_processor._split_explicit_multiple_assignments_before_literals
        source = "    x <- 1, y <- 2"
        transformed, transformations = helper(source)
        self.assertEqual("    x <- 1\n    y <- 2", transformed)
        self.assertEqual(1, len(transformations))
        self.assertEqual("GC078", transformations[0].rule)


if __name__ == "__main__":
    unittest.main()
