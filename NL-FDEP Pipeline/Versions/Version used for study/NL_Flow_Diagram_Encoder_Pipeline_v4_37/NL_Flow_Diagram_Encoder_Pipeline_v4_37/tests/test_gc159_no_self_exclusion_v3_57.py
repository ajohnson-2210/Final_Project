import unittest

from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC159NoSelfExclusionV357Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_other_iterator_name_does_not_invent_self_exclusion(self):
        source = '''FUNCTION compare ACCEPTS(items)
    FOR EACH item IN items DO
        FOR EACH otherItem IN items DO
            OUTPUT otherItem
        ENDFOR
    ENDFOR
ENDFUNCTION
'''
        result = self.process(source)

        self.assertIn('OUTPUT otherItem', result.processed_source)
        self.assertNotIn('IF otherItem != item THEN', result.processed_source)
        self.assertFalse(any(t.rule == 'GC159' for t in result.transformations))

    def test_explicit_source_self_exclusion_is_preserved(self):
        source = '''FUNCTION compare ACCEPTS(items)
    FOR EACH item IN items DO
        FOR EACH otherItem IN items DO
            IF otherItem != item THEN
                OUTPUT otherItem
            ENDIF
        ENDFOR
    ENDFOR
ENDFUNCTION
'''
        result = self.process(source)

        self.assertEqual(result.processed_source.count('IF otherItem != item THEN'), 1)
        self.assertIn('OUTPUT otherItem', result.processed_source)

    def test_iterator_name_without_flattened_property_is_not_a_gc159_change(self):
        source = '''FUNCTION compare ACCEPTS(items)
    FOR EACH item IN items DO
        FOR EACH otherItem IN items DO
            OUTPUT otherItem
        ENDFOR
    ENDFOR
ENDFUNCTION
'''
        result = self.process(source)

        self.assertNotIn('IF otherItem != item THEN', result.processed_source)
        self.assertFalse(any(t.rule == 'GC159' for t in result.transformations))



if __name__ == '__main__':
    unittest.main()
