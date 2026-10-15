import json
import tempfile
import unittest
from pathlib import Path

from aj_test_harness import TestCase
from nl_flow_pipeline import NLFlowDiagramEncoderPipeline
from pseudocode_profiles import (
    GenericPseudocodeLexer,
    GenericPseudocodeProcessor,
    PseudocodeProfile,
    PseudocodeProfileProcessor,
)


class PseudocodeProfileTests(unittest.TestCase):

    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def test_strict_profile_performs_only_safe_cleanup(self):
        source = "```text\ntotal ← INTEGER(0)   \nOUTPUT total\n```"

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.AJ_DIALECT_STRICT,
        )

        self.assertEqual(
            result.processed_source,
            "total <- INTEGER(0)\nOUTPUT total",
        )
        self.assertTrue(result.source_modified)
        self.assertGreaterEqual(result.transformation_count, 2)

    def test_generic_lexer_classifies_supported_statements(self):
        tokens = GenericPseudocodeLexer().tokenise(
            "SET total TO 0\nPRINT total\nEND IF"
        )

        categories = []

        for token in tokens:
            categories.append(token.category)

        self.assertEqual(
            categories,
            ["SET_ASSIGNMENT", "OUTPUT", "END_IF"],
        )

    def test_generic_profile_converts_compatible_syntax(self):
        source = "SET total TO 0\ntotal = total + 3\nPRINT total"

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
        )

        self.assertEqual(
            result.processed_source,
            "total <- 0\ntotal <- total + 3\nOUTPUT total",
        )
        self.assertEqual(result.transformation_count, 3)

    def test_generic_profile_normalises_corpus_unicode_characters(self):
        source = (
            'IF a ≠ b AND a ≤ b AND b ≥ a THEN\n'
            'total ← total × 2\n'
            'limit ← -∞\n'
            'angle ← 90°\n'
            'OUTPUT “value”'
        )

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
        )

        self.assertIn('a != b', result.processed_source)
        self.assertIn('a <= b', result.processed_source)
        self.assertIn('b >= a', result.processed_source)
        self.assertIn('total <- total * 2', result.processed_source)
        self.assertIn('limit <- CALL negative_infinity()', result.processed_source)
        self.assertIn('angle <- 90 DEG', result.processed_source)
        self.assertIn('OUTPUT STRING("value")', result.processed_source)

        rules = {transformation.rule for transformation in result.transformations}

        self.assertTrue(
            {"GC001", "GC002", "GC003", "GC004", "GC005", "GC006", "GC008", "GC009", "GC017"}.issubset(rules)
        )

    def test_generic_profile_normalises_corpus_operator_forms(self):
        source = (
            "count++\n"
            "index--\n"
            "total += value\n"
            "balance -= cost\n"
            "product *= factor\n"
            "ratio /= divisor\n"
            "remainder %= divisor\n"
            "IF found = FALSE THEN\n"
            "total = total + 1"
        )

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
        )

        expected_fragments = [
            "count <- count + 1",
            "index <- index - 1",
            "total <- total + value",
            "balance <- balance - cost",
            "product <- product * factor",
            "ratio <- ratio / divisor",
            "remainder <- remainder % divisor",
            "IF found == BOOLEAN(False) THEN",
            "total <- total + 1",
        ]

        for fragment in expected_fragments:
            self.assertIn(fragment, result.processed_source)

        rules = {transformation.rule for transformation in result.transformations}
        self.assertTrue(
            {
                "GC018", "GC019", "GC020", "GC021", "GC022",
                "GC023", "GC024", "GC025", "GC026",
            }.issubset(rules)
        )

    def test_generic_profile_normalises_collection_forms(self):
        source = (
            "items = empty List\n"
            "seen = empty Set\n"
            "counts = empty Hash Map\n"
            "queue = empty Queue\n"
            "deque = empty DoubleEndedQueue\n"
            "items.append(value)\n"
            "seen.add(value)\n"
            "queue.enqueue(value)\n"
            "item = queue.dequeue()\n"
            "deque.push_back(value)\n"
            "first = deque.pop_front()\n"
            "last = deque.pop_back()"
        )

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
        )

        expected = [
            "items <- EMPTY LIST",
            "seen <- EMPTY SET",
            "counts <- EMPTY DICTIONARY",
            "queue <- CALL create_queue()",
            "deque <- CALL create_deque()",
            "APPEND value TO items",
            "CALL add_to_set(seen, value)",
            "CALL ENQUEUE(queue, value)",
            "item <- CALL DEQUEUE(queue)",
            "CALL deque_push_back(deque, value)",
            "first <- CALL deque_pop_front(deque)",
            "last <- CALL deque_pop_back(deque)",
        ]
        for fragment in expected:
            self.assertIn(fragment, result.processed_source)


    def test_general_profile_does_not_normalise_collection_forms(self):
        source = "items = empty List\nitems.append(value)"
        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )
        self.assertEqual(result.processed_source, source)
        self.assertEqual(result.transformation_count, 0)

    def test_general_profile_does_not_normalise_operator_forms(self):
        source = "count++\nIF found = FALSE THEN\ntotal += value"

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(result.processed_source, source)
        self.assertEqual(result.transformation_count, 0)

    def test_general_profile_does_not_normalise_unicode_characters(self):
        source = 'IF a ≠ b THEN RETURN TRUE'

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(result.processed_source, source)
        self.assertEqual(result.transformation_count, 0)

    def test_general_profile_preserves_source_exactly(self):
        source = "set total to 0  \r\nprint total"

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(result.processed_source, source)
        self.assertFalse(result.source_modified)
        self.assertEqual(result.transformation_count, 0)

    def test_generic_profile_runs_complete_pipeline(self):
        source = "SET total TO 0\ntotal = total + 3\nPRINT total"

        with tempfile.TemporaryDirectory() as directory:
            result = NLFlowDiagramEncoderPipeline().run(
                pseudocode=source,
                output_directory=Path(directory),
                test_cases=[
                    TestCase(
                        name="Generic total",
                        expected_output=["3"],
                    )
                ],
                pseudocode_profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
            )

            report_path = Path(
                result.output_files["pseudocode_processing_report"]
            )
            report = json.loads(
                report_path.read_text(encoding="utf-8")
            )

        self.assertTrue(result.success, result.to_json())
        self.assertEqual(
            result.input_metadata["pseudocode_profile"],
            PseudocodeProfile.GENERIC_COMPATIBILITY.value,
        )
        self.assertEqual(report["transformation_count"], 3)

    def test_general_profile_does_not_repair_generic_syntax(self):
        source = "SET total TO 0\nPRINT total"

        with tempfile.TemporaryDirectory() as directory:
            result = NLFlowDiagramEncoderPipeline().run(
                pseudocode=source,
                output_directory=Path(directory),
                test_cases=[],
                pseudocode_profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
            )

        self.assertFalse(result.success)
        self.assertEqual(
            result.input_metadata["pseudocode_profile"],
            PseudocodeProfile.GENERAL_NO_CONVERSION.value,
        )
        self.assertIn("Expected", result.error)

    def test_general_profile_strips_initial_hash_comment_block(self):
        source = (
            "# Algorithm 1: Sum values\n"
            "This description wraps onto a second line.\n"
            "It can continue without another hash character.\n"
            "\n"
            "total <- INTEGER(0)\n"
            "OUTPUT total"
        )

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(
            result.processed_source,
            "total <- INTEGER(0)\nOUTPUT total",
        )
        self.assertTrue(result.header_comment_removed)
        self.assertEqual(result.header_lines_removed, 4)
        self.assertEqual(result.transformation_count, 0)

    def test_general_profile_strips_header_after_leading_blank_line(self):
        source = (
            "\n"
            "# Anagram Check\n"
            "\n"
            "INPUT str1, str2 IF length(str1) != length(str2) RETURN FALSE"
        )

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(
            result.processed_source,
            "INPUT str1, str2 IF length(str1) != length(str2) RETURN FALSE",
        )
        self.assertTrue(result.header_comment_removed)
        self.assertEqual(result.header_lines_removed, 3)
        self.assertEqual(result.transformation_count, 0)


    def test_general_profile_strips_header_without_blank_separator(self):
        source = (
            "# Anagram Check\n"
            "INPUT str1, str2 IF length(str1) != length(str2) RETURN FALSE"
        )

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(
            result.processed_source,
            "INPUT str1, str2 IF length(str1) != length(str2) RETURN FALSE",
        )
        self.assertTrue(result.header_comment_removed)
        self.assertEqual(result.header_lines_removed, 1)
        self.assertEqual(result.transformation_count, 0)

    def test_wrapped_header_without_blank_stops_at_pseudocode_line(self):
        source = (
            "# Anagram Check\n"
            "Checks whether two supplied strings are anagrams.\n"
            "INPUT str1, str2 IF length(str1) != length(str2) RETURN FALSE"
        )

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(
            result.processed_source,
            "INPUT str1, str2 IF length(str1) != length(str2) RETURN FALSE",
        )
        self.assertTrue(result.header_comment_removed)
        self.assertEqual(result.header_lines_removed, 2)

    def test_general_profile_strips_header_with_utf8_bom_and_indentation(self):
        source = (
            "\ufeff   # Anagram Check\n"
            "Wrapped description\n"
            "\n"
            "RETURN TRUE"
        )

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(result.processed_source, "RETURN TRUE")
        self.assertTrue(result.header_comment_removed)
        self.assertEqual(result.header_lines_removed, 3)

    def test_general_profile_strips_numbered_single_file_title(self):
        source = (
            "1. Anagram Check\n"
            "FUNCTION f ACCEPTS(x)\n"
            "RETURN x\n"
            "ENDFUNCTION"
        )

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(
            result.processed_source,
            "FUNCTION f ACCEPTS(x)\nRETURN x\nENDFUNCTION",
        )
        self.assertTrue(result.header_comment_removed)
        self.assertEqual(result.header_lines_removed, 1)
        self.assertEqual(result.transformation_count, 0)

    def test_general_profile_strips_numbered_title_with_blank_separator(self):
        source = (
            "1. Integer Square Root\n"
            "\n"
            "FUNCTION integerSqrt ACCEPTS(n)\n"
            "RETURN n\n"
            "ENDFUNCTION"
        )

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(
            result.processed_source,
            "FUNCTION integerSqrt ACCEPTS(n)\nRETURN n\nENDFUNCTION",
        )
        self.assertTrue(result.header_comment_removed)
        self.assertEqual(result.header_lines_removed, 2)

    def test_numbered_line_is_not_stripped_without_following_pseudocode(self):
        source = "1. This is prose\nAnother prose line"

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(result.processed_source, source)
        self.assertFalse(result.header_comment_removed)
        self.assertEqual(result.header_lines_removed, 0)

    def test_hash_comment_later_in_source_is_not_automatically_stripped(self):
        source = "total <- INTEGER(0)\n# later comment\nOUTPUT total"

        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

        self.assertEqual(result.processed_source, source)
        self.assertFalse(result.header_comment_removed)
        self.assertEqual(result.header_lines_removed, 0)

    def test_initial_hash_comment_block_runs_complete_pipeline(self):
        source = (
            "# Generated algorithm description\n"
            "This line is part of the wrapped description.\n"
            "\n"
            "total <- INTEGER(0)\n"
            "OUTPUT total"
        )

        with tempfile.TemporaryDirectory() as directory:
            result = NLFlowDiagramEncoderPipeline().run(
                pseudocode=source,
                output_directory=Path(directory),
                test_cases=[
                    TestCase(
                        name="Header stripped total",
                        expected_output=["0"],
                    )
                ],
                pseudocode_profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
            )

            processed_source = Path(
                result.output_files["processed_pseudocode"]
            ).read_text(encoding="utf-8")

        self.assertTrue(result.success, result.to_json())
        self.assertEqual(processed_source, "total <- INTEGER(0)\nOUTPUT total")
        self.assertTrue(result.input_metadata["header_comment_removed"])
        self.assertEqual(result.input_metadata["header_lines_removed"], 3)


