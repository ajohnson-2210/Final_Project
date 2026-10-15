import unittest

from aj_parser import AJParserFacade, MemberCallNode, LiteralNode
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import (
    GenericPseudocodeProcessor,
    PseudocodeProfile,
    PseudocodeProfileProcessor,
)


source_b_38 = '''FUNCTION firstNonRepeating(str):
    freq ← empty dictionary
    FOR each char IN str:
        freq[char] ← freq.get(char, 0) + 1
    FOR each char IN str:
        IF freq[char] == 1 THEN RETURN char
    RETURN None
'''


class AJV11NoneAndMemberGetV284Tests(unittest.TestCase):
    def setUp(self):
        self.parser = AJParserFacade()

    def compile(self, source):
        parsed = self.parser.parse(source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        return parsed, compiled.source_code

    def test_none_is_native_literal_and_is_case_insensitive(self):
        for spelling in ("NONE", "None", "none"):
            parsed, python_source = self.compile(
                f"FUNCTION f ACCEPTS()\nRETURN {spelling}\nENDFUNCTION\n"
            )
            returned = parsed.ast.body[0].body.statements[0].expression
            self.assertIsInstance(returned, LiteralNode)
            self.assertIsNone(returned.value)
            self.assertEqual("NONE", returned.data_type)
            self.assertIn("return None", python_source)

    def test_none_canonicalisation_does_not_touch_quoted_text(self):
        source = '''FUNCTION f ACCEPTS()
OUTPUT STRING("None")
RETURN None
ENDFUNCTION
'''
        processed, transformations = GenericPseudocodeProcessor()._canonicalise_v11_surface_syntax(source)
        self.assertIn('OUTPUT STRING("None")', processed)
        self.assertIn("RETURN NONE", processed)
        self.assertTrue(any(t.rule == "GC197" for t in transformations))

    def test_property_access_and_method_call_are_distinct(self):
        source = '''FUNCTION inspect ACCEPTS(obj)
OUTPUT obj.item
RETURN obj.item()
ENDFUNCTION
'''
        parsed, python_source = self.compile(source)
        return_expr = parsed.ast.body[0].body.statements[1].expression
        self.assertIsInstance(return_expr, MemberCallNode)
        self.assertIn("print(obj.item)", python_source)
        self.assertIn("return obj.item()", python_source)

    def test_member_call_can_be_a_standalone_statement(self):
        _, python_source = self.compile(
            "FUNCTION act ACCEPTS(drone)\ndrone.hover()\nENDFUNCTION\n"
        )
        self.assertIn("drone.hover()", python_source)

    def test_dictionary_get_resolves_only_with_dictionary_evidence(self):
        source = '''FUNCTION lookup ACCEPTS()
freq <- EMPTY DICTIONARY
RETURN freq.GET(STRING("x"), INTEGER(0))
ENDFUNCTION
'''
        parsed, python_source = self.compile(source)
        expr = parsed.ast.body[0].body.statements[1].expression
        self.assertIsInstance(expr, MemberCallNode)
        self.assertEqual("DICTIONARY_GET", expr.resolved_intrinsic)
        self.assertIn("return freq.get('x', 0)", python_source)

    def test_typed_dictionary_parameter_resolves_get_intrinsic(self):
        source = '''FUNCTION lookup ACCEPTS(freq AS DICTIONARY, key)
RETURN freq.GET(key)
ENDFUNCTION
'''
        parsed, python_source = self.compile(source)
        expr = parsed.ast.body[0].body.statements[0].expression
        self.assertEqual("DICTIONARY_GET", expr.resolved_intrinsic)
        self.assertIn("return freq[key]", python_source)

    def test_dictionary_property_resolves_get_intrinsic(self):
        source = '''CLASS Store
PROPERTY values AS DICTIONARY
CONSTRUCTOR ACCEPTS()
PROPERTY THIS.values <- EMPTY DICTIONARY
ENDCONSTRUCTOR
METHOD lookup ACCEPTS(key)
RETURN THIS.values.GET(key, NONE)
ENDMETHOD
ENDCLASS
'''
        _, python_source = self.compile(source)
        self.assertIn("return self.values.get(key, None)", python_source)

    def test_user_defined_get_method_is_not_dictionary_intrinsic(self):
        source = '''CLASS Registry
METHOD GET ACCEPTS(key)
RETURN key
ENDMETHOD
ENDCLASS
FUNCTION use ACCEPTS(registry AS Registry)
RETURN registry.GET(STRING("x"))
ENDFUNCTION
'''
        parsed, python_source = self.compile(source)
        expr = parsed.ast.body[1].body.statements[0].expression
        self.assertIsInstance(expr, MemberCallNode)
        self.assertIsNone(expr.resolved_intrinsic)
        self.assertIn("def GET(self, key):", python_source)
        self.assertIn("return registry.GET('x')", python_source)

    def test_legacy_tilde_get_remains_accepted_by_strict_parser(self):
        _, python_source = self.compile(
            '''FUNCTION lookup ACCEPTS()
freq <- EMPTY DICTIONARY
RETURN freq~GET(STRING("x"), INTEGER(0))
ENDFUNCTION
'''
        )
        self.assertIn("return freq.get('x', 0)", python_source)

    def test_generic_profile_canonicalises_legacy_tilde_get_to_dot_get(self):
        source = '''FUNCTION lookup ACCEPTS()
freq <- EMPTY DICTIONARY
RETURN freq~GET(STRING("x"), INTEGER(0))
ENDFUNCTION
'''
        result = PseudocodeProfileProcessor().process(
            source, PseudocodeProfile.GENERIC_COMPATIBILITY
        )
        self.assertIn("freq.GET", result.processed_source)
        self.assertNotIn("~GET", result.processed_source)
        self.assertTrue(any(t.rule == "GC198" for t in result.transformations))

    def test_source_b_38_is_native_v11_after_canonicalisation(self):
        result = PseudocodeProfileProcessor().process(
            source_b_38, PseudocodeProfile.GENERIC_COMPATIBILITY
        )
        self.assertIn("freq.GET(__reserved_keyword__char, 0)", result.processed_source)
        self.assertIn("RETURN NONE", result.processed_source)
        self.assertNotIn(".CALL get", result.processed_source)
        self.assertTrue(any(t.rule == "GC199" for t in result.transformations))
        self.assertTrue(any(t.rule == "GC197" for t in result.transformations))

        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        python_source = AJPythonCompiler().compile(
            FlowDiagramEncoder().encode(parsed.ast)
        ).source_code
        namespace = {}
        exec(python_source, namespace)
        self.assertEqual("w", namespace["firstNonRepeating"]("swiss"))
        self.assertIsNone(namespace["firstNonRepeating"]("aabb"))


if __name__ == "__main__":
    unittest.main()
