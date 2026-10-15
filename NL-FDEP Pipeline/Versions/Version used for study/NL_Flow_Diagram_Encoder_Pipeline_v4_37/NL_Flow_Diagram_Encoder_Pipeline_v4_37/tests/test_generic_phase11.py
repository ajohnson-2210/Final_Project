import unittest
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor
from aj_parser import AJParserFacade

class TestGenericPhase11(unittest.TestCase):
    def setUp(self):
        self.processor=PseudocodeProfileProcessor()
        self.parser=AJParserFacade()

    def test_structured_multiline_skips_compressed_reconstruction(self):
        src='''INPUT a, b\n\nIF a == b:\n    RETURN TRUE\nELSE:\n    RETURN FALSE\n'''
        result=self.processor.process(src,PseudocodeProfile.GENERIC_COMPATIBILITY)
        self.assertFalse(any(t.rule == 'GC085' for t in result.transformations))

    def test_visual_separator_is_removed(self):
        src='''INPUT n\nRETURN n\n________________________________________\n'''
        result=self.processor.process(src,PseudocodeProfile.GENERIC_COMPATIBILITY)
        self.assertNotIn('____', result.processed_source)
        self.assertTrue(self.parser.parse(result.processed_source).success)

if __name__ == '__main__':
    unittest.main()
