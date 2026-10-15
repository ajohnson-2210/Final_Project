import unittest

from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC159TransactionPropertyRetirementV359Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_transaction_iterator_does_not_reinterpret_flattened_properties(self):
        source = """FUNCTION audit ACCEPTS(transactions)
    FOR EACH transaction IN transactions DO
        OUTPUT transaction_itemID
        OUTPUT transaction_item
        OUTPUT transaction_type
        OUTPUT transaction_quantity
    ENDFOR
ENDFUNCTION
"""
        result = self.process(source)

        for identifier in (
            "transaction_itemID",
            "transaction_item",
            "transaction_type",
            "transaction_quantity",
        ):
            self.assertIn(identifier, result.processed_source)
        self.assertNotIn("transaction.itemID", result.processed_source)
        self.assertNotIn("transaction.item", result.processed_source)
        self.assertNotIn("transaction.type", result.processed_source)
        self.assertNotIn("transaction.quantity", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))

    def test_explicit_transaction_member_access_is_preserved(self):
        source = """FUNCTION audit ACCEPTS(transactions)
    FOR EACH transaction IN transactions DO
        OUTPUT transaction.itemID
        OUTPUT transaction.quantity
    ENDFOR
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("OUTPUT transaction.itemID", result.processed_source)
        self.assertIn("OUTPUT transaction.quantity", result.processed_source)

    def test_gc146_inventory_specific_path_no_longer_invents_member_access(self):
        source = """FUNCTION updateInventory ACCEPTS(inventory, transactions)
    FOR EACH transaction IN transactions DO
        item <- transaction_item
        type <- transaction_type
        quantity <- transaction_quantity
    ENDFOR
    RETURN inventory
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("item <- transaction_item", result.processed_source)
        self.assertIn("type <- transaction_type", result.processed_source)
        self.assertIn("quantity <- transaction_quantity", result.processed_source)
        self.assertNotIn("transaction.item", result.processed_source)
        self.assertNotIn("transaction.type", result.processed_source)
        self.assertNotIn("transaction.quantity", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))
        self.assertFalse(any(t.rule == "GC146" for t in result.transformations))


if __name__ == "__main__":
    unittest.main()
