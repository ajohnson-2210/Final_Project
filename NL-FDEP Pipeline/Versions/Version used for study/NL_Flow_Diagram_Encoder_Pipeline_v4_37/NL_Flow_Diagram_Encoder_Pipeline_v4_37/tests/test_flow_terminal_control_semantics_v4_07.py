from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from semantic_signature import flow_graph_validation


def encode(source):
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    return FlowDiagramEncoder().encode(parsed.ast).to_dict()


def outgoing(document, node_id):
    return [edge for edge in document['edges'] if edge['source'] == node_id]


def node_by_type(document, node_type):
    return next((node_id, node) for node_id, node in document['nodes'].items() if node['node_type'] == node_type)


def test_break_routes_to_statement_after_loop_not_back_to_loop_decision():
    document = encode('''x <- INTEGER(0)
WHILE x < 10 DO
    x <- x + INTEGER(1)
    IF x == 2 THEN
        BREAK
    ENDIF
ENDWHILE
OUTPUT x
''')
    break_id, _ = node_by_type(document, 'BREAK')
    output_id, _ = node_by_type(document, 'OUTPUT')
    assert {'source': break_id, 'target': output_id, 'label': 'NEXT'} in document['edges']
    assert not any(edge['label'] == 'LOOP' for edge in outgoing(document, break_id))
    assert flow_graph_validation(document)['valid']


def test_continue_routes_to_nearest_loop_decision_and_skips_following_body_statement():
    document = encode('''x <- INTEGER(0)
WHILE x < 10 DO
    x <- x + INTEGER(1)
    IF x == 2 THEN
        CONTINUE
    ENDIF
    OUTPUT x
ENDWHILE
''')
    continue_id, _ = node_by_type(document, 'CONTINUE')
    loop_id, _ = node_by_type(document, 'LOOP_DECISION')
    outs = outgoing(document, continue_id)
    assert outs == [{'source': continue_id, 'target': loop_id, 'label': 'CONTINUE'}]
    assert flow_graph_validation(document)['valid']


def test_return_inside_loop_terminates_instead_of_looping_or_falling_through():
    document = encode('''FUNCTION first_positive ACCEPTS(values AS LIST)
FOR EACH value IN values DO
    IF value > 0 THEN
        RETURN value
    ENDIF
END FOR
RETURN NONE
ENDFUNCTION
'''.replace('END FOR','ENDFOR'))
    return_nodes = [(nid,n) for nid,n in document['nodes'].items() if n['node_type'] == 'RETURN']
    assert len(return_nodes) == 2
    for return_id, _ in return_nodes:
        outs = outgoing(document, return_id)
        assert outs
        assert all(document['nodes'][edge['target']]['node_type'] == 'END' for edge in outs)
        assert not any(edge['label'] == 'LOOP' for edge in outs)
    assert flow_graph_validation(document)['valid']


def test_inner_break_exits_only_inner_loop_then_outer_body_continues():
    document = encode('''FUNCTION demo ACCEPTS(outer_values AS LIST, inner_values AS LIST)
FOR EACH outer IN outer_values DO
    FOR EACH inner IN inner_values DO
        BREAK
    ENDFOR
    OUTPUT outer
ENDFOR
RETURN NONE
ENDFUNCTION
''')
    break_id, _ = node_by_type(document, 'BREAK')
    output_id, _ = node_by_type(document, 'OUTPUT')
    assert {'source': break_id, 'target': output_id, 'label': 'NEXT'} in document['edges']
    assert flow_graph_validation(document)['valid']
