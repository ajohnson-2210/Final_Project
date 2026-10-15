import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


class MemberAccessCasePreservationV297Tests(unittest.TestCase):
    def setUp(self):
        self.parser = AJParserFacade()

    def compile(self, source):
        parsed = self.parser.parse(source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        return compiled.source_code

    def test_property_member_case_is_preserved_exactly(self):
        python_source = self.compile(
            '''FUNCTION inspect ACCEPTS(record)\nOUTPUT record.itemID\nOUTPUT record.ItemID\nOUTPUT record.itemid\nENDFUNCTION\n'''
        )
        self.assertIn('print(record.itemID)', python_source)
        self.assertIn('print(record.ItemID)', python_source)
        self.assertIn('print(record.itemid)', python_source)

    def test_property_member_case_is_preserved_in_assignment_expression(self):
        python_source = self.compile(
            '''FUNCTION read ACCEPTS(transaction)\nitemID <- transaction.itemID\nRETURN itemID\nENDFUNCTION\n'''
        )
        self.assertIn('itemID = transaction.itemID', python_source)
        self.assertNotIn('transaction.itemid', python_source)

    def test_member_calls_remain_case_preserving(self):
        python_source = self.compile(
            '''FUNCTION act ACCEPTS(device)\ndevice.ResetNow()\nRETURN device.StatusCode()\nENDFUNCTION\n'''
        )
        self.assertIn('device.ResetNow()', python_source)
        self.assertIn('return device.StatusCode()', python_source)

    def test_dictionary_get_intrinsic_still_lowers_to_python_get(self):
        python_source = self.compile(
            '''FUNCTION lookup ACCEPTS()\nvalues <- EMPTY DICTIONARY\nRETURN values.GET(STRING("x"), NONE)\nENDFUNCTION\n'''
        )
        self.assertIn("return values.get('x', None)", python_source)


if __name__ == '__main__':
    unittest.main()
