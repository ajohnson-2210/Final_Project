import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_b_ALGORITHM_30 = '''FUNCTION extractTopics(corpus, numTopics):
    tokens ← tokenize and clean each document in corpus
    vocabulary ← buildVocabulary(tokens)
    termMatrix ← buildDocumentTermMatrix(tokens, vocabulary)
    topics ← initializeRandomTopicAssignments(numTopics)
    REPEAT until convergence:
        FOR each document:
            FOR each word:
                UPDATE topic assignment using probability distribution
                UPDATE topic-word and document-topic counts
    RETURN top N words per topic as topic descriptions
'''

source_b_ALGORITHM_31 = '''FUNCTION resolveCoReferences(text):
    entities ← extractNamedEntities(text)
    mentions ← extractMentions(text)   // nouns and pronouns
    FOR each pronoun IN mentions:
        candidates ← findNearestEntities(pronoun, entities)
        bestMatch ← scoreAndRank(candidates, pronoun)
        MAP pronoun TO bestMatch
    RETURN coreferenceMap
'''

source_b_ALGORITHM_32 = '''FUNCTION answerQuestion(question, context):
    qTokens ← tokenize(question)
    cTokens ← tokenize(context)
    qEmbedding ← embed(qTokens)
    FOR each sentence IN context:
        score[sentence] ← similarity(qEmbedding, embed(sentence))
    bestSentence ← sentence with highest score
    answer ← extractAnswerSpan(question, bestSentence)
    RETURN answer
'''

source_b_ALGORITHM_33 = '''FUNCTION intSqrt(n):
    IF n == 0 THEN RETURN 0
    low ← 1, high ← n
    WHILE low <= high:
        mid ← (low + high) DIV 2
        IF mid * mid == n THEN RETURN mid
        ELSE IF mid * mid < n THEN
            result ← mid
            low ← mid + 1
        ELSE high ← mid - 1
    RETURN result
'''

source_b_ALGORITHM_34 = '''FUNCTION findCommonElements(list1, list2):
    set1 ← convert list1 to set
    result ← []
    FOR each item IN list2:
        IF item IN set1 AND item NOT IN result THEN
            APPEND item TO result
    RETURN result
'''

source_b_ALGORITHM_35 = '''FUNCTION LRUCache(capacity):
    cache ← ordered dictionary
    
    FUNCTION get(key):
        IF key NOT IN cache THEN RETURN -1
        MOVE key to most recently used position
        RETURN cache[key]
    
    FUNCTION put(key, value):
        IF key IN cache THEN REMOVE key
        ELSE IF length(cache) == capacity THEN
            REMOVE least recently used (front) item
        INSERT key:value at most recently used position
'''

source_b_ALGORITHM_36 = '''FUNCTION searchRotated(arr, target):
    low ← 0, high ← length(arr) - 1
    WHILE low <= high:
        mid ← (low + high) DIV 2
        IF arr[mid] == target THEN RETURN mid
        IF arr[low] <= arr[mid] THEN   // left half is sorted
            IF arr[low] <= target < arr[mid] THEN high ← mid - 1
            ELSE low ← mid + 1
        ELSE                           // right half is sorted
            IF arr[mid] < target <= arr[high] THEN low ← mid + 1
            ELSE high ← mid - 1
    RETURN -1
'''


