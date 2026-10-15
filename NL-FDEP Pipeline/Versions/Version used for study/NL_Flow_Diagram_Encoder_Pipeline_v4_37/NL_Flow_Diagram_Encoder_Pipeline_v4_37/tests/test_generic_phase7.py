import unittest

from aj_parser import AJParserFacade
from pseudocode_profiles import (
    GenericStatementBoundaryNormaliser,
    PseudocodeProfile,
    PseudocodeProfileProcessor,
)


class GenericStatementBoundaryPhase7Tests(unittest.TestCase):

    def setUp(self):
        self.boundary = GenericStatementBoundaryNormaliser()
        self.processor = PseudocodeProfileProcessor()
        self.parser = AJParserFacade()

    def test_reconstructs_compressed_gcd_program(self):
        source = "INPUT a, b WHILE b != 0: temp = b b = a MOD b a = temp RETURN a"
        result = self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)
        self.assertIn('FUNCTION unnamed_function ACCEPTS(a, b)', result.processed_source)
        self.assertIn('WHILE b != 0 DO', result.processed_source)
        self.assertIn('temp <- b', result.processed_source)
        self.assertIn('b <- a MODULUS b', result.processed_source)
        self.assertIn('ENDWHILE', result.processed_source)
        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_does_not_split_comparison_equals(self):
        source = 'INPUT n IF n == 0 RETURN "0" binary = "" RETURN binary'
        reconstructed, transformations = self.boundary.process(source)
        self.assertIn('IF n == 0', reconstructed)
        self.assertNotIn('IF\nn == 0', reconstructed)

    def test_general_profile_remains_unchanged(self):
        source = 'INPUT a, b WHILE b != 0: temp = b RETURN a'
        result = self.processor.process(source, PseudocodeProfile.GENERAL_NO_CONVERSION)
        self.assertEqual(source, result.processed_source)
        self.assertEqual(0, result.transformation_count)


if __name__ == '__main__':
    unittest.main()
