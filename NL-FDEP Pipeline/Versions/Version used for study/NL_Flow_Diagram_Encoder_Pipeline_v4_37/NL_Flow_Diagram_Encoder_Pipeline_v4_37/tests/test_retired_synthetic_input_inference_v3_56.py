import unittest

from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class RetiredSyntheticInputInferenceV356Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_two_list_intersection_preserves_external_inputs(self):
        source = '''FUNCTION demo ACCEPTS()
    INPUT List1
    INPUT List2
    FOR EACH x IN List1 DO
        IF x IN List2 THEN
            OUTPUT x
        ENDIF
    ENDFOR
ENDFUNCTION
'''
        result = self.process(source)
        self.assertNotIn('random_list', result.processed_source)
        self.assertIn('List1 <- INPUT(STRING("Enter List1"))', result.processed_source)
        self.assertIn('List2 <- INPUT(STRING("Enter List2"))', result.processed_source)
        self.assertFalse(any(t.rule == 'GC119' for t in result.transformations))

    def test_matrix_transpose_preserves_matrix_input(self):
        source = '''FUNCTION demo ACCEPTS()
    INPUT Matrix
    INPUT N
    Matrix <- CALL transpose(Matrix)
    OUTPUT Matrix
ENDFUNCTION
'''
        result = self.process(source)
        self.assertNotIn('random_matrix', result.processed_source)
        self.assertIn('Matrix <- INPUT(STRING("Enter Matrix"))', result.processed_source)
        self.assertIn('N <- INPUT(STRING("Enter N"))', result.processed_source)
        self.assertFalse(any(t.rule == 'GC118' and 'random_matrix' in t.target for t in result.transformations))

    def test_surface_transpose_recovery_remains_available(self):
        result = self.process('Matrix <- CALL matrix_value()\nTRANSPOSE Matrix\n')
        self.assertIn('CALL transpose_in_place(Matrix)', result.processed_source)
        self.assertNotIn('random_matrix', result.processed_source)

    def test_no_synthetic_input_intrinsics_are_introduced(self):
        source = '''FUNCTION demo ACCEPTS()
    INPUT Values
    INPUT Matrix
    INPUT N
    FOR EACH value IN Values DO
        OUTPUT value
    ENDFOR
    OUTPUT Matrix
ENDFUNCTION
'''
        result = self.process(source)
        self.assertNotIn('random_list', result.processed_source)
        self.assertNotIn('random_matrix', result.processed_source)


if __name__ == '__main__':
    unittest.main()