class source_bAlgorithms30To36AuditTests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()
        self.parser = AJParserFacade()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def compile_processed(self, source):
        processed = self.process(source)
        parsed = self.parser.parse(processed.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        return processed, compiled.source_code

    def assert_expected_abstract_failure(self, source, retained_fragment):
        processed = self.process(source)
        self.assertIn(retained_fragment, processed.processed_source)
        parsed = self.parser.parse(processed.processed_source)
        self.assertFalse(parsed.success)
        return processed

    def test_algorithm30_is_retained_as_expected_abstract_failure(self):
        processed = self.assert_expected_abstract_failure(
            source_b_ALGORITHM_30,
            "REPEAT until convergence",
        )
        self.assertIn("UPDATE topic assignment using probability distribution", processed.processed_source)
        self.assertIn("RETURN top N words per topic as topic descriptions", processed.processed_source)

    def test_algorithm31_is_retained_as_expected_abstract_failure(self):
        processed = self.assert_expected_abstract_failure(
            source_b_ALGORITHM_31,
            "MAP pronoun TO bestMatch",
        )
        self.assertIn("RETURN coreferenceMap", processed.processed_source)

    def test_algorithm32_is_retained_as_expected_abstract_failure(self):
        processed = self.assert_expected_abstract_failure(
            source_b_ALGORITHM_32,
            "bestSentence <- sentence with highest score",
        )
        self.assertIn("CALL extractAnswerSpan", processed.processed_source)

    def test_algorithm33_is_expected_failure_under_definite_assignment_rule(self):
        processed = self.process(source_b_ALGORITHM_33)
        self.assertIn("result <- mid", processed.processed_source)
        parsed = self.parser.parse(processed.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("Identifier 'result' is read before declaration or assignment", parsed.error)
        self.assertEqual("STATIC_SEMANTIC_ANALYSIS", parsed.report.stages[-1].name)

    def test_algorithm34_remains_an_unchanged_pass(self):
        _, python_source = self.compile_processed(source_b_ALGORITHM_34)
        self.assertIn("set1 = set(list1)", python_source)
        self.assertIn("result.append(item)", python_source)

    def test_algorithm35_is_retained_as_expected_abstract_failure(self):
        processed = self.assert_expected_abstract_failure(
            source_b_ALGORITHM_35,
            "MOVE key to most recently used position",
        )
        self.assertIn("INSERT key:value at most recently used position", processed.processed_source)

    def test_algorithm36_uses_semantic_preserving_comparison_chain_recovery(self):
        processed, python_source = self.compile_processed(source_b_ALGORITHM_36)

        self.assertIn(
            "IF arr[low] <= target AND target < arr[mid] THEN",
            processed.processed_source,
        )
        self.assertIn(
            "IF arr[mid] < target AND target <= arr[high] THEN",
            processed.processed_source,
        )
        self.assertNotIn("arr[low] <= target < arr[mid]", processed.processed_source)
        self.assertNotIn("arr[mid] < target <= arr[high]", processed.processed_source)
        self.assertEqual(2, len([t for t in processed.transformations if t.rule == "GC195"]))

        self.assertIn("(arr[low] <= target) and (target < arr[mid])", python_source)
        self.assertIn("(arr[mid] < target) and (target <= arr[high])", python_source)

        namespace = {}
        exec(python_source, namespace)
        search = namespace["searchRotated"]
        arr = [4, 5, 6, 7, 0, 1, 2]
        for expected_index, target in enumerate(arr):
            self.assertEqual(expected_index, search(arr, target))
        self.assertEqual(-1, search(arr, 3))

    def test_general_safe_chain_expands_all_adjacent_comparisons(self):
        source = '''FUNCTION inside ACCEPTS(a, b, c, d)
    IF a < b <= c < d THEN
        RETURN BOOLEAN(TRUE)
    ENDIF
    RETURN BOOLEAN(FALSE)
ENDFUNCTION
'''
        processed, python_source = self.compile_processed(source)
        self.assertIn("IF a < b AND b <= c AND c < d THEN", processed.processed_source)
        self.assertTrue(any(t.rule == "GC195" for t in processed.transformations))
        self.assertIn("((a < b) and (b <= c)) and (c < d)", python_source)

    def test_already_canonical_boolean_comparisons_are_unchanged(self):
        source = '''FUNCTION inside ACCEPTS(a, b, c)
    IF a < b AND b < c THEN
        RETURN BOOLEAN(TRUE)
    ENDIF
    RETURN BOOLEAN(FALSE)
ENDFUNCTION
'''
        processed, _ = self.compile_processed(source)
        self.assertIn("IF a < b AND b < c THEN", processed.processed_source)
        self.assertFalse(any(t.rule == "GC195" for t in processed.transformations))

    def test_side_effecting_chain_is_not_duplicated_and_is_rejected(self):
        source = '''FUNCTION unsafe ACCEPTS(x)
    IF CALL nextValue() < x < 10 THEN
        RETURN BOOLEAN(TRUE)
    ENDIF
    RETURN BOOLEAN(FALSE)
ENDFUNCTION
'''
        processed = self.process(source)
        self.assertIn("CALL nextValue() < x < 10", processed.processed_source)
        self.assertFalse(any(t.rule == "GC195" for t in processed.transformations))
        parsed = self.parser.parse(processed.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("Chained comparisons are not canonical AJ", parsed.error)

    def test_strict_parser_rejects_unparenthesised_chain_instead_of_left_associating(self):
        source = '''FUNCTION invalid ACCEPTS(a, b, c)
    IF a < b < c THEN
        RETURN BOOLEAN(TRUE)
    ENDIF
    RETURN BOOLEAN(FALSE)
ENDFUNCTION
'''
        parsed = self.parser.parse(source)
        self.assertFalse(parsed.success)
        self.assertIn("Chained comparisons are not canonical AJ", parsed.error)

    def test_parenthesised_comparison_result_is_not_mistaken_for_a_chain(self):
        source = '''FUNCTION explicit ACCEPTS(a, b, c)
    IF (a < b) == c THEN
        RETURN BOOLEAN(TRUE)
    ENDIF
    RETURN BOOLEAN(FALSE)
ENDFUNCTION
'''
        parsed = self.parser.parse(source)
        self.assertTrue(parsed.success, parsed.error)


if __name__ == "__main__":
    unittest.main()
