import unittest

from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GenericLiteralDeclarationPhase8Tests(unittest.TestCase):

    def setUp(self):
        self.processor = PseudocodeProfileProcessor()
        self.parser = AJParserFacade()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_empty_list_and_raw_string_are_canonicalised(self):
        result = self.process('FUNCTION f()\n    values = []\n    text = ""\n    RETURN values\nEND FUNCTION')
        self.assertIn('values <- EMPTY LIST', result.processed_source)
        self.assertIn('text <- EMPTY STRING', result.processed_source)
        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_create_map_becomes_empty_dictionary(self):
        result = self.process('FUNCTION f()\n    CREATE map counts\n    RETURN counts\nEND FUNCTION')
        self.assertIn('counts <- EMPTY DICTIONARY', result.processed_source)
        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_non_empty_list_assignment_becomes_aj_list_literal(self):
        result = self.process('FUNCTION f()\n    values = [1, 2, 3]\n    RETURN values\nEND FUNCTION')
        self.assertIn('values <- CALL list_value(1, 2, 3)', result.processed_source)
        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_annotated_input_is_recovered(self):
        result = self.process('INPUT matrix (N x N) RETURN matrix')
        self.assertIn('FUNCTION unnamed_function ACCEPTS(matrix)', result.processed_source)

    def test_general_profile_remains_unchanged(self):
        source = 'values = []'
        result = self.processor.process(source, PseudocodeProfile.GENERAL_NO_CONVERSION)
        self.assertEqual(source, result.processed_source)


if __name__ == '__main__':
    unittest.main()
