import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC146TransactionPropertyRetirementV363Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_update_inventory_preserves_declared_flattened_identifiers_and_compiles(self):
        source = '''FUNCTION updateInventory ACCEPTS(inventory, transactions)
    transaction_item <- STRING("local")
    transaction_type <- STRING("audit")
    transaction_quantity <- 1
    FOR EACH transaction IN transactions DO
        OUTPUT transaction_item
        OUTPUT transaction_type
        OUTPUT transaction_quantity
    ENDFOR
    RETURN inventory
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn('transaction_item <- STRING("local")', result.processed_source)
        self.assertIn('transaction_type <- STRING("audit")', result.processed_source)
        self.assertIn('transaction_quantity <- 1', result.processed_source)
        self.assertNotIn('transaction.item', result.processed_source)
        self.assertNotIn('transaction.type', result.processed_source)
        self.assertNotIn('transaction.quantity', result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        self.assertIn("transaction_item = 'local'", compiled.source_code)
        self.assertIn("transaction_type = 'audit'", compiled.source_code)
        self.assertIn('transaction_quantity = 1', compiled.source_code)
        self.assertNotIn('transaction.item', compiled.source_code)

    def test_explicit_member_access_remains_member_access(self):
        source = '''FUNCTION updateInventory ACCEPTS(inventory, transactions)
    FOR EACH transaction IN transactions DO
        OUTPUT transaction.item
        OUTPUT transaction.type
        OUTPUT transaction.quantity
    ENDFOR
    RETURN inventory
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn('OUTPUT transaction.item', result.processed_source)
        self.assertIn('OUTPUT transaction.type', result.processed_source)
        self.assertIn('OUTPUT transaction.quantity', result.processed_source)

    def test_gc146_alert_surface_recovery_remains_available(self):
        source = '''FUNCTION updateInventory ACCEPTS(inventory, transactions)
    transaction_item <- STRING("local")
    transaction_type <- STRING("audit")
    transaction_quantity <- 1
    ALERT STRING("check inventory")
    RETURN inventory
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn('OUTPUT STRING("check inventory")', result.processed_source)
        self.assertIn('transaction_item <- STRING("local")', result.processed_source)
        self.assertTrue(any(t.rule == 'GC146' for t in result.transformations))


if __name__ == '__main__':
    unittest.main()
