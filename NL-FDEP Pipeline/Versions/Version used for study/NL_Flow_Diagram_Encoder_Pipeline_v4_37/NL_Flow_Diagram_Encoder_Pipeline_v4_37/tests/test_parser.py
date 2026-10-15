import unittest,sys
sys.path.insert(0,'.')
from aj_parser import AJParserFacade

class Tests(unittest.TestCase):
    def test_valid(self):
        src='''FUNCTION sum_even ACCEPTS(numbers AS LIST)\n total <- INTEGER(0)\n FOR EACH number IN numbers DO\n  IF number MODULUS 2 == 0 THEN\n   total <- total + number\n  ENDIF\n ENDFOR\n RETURN total\nENDFUNCTION\n'''
        r=AJParserFacade().parse(src); self.assertTrue(r.success,r.report.pretty()); self.assertGreater(len(r.adjacency_list.nodes),5)
    def test_missing_endif(self):
        r=AJParserFacade().parse('IF x > 0 THEN\nOUTPUT x\n'); self.assertFalse(r.success); self.assertIn('expected one of',r.error.lower())
    def test_break_outside_loop(self):
        r=AJParserFacade().parse('BREAK\n'); self.assertFalse(r.success); self.assertIn('outside loop',r.error.lower())

    def test_question_mark_is_not_an_aj_assignment_token(self):
        # AJ_24038155 Dialect v1.0 assignment is strictly ``<-``.  A bare
        # question mark may occur in lossy legacy source recovery upstream,
        # but it is never a canonical token or alias accepted by the parser.
        r = AJParserFacade().parse('Found ? BOOLEAN(False)\n')
        self.assertFalse(r.success)
        self.assertIn("unrecognised character '?'", r.error.lower())

    def test_canonical_assignment_operator_remains_left_arrow_ascii(self):
        r = AJParserFacade().parse('Found <- BOOLEAN(False)\n')
        self.assertTrue(r.success, r.report.pretty())
if __name__=='__main__':unittest.main()
