import unittest

from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC159FlattenedPropertyRetirementV358Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_nested_other_iterator_does_not_reinterpret_valid_identifier(self):
        source = """FUNCTION compare ACCEPTS(items)
    FOR EACH item IN items DO
        FOR EACH otherItem IN items DO
            OUTPUT otherItem_value
        ENDFOR
    ENDFOR
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("OUTPUT otherItem_value", result.processed_source)
        self.assertNotIn("otherItem.value", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))

    def test_current_and_other_flattened_names_both_remain_identifiers(self):
        source = """FUNCTION compare ACCEPTS(items)
    FOR EACH item IN items DO
        OUTPUT item_value
        FOR EACH otherItem IN items DO
            OUTPUT otherItem_value
        ENDFOR
    ENDFOR
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("OUTPUT item_value", result.processed_source)
        self.assertIn("OUTPUT otherItem_value", result.processed_source)
        self.assertNotIn("item.value", result.processed_source)
        self.assertNotIn("otherItem.value", result.processed_source)

    def test_explicit_member_access_is_preserved(self):
        source = """FUNCTION compare ACCEPTS(items)
    FOR EACH item IN items DO
        FOR EACH otherItem IN items DO
            OUTPUT otherItem.value
        ENDFOR
    ENDFOR
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("OUTPUT otherItem.value", result.processed_source)

    def test_transaction_flattened_names_are_not_gc159_property_evidence(self):
        source = """FUNCTION apply ACCEPTS(transactions)
    FOR EACH transaction IN transactions DO
        itemID <- transaction_itemID
        quantity <- transaction_quantity
    ENDFOR
    RETURN quantity
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("itemID <- transaction_itemID", result.processed_source)
        self.assertIn("quantity <- transaction_quantity", result.processed_source)
        self.assertNotIn("transaction.itemID", result.processed_source)
        self.assertNotIn("transaction.quantity", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))


if __name__ == "__main__":
    unittest.main()
