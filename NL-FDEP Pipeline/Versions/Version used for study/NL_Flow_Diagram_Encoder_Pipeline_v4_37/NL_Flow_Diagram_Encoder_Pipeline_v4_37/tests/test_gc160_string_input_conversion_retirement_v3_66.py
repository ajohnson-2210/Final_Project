import unittest

from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor
from aj_python_compiler import AJPythonCompiler


class GC160StringInputConversionRetirementV366Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def compile_processed(self, source):
        result = self.process(source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        return result, compiled.source_code

    def test_indexed_length_text_input_stays_string(self):
        source = '''FUNCTION inspect ACCEPTS()
    text <- INPUT(STRING("Enter text"))
    first <- text[0]
    OUTPUT LENGTH OF text
    RETURN text
ENDFUNCTION
'''
        result, python_source = self.compile_processed(source)
        self.assertIn('text <- INPUT(STRING("Enter text"))', result.processed_source)
        self.assertNotIn('list_from_string', result.processed_source)
        self.assertIn("text = input('Enter text')", python_source)
        self.assertIn('first = text[0]', python_source)
        self.assertIn('print(len(text))', python_source)
        self.assertIn('return text', python_source)
        self.assertNotIn('list(input(', python_source)

    def test_name_and_prompt_text_are_not_conversion_evidence(self):
        source = '''FUNCTION inspect ACCEPTS()
    paragraph <- INPUT(STRING("Enter paragraph text"))
    last <- paragraph[LENGTH OF paragraph - 1]
    RETURN paragraph
ENDFUNCTION
'''
        result, python_source = self.compile_processed(source)
        self.assertIn('paragraph <- INPUT(STRING("Enter paragraph text"))', result.processed_source)
        self.assertNotIn('list_from_string', result.processed_source)
        self.assertIn("paragraph = input('Enter paragraph text')", python_source)
        self.assertIn('return paragraph', python_source)

    def test_explicit_list_from_string_call_remains_explicit(self):
        source = '''FUNCTION inspect ACCEPTS(text)
    characters <- CALL list_from_string(text)
    RETURN characters
ENDFUNCTION
'''
        result, python_source = self.compile_processed(source)
        self.assertIn('characters <- CALL list_from_string(text)', result.processed_source)
        self.assertIn('characters = list(text)', python_source)
        self.assertIn('return characters', python_source)

    def test_non_text_collection_resolution_is_unchanged(self):
        source = '''Items <- INPUT(STRING("Enter Items"))
FOR i <- IN RANGE 0 TO LENGTH OF Items - 1 DO
    OUTPUT Items[i]
ENDFOR
'''
        result = self.process(source)
        self.assertNotIn('list_from_string', result.processed_source)


if __name__ == '__main__':
    unittest.main()
