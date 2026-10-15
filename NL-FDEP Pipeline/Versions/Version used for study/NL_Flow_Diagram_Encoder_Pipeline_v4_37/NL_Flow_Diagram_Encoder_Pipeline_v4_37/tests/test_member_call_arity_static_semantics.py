from aj_parser import AJParserFacade


def fail(source):
    result=AJParserFacade().parse(source)
    assert not result.success
    assert result.error
    return result.error


def ok(source):
    result=AJParserFacade().parse(source)
    assert result.success, result.error
    return result


def test_this_method_wrong_arity_is_static_failure():
    error=fail('''CLASS Demo\n    METHOD add ACCEPTS(a, b)\n        RETURN a + b\n    ENDMETHOD\n    METHOD run ACCEPTS()\n        RETURN THIS.add(INTEGER(1))\n    ENDMETHOD\nENDCLASS\n''')
    assert "Method Demo.add requires 2 arguments, but 1 was supplied" in error


def test_this_method_exact_arity_passes():
    ok('''CLASS Demo\n    METHOD add ACCEPTS(a, b)\n        RETURN a + b\n    ENDMETHOD\n    METHOD run ACCEPTS()\n        RETURN THIS.add(INTEGER(1), INTEGER(2))\n    ENDMETHOD\nENDCLASS\n''')


def test_explicitly_typed_parameter_receiver_is_checked():
    error=fail('''CLASS Demo\n    METHOD add ACCEPTS(a, b)\n        RETURN a + b\n    ENDMETHOD\nENDCLASS\nFUNCTION use ACCEPTS(d AS Demo)\n    RETURN d.add(INTEGER(1), INTEGER(2), INTEGER(3))\nENDFUNCTION\n''')
    assert "Method Demo.add requires 2 arguments, but 3 were supplied" in error


def test_explicitly_typed_property_chain_is_checked():
    error=fail('''CLASS Child\n    METHOD ping ACCEPTS(value)\n        RETURN value\n    ENDMETHOD\nENDCLASS\nCLASS Parent\n    PROPERTY child AS Child\n    METHOD run ACCEPTS()\n        RETURN THIS.child.ping()\n    ENDMETHOD\nENDCLASS\n''')
    assert "Method Child.ping requires 1 argument, but 0 were supplied" in error


def test_unknown_external_receiver_remains_unchecked():
    ok('''FUNCTION use ACCEPTS(external)\n    RETURN external.add(INTEGER(1))\nENDFUNCTION\n''')


def test_unknown_method_on_known_class_is_not_rejected_by_arity_pass():
    ok('''CLASS Demo\n    METHOD run ACCEPTS()\n        RETURN THIS.externalMethod(INTEGER(1))\n    ENDMETHOD\nENDCLASS\n''')


def test_loop_binder_shadows_typed_receiver_inside_loop():
    ok('''CLASS Demo\n    METHOD ping ACCEPTS(a, b)\n        RETURN a\n    ENDMETHOD\nENDCLASS\nFUNCTION use ACCEPTS(d AS Demo, values)\n    FOR EACH d IN values DO\n        CALL consume(d.ping(INTEGER(1)))\n    ENDFOR\n    RETURN d.ping(INTEGER(1), INTEGER(2))\nENDFUNCTION\n''')


def test_nested_local_assignment_shadows_outer_typed_receiver():
    ok('''CLASS Demo\n    METHOD ping ACCEPTS(a, b)\n        RETURN a\n    ENDMETHOD\nENDCLASS\nFUNCTION outer ACCEPTS(d AS Demo)\n    FUNCTION inner ACCEPTS()\n        d <- EMPTY LIST\n        RETURN d.ping(INTEGER(1))\n    ENDFUNCTION\n    RETURN d.ping(INTEGER(1), INTEGER(2))\nENDFUNCTION\n''')
