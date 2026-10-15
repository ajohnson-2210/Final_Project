import unittest

from aj_parser import (
    AJParserFacade,
    ClassNode,
    ConstructorNode,
    MethodNode,
    PropertyAssignmentNode,
    PropertyDeclarationNode,
)
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


STACK_AJ = '''CLASS Stack
    PROPERTY data AS LIST

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.data <- EMPTY LIST
    ENDCONSTRUCTOR

    METHOD push ACCEPTS(item)
        APPEND item TO THIS.data
    ENDMETHOD

    METHOD pop ACCEPTS()
        IF LENGTH OF THIS.data == 0 THEN
            RETURN STRING("Underflow")
        ENDIF
        RETURN REMOVE LAST ITEM FROM THIS.data
    ENDMETHOD

    METHOD peek ACCEPTS()
        IF LENGTH OF THIS.data == 0 THEN
            RETURN STRING("Empty")
        ENDIF
        RETURN THIS.data[-1]
    ENDMETHOD
ENDCLASS
'''


class AJV1ClassGrammarV283Tests(unittest.TestCase):
    def setUp(self):
        self.parser = AJParserFacade()

    def compile(self, source):
        parsed = self.parser.parse(source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        return parsed, compiled.source_code

    def test_frozen_property_constructor_method_syntax_parses_and_compiles(self):
        parsed, python_source = self.compile(STACK_AJ)
        cls = parsed.ast.body[0]
        self.assertIsInstance(cls, ClassNode)
        self.assertIsInstance(cls.body.statements[0], PropertyDeclarationNode)
        self.assertIsInstance(cls.body.statements[1], ConstructorNode)
        self.assertIsInstance(cls.body.statements[1].body.statements[0], PropertyAssignmentNode)
        self.assertTrue(all(isinstance(node, MethodNode) for node in cls.body.statements[2:]))

        self.assertIn("class Stack:", python_source)
        self.assertIn("def __init__(self):", python_source)
        self.assertIn("self.data = []", python_source)
        self.assertIn("def push(self, item):", python_source)
        self.assertIn("return self.data.pop(-1)", python_source)
        self.assertIn("return self.data[(-1)]", python_source)

        namespace = {}
        exec(python_source, namespace)
        stack = namespace["Stack"]()
        stack.push(3)
        stack.push(5)
        self.assertEqual(5, stack.peek())
        self.assertEqual(5, stack.pop())
        self.assertEqual(3, stack.peek())

    def test_constructor_parameters_remain_supported_when_explicit_in_aj(self):
        source = '''CLASS Box
    PROPERTY value AS INTEGER
    CONSTRUCTOR ACCEPTS(value AS INTEGER)
        PROPERTY THIS.value <- value
    ENDCONSTRUCTOR
    METHOD get ACCEPTS()
        RETURN THIS.value
    ENDMETHOD
ENDCLASS
'''
        _, python_source = self.compile(source)
        self.assertIn("def __init__(self, value):", python_source)
        self.assertIn("self.value = value", python_source)
        namespace = {}
        exec(python_source, namespace)
        self.assertEqual(7, namespace["Box"](7).get())

    def test_property_is_rejected_outside_class(self):
        parsed = self.parser.parse("PROPERTY data AS LIST\n")
        self.assertFalse(parsed.success)
        self.assertIn("PROPERTY outside class", parsed.error)

    def test_constructor_is_rejected_outside_class(self):
        parsed = self.parser.parse("CONSTRUCTOR ACCEPTS()\nENDCONSTRUCTOR\n")
        self.assertFalse(parsed.success)
        self.assertIn("CONSTRUCTOR outside class", parsed.error)

    def test_method_is_rejected_outside_class(self):
        parsed = self.parser.parse("METHOD push ACCEPTS(item)\nRETURN item\nENDMETHOD\n")
        self.assertFalse(parsed.success)
        self.assertIn("METHOD outside class", parsed.error)


if __name__ == "__main__":
    unittest.main()
