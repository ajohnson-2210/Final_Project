from aj_parser import AJParserFacade, QuitNode
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from semantic_signature import flow_graph_validation


def parse(source: str):
    result = AJParserFacade().parse(source)
    assert result.success, result.error
    return result


def compile_source(source: str):
    parsed = parse(source)
    flow = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(flow)
    assert compiled.success, compiled.message
    return parsed, flow, compiled.source_code


def test_quit_is_valid_at_top_level_and_has_dedicated_ast_node():
    parsed = parse('OUTPUT STRING("done")\nQUIT\n')
    assert isinstance(parsed.ast.body[1], QuitNode)


def test_quit_lowers_deterministically_to_python_system_exit():
    _, _, source = compile_source('OUTPUT STRING("done")\nQUIT\n')
    assert "print('done')" in source
    assert 'raise SystemExit' in source


def test_quit_is_terminal_in_flow_graph_and_does_not_fall_through():
    _, flow, _ = compile_source(
        'flag <- BOOLEAN(TRUE)\n'
        'IF flag == BOOLEAN(TRUE) THEN\n'
        'QUIT\n'
        'ENDIF\n'
        'OUTPUT STRING("unreached on true path")\n'
    )
    doc = flow.to_dict()
    quit_ids = [nid for nid, node in doc['nodes'].items() if node['node_type'] == 'QUIT']
    assert len(quit_ids) == 1
    quit_id = quit_ids[0]
    outs = [edge for edge in doc['edges'] if edge['source'] == quit_id]
    assert outs
    assert all(doc['nodes'][edge['target']]['node_type'] == 'END' for edge in outs)
    validation = flow_graph_validation(doc)
    assert validation['valid'], validation['issues']


def test_quit_inside_loop_terminates_program_instead_of_becoming_break():
    _, flow, source = compile_source(
        'i <- INTEGER(0)\n'
        'WHILE i < INTEGER(2) DO\n'
        'QUIT\n'
        'ENDWHILE\n'
        'OUTPUT STRING("after")\n'
    )
    doc = flow.to_dict()
    quit_id = next(nid for nid, node in doc['nodes'].items() if node['node_type'] == 'QUIT')
    outs = [edge for edge in doc['edges'] if edge['source'] == quit_id]
    assert all(doc['nodes'][edge['target']]['node_type'] == 'END' for edge in outs)
    assert 'raise SystemExit' in source
    assert '\nbreak\n' not in source


def test_legacy_stop_remains_accepted_for_backwards_compatibility():
    parsed, _, source = compile_source('STOP\n')
    assert parsed.ast.body[0].kind == 'StopNode'
    assert 'raise SystemExit' in source


def test_input_conversion_and_quit_pattern_from_baseline_is_expressible_in_v1_3():
    _, flow, source = compile_source(
        'loop <- BOOLEAN(TRUE)\n'
        'WHILE loop == BOOLEAN(TRUE) DO\n'
        'givenNum <- INPUT(STRING("Enter Number: "))\n'
        'TRY\n'
        'givenNum <- CALL INTEGER(givenNum)\n'
        'loop <- BOOLEAN(FALSE)\n'
        'CATCH\n'
        'OUTPUT STRING("Invalid number")\n'
        'ENDTRY\n'
        'ENDWHILE\n'
        'TRY\n'
        'QUIT\n'
        'CATCH\n'
        'OUTPUT STRING("unreachable")\n'
        'ENDTRY\n'
    )
    structured = flow.to_dict()['structured_program']
    assert 'CastNode' in repr(structured)
    assert 'QuitNode' in repr(structured)
    assert 'int(givenNum)' in source
    assert 'raise SystemExit' in source
