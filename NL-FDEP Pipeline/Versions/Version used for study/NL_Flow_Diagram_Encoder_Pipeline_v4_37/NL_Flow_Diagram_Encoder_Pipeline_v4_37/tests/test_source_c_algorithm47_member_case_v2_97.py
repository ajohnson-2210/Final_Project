import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_c_47_SOURCE = '''FUNCTION updateInventory(inventory, transactions):
    FOR each transaction in transactions:
        itemID = transaction.itemID
        quantityChange = transaction.quantity // positive for delivery, negative for purchase
        IF itemID IN inventory:
            inventory[itemID] = inventory[itemID] + quantityChange
        ELSE:
            // Handle new item, maybe set initial stock
            inventory[itemID] = quantityChange
    // Ensure no negative inventory (adjust accordingly)
    FOR each item in inventory:
        IF inventory[item] < 0:
            inventory[item] = 0 // or raise error
    RETURN inventory
'''


class source_cAlgorithm47MemberCaseV297Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()
        self.parser = AJParserFacade()

    def test_exact_occurrence_preserves_item_id_case_and_executes(self):
        result = self.processor.process(
            source_c_47_SOURCE,
            PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        self.assertIn('itemID <- transaction.itemID', result.processed_source)
        self.assertIn('quantityChange <- transaction.quantity', result.processed_source)

        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        self.assertIn('itemID = transaction.itemID', compiled.source_code)
        self.assertNotIn('transaction.itemid', compiled.source_code)

        class Transaction:
            def __init__(self, itemID, quantity):
                self.itemID = itemID
                self.quantity = quantity

        namespace = {}
        exec(compiled.source_code, namespace)
        inventory = {'A': 3, 'B': 1}
        transactions = [
            Transaction('A', 2),
            Transaction('B', -4),
            Transaction('C', 5),
        ]
        returned = namespace['updateInventory'](inventory, transactions)
        self.assertEqual({'A': 5, 'B': 0, 'C': 5}, returned)


if __name__ == '__main__':
    unittest.main()
