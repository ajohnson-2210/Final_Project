import unittest

from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GenericRecoveryPhase6Tests(unittest.TestCase):

    def setUp(self):
        self.processor = PseudocodeProfileProcessor()
        self.parser = AJParserFacade()

    def test_recovery_normalises_inputs_booleans_and_missing_closers(self):
        source = """FUNCTION check(items):
    INPUT value
    FOR EACH char IN items:
        IF char == value:
            RETURN True
    RETURN False
"""
        result = self.processor.process(
            source,
            PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        self.assertIn('value <- INPUT(STRING("Enter value"))', result.processed_source)
        self.assertIn('FOR EACH __reserved_keyword__char IN items DO', result.processed_source)
        self.assertIn('RETURN BOOLEAN(True)', result.processed_source)
        self.assertIn('RETURN BOOLEAN(False)', result.processed_source)
        self.assertIn('ENDIF', result.processed_source)
        self.assertIn('ENDFOR', result.processed_source)
        self.assertIn('ENDFUNCTION', result.processed_source)
        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_general_profile_does_not_apply_recovery_rules(self):
        source = "INPUT value\nRETURN True"
        result = self.processor.process(
            source,
            PseudocodeProfile.GENERAL_NO_CONVERSION,
        )
        self.assertEqual(source, result.processed_source)
        self.assertEqual(0, result.transformation_count)


if __name__ == "__main__":
    unittest.main()
