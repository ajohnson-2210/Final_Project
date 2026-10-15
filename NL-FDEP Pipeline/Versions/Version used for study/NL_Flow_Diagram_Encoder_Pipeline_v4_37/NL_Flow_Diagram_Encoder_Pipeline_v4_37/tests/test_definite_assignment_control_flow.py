from aj_parser import AJParserFacade


def parse(source: str):
    return AJParserFacade().parse(source)


def assert_unbound(source: str, name: str):
    result = parse(source)
    assert not result.success
    assert name in result.error
    assert "read before declaration or assignment" in result.error
    assert result.report.stages[-1].name == "STATIC_SEMANTIC_ANALYSIS"


def test_if_without_else_does_not_definitely_assign_new_name():
    assert_unbound('''FUNCTION demo ACCEPTS(flag)
    IF flag THEN
        x <- 1
    ENDIF
    OUTPUT x
ENDFUNCTION
''', 'x')


def test_if_else_assigning_on_every_path_definitely_assigns_name():
    result = parse('''FUNCTION demo ACCEPTS(flag)
    IF flag THEN
        x <- 1
    ELSE
        x <- 2
    ENDIF
    OUTPUT x
ENDFUNCTION
''')
    assert result.success, result.error


def test_else_if_chain_requires_final_else_for_new_name_to_escape():
    assert_unbound('''FUNCTION demo ACCEPTS(a, b)
    IF a THEN
        x <- 1
    ELSE IF b THEN
        x <- 2
    ENDIF
    RETURN x
ENDFUNCTION
''', 'x')


def test_all_if_else_if_else_branches_can_establish_name():
    result = parse('''FUNCTION demo ACCEPTS(a, b)
    IF a THEN
        x <- 1
    ELSE IF b THEN
        x <- 2
    ELSE
        x <- 3
    ENDIF
    RETURN x
ENDFUNCTION
''')
    assert result.success, result.error


def test_while_body_only_assignment_does_not_escape_zero_iteration_loop():
    assert_unbound('''FUNCTION demo ACCEPTS(flag)
    WHILE flag DO
        x <- 1
        flag <- BOOLEAN(FALSE)
    ENDWHILE
    RETURN x
ENDFUNCTION
''', 'x')


def test_foreach_body_only_assignment_does_not_escape_zero_iteration_loop():
    assert_unbound('''FUNCTION demo ACCEPTS(values)
    FOR EACH item IN values DO
        x <- item
    ENDFOR
    RETURN x
ENDFUNCTION
''', 'x')


def test_range_body_only_assignment_does_not_escape_zero_iteration_loop():
    assert_unbound('''FUNCTION demo ACCEPTS(limit)
    FOR i <- IN RANGE 0 TO limit DO
        x <- i
    ENDFOR
    RETURN x
ENDFUNCTION
''', 'x')


def test_preexisting_name_remains_available_after_conditional_and_loop():
    result = parse('''FUNCTION demo ACCEPTS(flag, values)
    x <- 0
    IF flag THEN
        x <- 1
    ENDIF
    FOR EACH item IN values DO
        x <- item
    ENDFOR
    RETURN x
ENDFUNCTION
''')
    assert result.success, result.error


def test_try_catch_requires_assignment_on_both_paths():
    assert_unbound('''FUNCTION demo ACCEPTS()
    TRY
        x <- 1
    CATCH error
        OUTPUT error
    ENDTRY
    RETURN x
ENDFUNCTION
''', 'x')


def test_try_catch_assignment_on_both_paths_is_definite_after_endtry():
    result = parse('''FUNCTION demo ACCEPTS()
    TRY
        x <- 1
    CATCH error
        x <- 2
    ENDTRY
    RETURN x
ENDFUNCTION
''')
    assert result.success, result.error


def test_named_catch_binding_does_not_escape_catch_scope():
    assert_unbound('''FUNCTION demo ACCEPTS()
    TRY
        RAISE STRING("boom")
    CATCH error
        OUTPUT error
    ENDTRY
    RETURN error
ENDFUNCTION
''', 'error')


def test_break_branch_is_excluded_from_later_loop_body_definite_assignment_join():
    result = parse('''FUNCTION demo ACCEPTS(values, flag)
    FOR EACH item IN values DO
        IF flag THEN
            BREAK
        ELSE
            x <- item
        ENDIF
        OUTPUT x
    ENDFOR
    RETURN NONE
ENDFUNCTION
''')
    assert result.success, result.error


def test_continue_branch_is_excluded_from_later_loop_body_definite_assignment_join():
    result = parse('''FUNCTION demo ACCEPTS(values, flag)
    FOR EACH item IN values DO
        IF flag THEN
            CONTINUE
        ELSE
            x <- item
        ENDIF
        OUTPUT x
    ENDFOR
    RETURN NONE
ENDFUNCTION
''')
    assert result.success, result.error
