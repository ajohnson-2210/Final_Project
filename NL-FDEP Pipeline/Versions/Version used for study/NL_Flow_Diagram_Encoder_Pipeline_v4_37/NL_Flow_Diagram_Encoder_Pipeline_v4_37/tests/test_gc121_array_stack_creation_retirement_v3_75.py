import unittest

from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC121ArrayStackCreationRetirementV375Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def _process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_create_stack_does_not_invent_empty_list_backing(self):
        source = '''CREATE Stack
Top <- -1

PUSH(Item)
    Top <- Top + 1
    Stack[Top] <- Item

POP()
    IF Top == -1 THEN
        OUTPUT STRING("Stack Empty")
    ELSE
        Item <- Stack[Top]
        Top <- Top - 1
        OUTPUT Item
    ENDIF

PEEK()
    IF Top != -1 THEN
        OUTPUT Stack[Top]
    ENDIF
'''
        result = self._process(source)
        self.assertIn('CREATE Stack', result.processed_source)
        self.assertNotIn('Stack <- EMPTY LIST', result.processed_source)
        self.assertIn('FUNCTION PUSH ACCEPTS(Item)', result.processed_source)
        self.assertIn('Stack[Top] <- Item', result.processed_source)
        self.assertNotIn('APPEND Item TO Stack', result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIsNone(parsed.ast)

    def test_array_stack_remains_expected_failure_before_python_generation(self):
        source = '''BEGIN
    CREATE Stack
    Top <- -1

    PUSH(Item)
        Top <- Top + 1
        Stack[Top] <- Item

    POP()
        IF Top == -1 THEN
            OUTPUT "Stack Empty"
        ELSE
            Item <- Stack[Top]
            Top <- Top - 1
            OUTPUT Item
        ENDIF

    PEEK()
        IF Top != -1 THEN
            OUTPUT Stack[Top]
        ENDIF
END
'''
        result = self._process(source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIsNone(parsed.ast)
        self.assertNotIn('EMPTY LIST', result.processed_source)

    def test_explicit_list_backing_is_not_reinterpreted_by_gc121(self):
        source = '''FUNCTION push_one ACCEPTS(Item)
    Stack <- EMPTY LIST
    APPEND Item TO Stack
    RETURN Stack
ENDFUNCTION
'''
        result = self._process(source)
        self.assertIn('Stack <- EMPTY LIST', result.processed_source)
        self.assertIn('APPEND Item TO Stack', result.processed_source)
        self.assertTrue(AJParserFacade().parse(result.processed_source).success)


if __name__ == '__main__':
    unittest.main()
