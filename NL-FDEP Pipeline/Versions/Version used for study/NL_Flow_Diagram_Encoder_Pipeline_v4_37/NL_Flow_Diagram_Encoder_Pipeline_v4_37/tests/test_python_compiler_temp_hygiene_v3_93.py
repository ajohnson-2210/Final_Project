import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


class PythonCompilerTemporaryHygieneTests(unittest.TestCase):
    def compile(self, canonical: str) -> str:
        parsed = AJParserFacade().parse(canonical)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertTrue(compiled.success, compiled.message)
        return compiled.source_code

    def test_nested_push_pop_uses_fresh_temp_when_temp_names_are_source_parameters(self):
        canonical = '''FUNCTION transfer ACCEPTS(temp, temp_1)
    source <- CALL create_stack()
    target <- CALL create_stack()
    CALL PUSH(7, source)
    CALL PUSH(CALL POP(source), target)
    RETURN TUPLE(temp, temp_1, CALL POP(target))
ENDFUNCTION
'''
        python_source = self.compile(canonical)
        self.assertIn('temp_2 = source.pop(-1)', python_source)
        self.assertIn('target.append(temp_2)', python_source)
        namespace = {}
        exec(python_source, namespace)
        self.assertEqual((99, 100, 7), namespace['transfer'](99, 100))

    def test_nested_dequeue_enqueue_does_not_overwrite_source_temp(self):
        canonical = '''FUNCTION transfer ACCEPTS(temp)
    source <- CALL create_queue()
    target <- CALL create_queue()
    CALL ENQUEUE(source, 8)
    CALL ENQUEUE(target, CALL DEQUEUE(source))
    RETURN TUPLE(temp, CALL DEQUEUE(target))
ENDFUNCTION
'''
        python_source = self.compile(canonical)
        self.assertIn('temp_1 = source.pop(0)', python_source)
        self.assertIn('target.append(temp_1)', python_source)
        namespace = {}
        exec(python_source, namespace)
        self.assertEqual((99, 8), namespace['transfer'](99))

    def test_indexed_swap_does_not_overwrite_source_temp(self):
        canonical = '''FUNCTION exchange ACCEPTS(values, temp)
    CALL swap(values, 0, 1)
    RETURN temp
ENDFUNCTION
'''
        python_source = self.compile(canonical)
        self.assertIn('temp_1 = values[0]', python_source)
        self.assertIn('values[1] = temp_1', python_source)
        namespace = {}
        exec(python_source, namespace)
        values = [1, 2]
        self.assertEqual(99, namespace['exchange'](values, 99))
        self.assertEqual([2, 1], values)

    def test_historical_temp_spelling_is_retained_when_free(self):
        canonical = '''FUNCTION exchange ACCEPTS(values)
    CALL swap(values, 0, 1)
    RETURN values
ENDFUNCTION
'''
        python_source = self.compile(canonical)
        self.assertIn('temp = values[0]', python_source)
        self.assertIn('values[1] = temp', python_source)


if __name__ == '__main__':
    unittest.main()
