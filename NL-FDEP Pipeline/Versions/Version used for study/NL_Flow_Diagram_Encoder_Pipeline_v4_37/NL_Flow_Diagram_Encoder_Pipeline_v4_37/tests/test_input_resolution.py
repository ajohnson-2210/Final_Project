import unittest

from input_resolution import score_input_resolution


class InputResolutionTests(unittest.TestCase):
    def test_collection_semantics_can_promote_when_encoding_is_insufficient(self):
        source = """IP_List <- INPUT(STRING("Enter IP_List"))
FOR EACH IP IN IP_List DO
    OUTPUT IP
ENDFOR
"""
        result = score_input_resolution(source, "IP_List")
        self.assertEqual(result.semantic_type, "COLLECTION")
        self.assertEqual(result.semantic_confidence, "medium")
        self.assertEqual(result.encoding_confidence, "insufficient")
        self.assertEqual(result.resolution, "PROMOTE_TO_PARAMETER")
        self.assertIsNone(result.encoding)

    def test_tuple_semantics_do_not_invent_delimiter(self):
        source = """Coordinates <- INPUT(STRING("Enter Coordinates"))
x <- Coordinates[0]
y <- Coordinates[1]
RETURN TUPLE(x, y)
"""
        result = score_input_resolution(source, "Coordinates")
        self.assertEqual(result.semantic_type, "TUPLE")
        self.assertEqual(result.encoding_confidence, "insufficient")
        self.assertIsNone(result.encoding)

    def test_indexed_length_input_is_high_confidence_list(self):
        source = """Items <- INPUT(STRING("Enter Items"))
FOR i <- IN RANGE 0 TO LENGTH OF Items - 1 DO
    OUTPUT Items[i]
ENDFOR
"""
        result = score_input_resolution(source, "Items")
        self.assertEqual(result.semantic_type, "LIST")
        self.assertEqual(result.semantic_confidence, "high")
        self.assertEqual(result.encoding_confidence, "insufficient")

    def test_text_indexing_preserves_explicit_string_input(self):
        source = """Text <- INPUT(STRING("Enter Text"))
FOR End <- IN RANGE 0 TO LENGTH OF Text - 1 DO
    OUTPUT Text[End]
ENDFOR
"""
        result = score_input_resolution(source, "Text")
        self.assertEqual(result.semantic_type, "STRING")
        self.assertIsNone(result.deterministic_conversion)
        self.assertEqual(result.resolution, "PRESERVE_EXPLICIT_INPUT")


if __name__ == "__main__":
    unittest.main()