if __name__ == "__main__":
    unittest.main()

class TestGenericPhase4Statements(unittest.TestCase):
    def test_statement_and_builtin_normalisation(self):
        source = """count = length(items)\nPRINT count\nDISPLAY lowercase(name)\nSWAP(a, b)\n"""
        result = GenericPseudocodeProcessor().process(source)
        self.assertIn("count <- LENGTH OF items", result.processed_source)
        self.assertIn("OUTPUT count", result.processed_source)
        self.assertIn("OUTPUT CALL lowercase(name)", result.processed_source)
        self.assertIn("temp_var <- a", result.processed_source)
        rules = {t.rule for t in result.transformations}
        self.assertTrue({"GC040", "GC043", "GC044", "GC051"}.issubset(rules))

    def test_general_profile_does_not_normalise_builtins(self):
        source = "PRINT length(items)\n"
        result = PseudocodeProfileProcessor().process(source, PseudocodeProfile.GENERAL_NO_CONVERSION)
        self.assertEqual(source, result.processed_source)
        self.assertEqual([], result.transformations)

class GenericGrammarPhase5Tests(unittest.TestCase):

    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def test_generic_profile_normalises_grammar_variants(self):
        source = (
            "BEGIN\n"
            "FUNCTION gcd(a, b):\n"
            "    WHILE b != 0:\n"
            "        b = a MOD b\n"
            "    END WHILE\n"
            "    RETURN a\n"
            "END FUNCTION\n"
            "END"
        )
        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        expected = (
            "FUNCTION gcd ACCEPTS(a, b)\n"
            "    WHILE b != 0 DO\n"
            "        b <- a MODULUS b\n"
            "    ENDWHILE\n"
            "    RETURN a\n"
            "ENDFUNCTION"
        )
        self.assertEqual(result.processed_source, expected)

    def test_generic_profile_normalises_for_and_inline_if_forms(self):
        source = (
            "PROCEDURE scan(items):\n"
            "    FOR item IN items:\n"
            "        IF item == 0 THEN RETURN FALSE\n"
            "    END FOR\n"
            "    FOR i FROM 5 DOWNTO 0:\n"
            "        PRINT i\n"
            "    END FOR\n"
            "END PROCEDURE"
        )
        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        self.assertIn("FUNCTION scan ACCEPTS(items)", result.processed_source)
        self.assertIn("FOR EACH item IN items DO", result.processed_source)
        self.assertIn("IF item == 0 THEN\n            RETURN BOOLEAN(False)\n        ENDIF", result.processed_source)
        self.assertIn("FOR i <- IN RANGE 5 TO (0) - 1 STEP -1 DO", result.processed_source)
        self.assertIn("OUTPUT i", result.processed_source)
        self.assertTrue(result.processed_source.endswith("ENDFUNCTION"))

    def test_generic_profile_preserves_inclusive_ascending_to_endpoint(self):
        source = (
            "FOR i FROM 0 TO N - 1:\n"
            "    OUTPUT i\n"
            "END FOR"
        )
        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        self.assertIn(
            "FOR i <- IN RANGE 0 TO (N - 1) + 1 DO",
            result.processed_source,
        )
        self.assertIn("GC176", {item.rule for item in result.transformations})

    def test_generic_profile_preserves_inclusive_arrow_to_endpoint(self):
        source = (
            "FOR i <- 1 TO Number\n"
            "    OUTPUT i\n"
            "ENDFOR"
        )
        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        self.assertIn(
            "FOR i <- IN RANGE 1 TO (Number) + 1 DO",
            result.processed_source,
        )

    def test_generic_profile_does_not_double_adjust_canonical_range(self):
        source = (
            "FOR i <- IN RANGE 0 TO (N - 1) + 1 DO\n"
            "    OUTPUT i\n"
            "ENDFOR"
        )
        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        self.assertEqual(result.processed_source, source)
        self.assertNotIn("+ 1) + 1", result.processed_source)

    def test_generic_profile_preserves_implicit_last_index_to_zero_direction(self):
        source = (
            "FOR i FROM LENGTH OF values - 1 TO 0\n"
            "    OUTPUT values[i]\n"
            "END FOR"
        )
        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        self.assertIn(
            "FOR i <- IN RANGE LENGTH OF values - 1 TO (0) - 1 STEP -1 DO",
            result.processed_source,
        )
        self.assertIn("GC177", {item.rule for item in result.transformations})

    def test_general_profile_does_not_normalise_grammar_variants(self):
        source = "FUNCTION demo(x):\n    IF x == 1:\n        RETURN x\nEND FUNCTION"
        result = self.processor.process(
            source=source,
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )
        self.assertEqual(result.processed_source, source)
        self.assertEqual(result.transformation_count, 0)
