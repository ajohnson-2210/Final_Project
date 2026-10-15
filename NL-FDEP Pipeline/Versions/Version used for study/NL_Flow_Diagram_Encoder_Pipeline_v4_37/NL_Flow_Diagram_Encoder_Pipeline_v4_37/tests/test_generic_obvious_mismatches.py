import unittest

from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler


class GenericObviousMismatchTests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_raw_output_string_and_sort_characters_parse(self):
        source = """String1 <- INPUT(STRING(\"Enter String1\"))
String2 <- INPUT(STRING(\"Enter String2\"))
IF LENGTH OF String1 != LENGTH OF String2 THEN
    OUTPUT \"Not Anagrams\"
ELSE
    SORT characters of String1
    SORT characters of String2
    IF String1 == String2 THEN
        OUTPUT \"Anagrams\"
    ELSE
        OUTPUT \"Not Anagrams\"
    ENDIF
ENDIF
"""
        result = self.process(source)
        self.assertIn('OUTPUT STRING("Not Anagrams")', result.processed_source)
        self.assertIn('String1 <- CALL sort_characters(String1)', result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_not_in_operator_parses(self):
        parsed = AJParserFacade().parse("FUNCTION f ACCEPTS(x, seen)\n    IF x NOT IN seen THEN\n        RETURN BOOLEAN(True)\n    ENDIF\n    RETURN BOOLEAN(False)\nENDFUNCTION\n")
        self.assertTrue(parsed.success, parsed.error)

    def test_swap_expands_to_assignments(self):
        result = self.process("SWAP left AND right\n")
        self.assertIn('temp_var <- left', result.processed_source)
        self.assertIn('left <- right', result.processed_source)

    def test_swap_indexed_items_expands_and_parses(self):
        source = "WordList <- EMPTY LIST\nj <- 0\nSWAP WordList[j], WordList[j+1]\n"
        result = self.process(source)
        self.assertIn("temp_var <- WordList[j]", result.processed_source)
        self.assertIn("WordList[j] <- WordList[j+1]", result.processed_source)
        self.assertIn("WordList[j+1] <- temp_var", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_reserved_list_identifier_and_exit_for_parse(self):
        source = """List <- INPUT(STRING("Enter List"))
Target <- INPUT(STRING("Enter Target"))
Found <- BOOLEAN(False)
FOR i from 0 to length(List)-1:
    IF List[i] == Target THEN
        OUTPUT TUPLE(STRING("Found at position"), i)
        Found <- BOOLEAN(True)
        EXIT FOR
    ENDIF
ENDFOR
IF Found == BOOLEAN(False) THEN
    OUTPUT STRING("Target not found")
ENDIF
"""
        result = self.process(source)
        self.assertIn("FUNCTION unnamed_function ACCEPTS(__reserved_keyword__List, Target)", result.processed_source)
        self.assertIn("IF __reserved_keyword__List[i] == Target THEN", result.processed_source)
        self.assertIn("BREAK", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_case_block_and_part_heading_normalise_and_parse(self):
        source = """Text <- INPUT(STRING("Enter Text"))
A <- 0
E <- 0
FOR EACH Character IN Text DO
    CASE Character OF
        STRING("a"): A <- A + 1
        STRING("e"): E <- E + 1
    ENDCASE
ENDFOR
OUTPUT TUPLE(A, E)
Part 2 - Pseudocode for Tasks 11-20
"""
        result = self.process(source)
        self.assertIn('IF Character == STRING("a") THEN', result.processed_source)
        self.assertIn('ELSE IF Character == STRING("e") THEN', result.processed_source)
        self.assertNotIn("Part 2 -", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_add_to_known_set_becomes_set_call_and_parses(self):
        source = """IP_List <- INPUT(STRING("Enter IP_List"))
UniqueIPs <- EMPTY SET
FOR EACH IP IN IP_List DO
    ADD IP TO UniqueIPs
ENDFOR
OUTPUT UniqueIPs
"""
        result = self.process(source)
        self.assertIn("CALL add_to_set(UniqueIPs, IP)", result.processed_source)
        self.assertNotIn("APPEND IP TO UniqueIPs", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("UniqueIPs.add(IP)", compiled.source_code)


    def test_source_a_algorithm_34_known_set_insertion_is_canonical(self):
        source = """BEGIN
    INPUT List1, List2

    Result ← Empty Set

    FOR EACH Item IN List1
        IF Item EXISTS IN List2 THEN
            ADD Item TO Result
        ENDIF
    ENDFOR

    OUTPUT Result
END
"""
        result = self.process(source)
        self.assertIn("Result <- EMPTY SET", result.processed_source)
        self.assertIn("CALL add_to_set(Result, Item)", result.processed_source)
        self.assertNotIn("APPEND Item TO Result", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("Result.add(Item)", compiled.source_code)

    def test_downto_range_is_normalised_once(self):
        source = """BEGIN
    INPUT Text

    Reverse ← ""

    FOR i ← LENGTH(Text)-1 DOWNTO 0
        Reverse ← Reverse + Text[i]
    ENDFOR

    OUTPUT Reverse
END
"""
        result = self.process(source)
        expected = """FUNCTION unnamed_function ACCEPTS(Text)
    Reverse <- EMPTY STRING

    FOR i <- IN RANGE LENGTH OF Text-1 TO (0) - 1 STEP -1 DO
        Reverse <- Reverse + Text[i]
    ENDFOR

    OUTPUT Reverse
ENDFUNCTION"""
        self.assertEqual(expected, result.processed_source.strip())
        self.assertNotIn("IN RANGE IN RANGE", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_anonymous_dictionary_declaration_parses(self):
        source = """Text <- INPUT(STRING("Enter Text"))
Create Dictionary
OUTPUT Text
"""
        result = self.process(source)
        self.assertIn("Anonymous_Dictionary <- EMPTY DICTIONARY", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_all_part_section_labels_are_stripped(self):
        for heading in (
            "Part 1 - Pseudocode for Tasks 1-10",
            "Part 2 - Pseudocode for Tasks 11-20",
            "Part 3 - Pseudocode for Tasks 21-30",
            "Part 10 - Additional Pseudocode",
        ):
            source = f"""Number <- 6
OUTPUT Number
{heading}
"""
            result = self.process(source)
            self.assertNotIn("Part ", result.processed_source)
            parsed = AJParserFacade().parse(result.processed_source)
            self.assertTrue(parsed.success, parsed.error)

    def test_anonymous_queue_uses_append_and_pop_zero_semantics(self):
        source = """Root <- INPUT(STRING("Enter Root"))
CREATE EMPTY QUEUE
ENQUEUE Root
WHILE Queue is not empty DO
    Node <- DEQUEUE Queue
    OUTPUT Node
ENDWHILE
"""
        result = self.process(source)
        self.assertIn("Queue <- CALL create_queue()", result.processed_source)
        self.assertIn("CALL ENQUEUE(Queue, Root)", result.processed_source)
        self.assertIn("Node <- CALL DEQUEUE(Queue)", result.processed_source)
        self.assertNotRegex(result.processed_source, r"\\bQueue\\b")

    def test_inferred_node_queue_traversal_compiles(self):
        source = """BEGIN
    INPUT Root

    CREATE Empty Queue
    ENQUEUE Root

    WHILE Queue is not empty
        Node ← DEQUEUE Queue
        OUTPUT Node.Value

        IF Node.Left exists THEN
            ENQUEUE Node.Left
        ENDIF

        IF Node.Right exists THEN
            ENQUEUE Node.Right
        ENDIF
    ENDWHILE
END
"""
        result = self.process(source)
        self.assertIn("FUNCTION unnamed_function ACCEPTS(Root)", result.processed_source)
        self.assertIn("Queue <- CALL create_queue()", result.processed_source)
        self.assertIn("Node <- CALL DEQUEUE(Queue)", result.processed_source)
        self.assertIn("OUTPUT Node.Value", result.processed_source)
        self.assertIn("IF Node.Left != NULL THEN", result.processed_source)
        self.assertIn("IF Node.Right != NULL THEN", result.processed_source)
        self.assertNotIn("CALL NULL()", result.processed_source)
        self.assertNotIn("Root_Key", result.processed_source)
        self.assertNotIn("lookup_inferred_node", result.processed_source)
        self.assertNotIn("Anonymous_Queue", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertTrue(compiled.success)
        self.assertIn("def unnamed_function(Root):", compiled.source_code)
        self.assertIn("Node = Queue.pop(0)", compiled.source_code)
        self.assertIn("print(Node.Value)", compiled.source_code)
        self.assertIn("if (Node.Left is not None):", compiled.source_code)

    def test_inferred_node_lookup_is_preinitialised_and_does_not_insert_missing_key(self):
        source = """BEGIN
    INPUT Root
    CREATE Empty Queue
    ENQUEUE Root
    WHILE Queue is not empty
        Node ← DEQUEUE Queue
        OUTPUT Node.Value
        IF Node.Left exists THEN
            ENQUEUE Node.Left
        ENDIF
        IF Node.Right exists THEN
            ENQUEUE Node.Right
        ENDIF
    ENDWHILE
END
"""
        result = self.process(source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("def unnamed_function(Root):", compiled.source_code)
        self.assertIn("Queue = []", compiled.source_code)
        self.assertIn("Queue.append(Root)", compiled.source_code)
        self.assertNotIn("_inferred_node_lookup", compiled.source_code)
        self.assertNotIn("InferredNode", compiled.source_code)

    def test_inferred_lookup_does_not_output_success_value(self):
        source = """BEGIN
    INPUT Root
    CREATE Empty Queue
    ENQUEUE Root
    WHILE Queue is not empty
        Node ← DEQUEUE Queue
        OUTPUT Node.Value
        IF Node.Left exists THEN
            ENQUEUE Node.Left
        ENDIF
        IF Node.Right exists THEN
            ENQUEUE Node.Right
        ENDIF
    ENDWHILE
END
"""
        result = self.process(source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("def unnamed_function(Root):", compiled.source_code)
        self.assertNotIn("_inferred_node_lookup", compiled.source_code)
        self.assertIn("print(Node.Value)", compiled.source_code)

    def test_stop_compiles_to_system_exit(self):
        source = """Number <- 9
WHILE Number > 0 DO
    IF Number == 9 THEN
        OUTPUT Number
        STOP
    ENDIF
    Number <- Number - 1
ENDWHILE
"""
        parsed = AJParserFacade().parse(source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertTrue(compiled.success)
        self.assertIn("raise SystemExit", compiled.source_code)
        self.assertNotIn("break", compiled.source_code)

    def test_array_stack_recovery_preserves_top_index_algorithm(self):
        source = """CREATE Stack
Top <- -1

CALL PUSH(Item)
    Top <- Top + 1
    Stack[Top] <- Item

CALL POP()
    IF Top == -1 THEN
        OUTPUT STRING("Stack Empty")
    ELSE
        Item <- Stack[Top]
        Top <- Top - 1
        OUTPUT Item
    ENDIF

CALL PEEK()
    IF Top != -1 THEN
        OUTPUT Stack[Top]
    ENDIF
"""
        result = self.process(source)
        self.assertIn("CREATE Stack", result.processed_source)
        self.assertNotIn("Stack <- EMPTY LIST", result.processed_source)
        self.assertIn("Top <- -1", result.processed_source)
        self.assertIn("FUNCTION PUSH ACCEPTS(Item)", result.processed_source)
        self.assertIn("Top <- Top + 1", result.processed_source)
        self.assertIn("Stack[Top] <- Item", result.processed_source)
        self.assertIn("FUNCTION POP ACCEPTS()", result.processed_source)
        self.assertIn("Item <- Stack[Top]", result.processed_source)
        self.assertIn("Top <- Top - 1", result.processed_source)
        self.assertIn("FUNCTION PEEK ACCEPTS()", result.processed_source)
        self.assertIn("IF Top != -1 THEN", result.processed_source)
        self.assertIn("OUTPUT Stack[Top]", result.processed_source)
        self.assertNotIn("APPEND Item TO Stack", result.processed_source)
        self.assertNotIn("REMOVE LAST ITEM FROM Stack", result.processed_source)
        self.assertNotIn("LENGTH OF Stack", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIsNone(parsed.ast)

    def test_raw_source_a_algorithm_37_bare_headers_preserve_source_operations(self):
        source = """BEGIN
    CREATE Stack
    Top ← -1

    PUSH(Item)
        Top ← Top + 1
        Stack[Top] ← Item

    POP()
        IF Top = -1 THEN
            OUTPUT "Stack Empty"
        ELSE
            Item ← Stack[Top]
            Top ← Top - 1
            OUTPUT Item
        ENDIF

    PEEK()
        IF Top ≠ -1 THEN
            OUTPUT Stack[Top]
        ENDIF
END
"""
        result = self.process(source)
        expected_fragments = (
            "CREATE Stack",
            "Top <- -1",
            "FUNCTION PUSH ACCEPTS(Item)",
            "Top <- Top + 1",
            "Stack[Top] <- Item",
            "FUNCTION POP ACCEPTS()",
            "IF Top == -1 THEN",
            "Item <- Stack[Top]",
            "Top <- Top - 1",
            "FUNCTION PEEK ACCEPTS()",
            "IF Top != -1 THEN",
            "OUTPUT Stack[Top]",
        )
        for fragment in expected_fragments:
            self.assertIn(fragment, result.processed_source)
        self.assertNotIn("Stack <- EMPTY LIST", result.processed_source)
        self.assertNotIn("APPEND", result.processed_source)
        self.assertNotIn("REMOVE LAST ITEM", result.processed_source)
        self.assertNotIn("LENGTH OF Stack", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIsNone(parsed.ast)

    def test_character_frequency_abstract_count_is_expected_failure(self):
        source = """BEGIN
    INPUT Text
    COUNT frequency of each character
    FOR EACH Character IN Text DO
        IF Frequency(Character) = 1 THEN
            OUTPUT Character
            STOP
        ENDIF
    ENDFOR
    OUTPUT "None Found"
END
"""
        result = self.process(source)
        self.assertIn('FUNCTION unnamed_function ACCEPTS(Text)', result.processed_source)
        self.assertIn("COUNT frequency of each character", result.processed_source)
        self.assertNotIn("Frequency <- EMPTY DICTIONARY", result.processed_source)
        self.assertNotIn("IF Character IN Frequency THEN", result.processed_source)
        self.assertEqual(result.processed_source.count("FOR EACH Character IN Text DO"), 1)
        self.assertFalse(any(t.rule == "GC122" for t in result.transformations))

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("Expected assignment or CALL statement", parsed.error or "")

    def test_linked_cycle_detection_preserves_source_traversal(self):
        source = """BEGIN
    INPUT Head
    Slow <- Head
    Fast <- Head
    WHILE Fast != NULL AND Fast.Next != NULL
        Slow <- Slow.Next
        Fast <- Fast.Next.Next
        IF Slow == Fast THEN
            OUTPUT "Cycle Detected"
            STOP
        ENDIF
    ENDWHILE
    OUTPUT "No Cycle"
END
"""
        result = self.process(source)
        self.assertNotIn("lookup_inferred_linked_node", result.processed_source)
        self.assertNotIn("Head_Key", result.processed_source)
        self.assertIn("Fast.Next.Next", result.processed_source)
        self.assertNotIn("CALL output_adjacency_list(Head)", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertNotIn("def output_adjacency_list(head):", compiled.source_code)
        self.assertNotIn("InferredNode", compiled.source_code)
        self.assertIn("Fast = Fast.Next.Next", compiled.source_code)

    def test_two_stack_queue_recovery(self):
        source = """BEGIN
    CREATE Stack1
    CREATE Stack2

    ENQUEUE(Item)
        PUSH Item onto Stack1

    DEQUEUE()
        IF Stack2 is empty THEN
            WHILE Stack1 is not empty
                PUSH POP(Stack1) onto Stack2
            ENDWHILE
        ENDIF

        OUTPUT POP(Stack2)
END
"""
        result = self.process(source)
        self.assertIn("Stack1 <- CALL create_stack()", result.processed_source)
        self.assertIn("Stack2 <- CALL create_stack()", result.processed_source)
        self.assertIn("FUNCTION ENQUEUE ACCEPTS(Item)", result.processed_source)
        self.assertIn("CALL PUSH(Item, Stack1)", result.processed_source)
        self.assertIn("FUNCTION DEQUEUE ACCEPTS()", result.processed_source)
        self.assertIn("IF CALL stack_is_empty(Stack2) THEN", result.processed_source)
        self.assertIn("WHILE NOT CALL stack_is_empty(Stack1) DO", result.processed_source)
        self.assertIn("CALL PUSH(CALL POP(Stack1), Stack2)", result.processed_source)
        self.assertIn("OUTPUT CALL POP(Stack2)", result.processed_source)
        self.assertNotIn("REMOVE LAST ITEM", result.processed_source)
        self.assertNotIn("APPEND Item TO Stack2", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("Stack1.append(Item)", compiled.source_code)
        self.assertIn("if (len(Stack2) == 0):", compiled.source_code)
        self.assertIn("while (not (len(Stack1) == 0)):", compiled.source_code)
        self.assertIn("temp = Stack1.pop(-1)", compiled.source_code)
        self.assertIn("Stack2.append(temp)", compiled.source_code)
        self.assertIn("print(Stack2.pop(-1))", compiled.source_code)

    def test_n_queens_with_undefined_safe_predicate_remains_expected_failure(self):
        source = """BEGIN
    INPUT N
    CREATE N * N board
    FUNCTION Solve ACCEPTS(Row)
        IF Row = N THEN
            OUTPUT Board
            RETURN
        ENDIF
        FOR Col <- 0 TO N-1
            IF Position(Row, Col) is safe THEN
                PLACE Queen at (Row, Col)
                CALL Solve(Row + 1)
                REMOVE Queen from (Row, Col)
            ENDIF
        ENDFOR
    ENDFUNCTION
    CALL Solve(0)
END
"""
        result = self.process(source)

        # The safety rule is essential algorithmic semantics. Do not fabricate
        # a board representation or an is_safe/position_is_safe function.
        self.assertNotIn("create_matrix", result.processed_source)
        self.assertNotIn("FUNCTION is_safe", result.processed_source)
        self.assertNotIn("CALL Position", result.processed_source)
        self.assertIn("Position(Row, Col) is safe", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)

    def test_matrix_addition_without_result_initialisation_remains_expected_failure(self):
        source = """BEGIN
    INPUT MatrixA, MatrixB
    INPUT Rows, Columns

    FOR i <- 0 TO Rows-1
        FOR j <- 0 TO Columns-1
            Result[i][j] <- MatrixA[i][j] + MatrixB[i][j]
        ENDFOR
    ENDFOR

    OUTPUT Result
END
"""
        result = self.process(source)

        # The element-wise addition is explicit, but Result storage is not.
        # Do not fabricate a matrix allocation or hide the omission inside a
        # generated wrapper that would make this look executable.
        self.assertNotIn("create_matrix", result.processed_source)
        self.assertNotIn("FUNCTION PROCESS", result.processed_source)
        self.assertNotIn("FUNCTION unnamed_function", result.processed_source)
        self.assertIn(
            "Result[i][j] <- MatrixA[i][j] + MatrixB[i][j]",
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)

    def test_matrix_multiplication_without_result_allocation_remains_expected_failure(self):
        source = """BEGIN
    INPUT MatrixA
    INPUT MatrixB
    INPUT RowsA
    INPUT ColumnsA
    INPUT ColumnsB

    FOR i <- 0 TO RowsA-1
        FOR j <- 0 TO ColumnsB-1
            Result[i][j] <- 0

            FOR k <- 0 TO ColumnsA-1
                Result[i][j] <- Result[i][j] +
                                MatrixA[i][k] * MatrixB[k][j]
            ENDFOR
        ENDFOR
    ENDFOR

    OUTPUT Result
END
"""
        result = self.process(source)

        # The multiplication recurrence is explicit, but the containing Result
        # matrix is never created.  Do not generate inputs, derive dimensions,
        # allocate Result, or hide the omission inside a generated wrapper.
        self.assertNotIn("random_matrix_auto", result.processed_source)
        self.assertNotIn("random_compatible_matrix", result.processed_source)
        self.assertNotIn("create_matrix", result.processed_source)
        self.assertNotIn("FUNCTION PROCESS", result.processed_source)
        self.assertNotIn("FUNCTION unnamed_function", result.processed_source)
        self.assertIn("Result[i][j] <- 0", result.processed_source)
        self.assertIn("MatrixA[i][k] * MatrixB[k][j]", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)

    def test_matrix_multiplication_explicit_result_allocation_is_not_blocked(self):
        source = """MatrixA <- CALL matrix_value()
MatrixB <- CALL matrix_value()
RowsA <- 2
ColumnsA <- 2
ColumnsB <- 2
Result <- CALL create_matrix(RowsA, ColumnsB, 0)
FOR i <- IN RANGE 0 TO RowsA DO
    FOR j <- IN RANGE 0 TO ColumnsB DO
        Result[i][j] <- 0
        FOR k <- IN RANGE 0 TO ColumnsA DO
            Result[i][j] <- Result[i][j] + MatrixA[i][k] * MatrixB[k][j]
        ENDFOR
    ENDFOR
ENDFOR
OUTPUT Result
"""
        self.assertFalse(
            self.processor.generic_processor.obvious_mismatch_normaliser._has_uninitialised_matrix_multiplication_result(source)
        )

    def test_maze_pathfinding_does_not_invent_graph_bfs(self):
        source = """BEGIN
    INPUT Maze, Start, Goal
    CREATE Queue
    MARK Start as visited
    ENQUEUE Start
    WHILE Queue is not empty
        Current <- DEQUEUE Queue
        IF Current = Goal THEN
            OUTPUT "Path Found"
            STOP
        ENDIF
        FOR EACH Neighbour of Current
            IF Neighbour not visited THEN
                MARK Neighbour as visited
                ENQUEUE Neighbour
            ENDIF
        ENDFOR
    ENDWHILE
    OUTPUT "No Path Found"
END
"""
        result = self.process(source)
        self.assertIn("FOR EACH Neighbour of Current", result.processed_source)
        self.assertNotIn("Maze[Current]", result.processed_source)
        self.assertNotIn("FUNCTION find_path", result.processed_source)
        self.assertNotIn("random_graph", result.processed_source)
        self.assertTrue(all(t.rule != "GC128" for t in result.transformations))
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)

    def test_maze_pathfinding_does_not_assume_graph_directionality(self):
        source = """BEGIN
    INPUT Maze, Start, Goal
    CREATE Queue
    MARK Start as visited
    ENQUEUE Start
    WHILE Queue is not empty
        Current <- DEQUEUE Queue
        IF Current = Goal THEN
            OUTPUT "Path Found"
            STOP
        ENDIF
        FOR EACH Neighbour of Current
            IF Neighbour not visited THEN
                MARK Neighbour as visited
                ENQUEUE Neighbour
            ENDIF
        ENDFOR
    ENDWHILE
    OUTPUT "No Path Found"
END
"""
        result = self.process(source)
        self.assertNotIn("graph[left].append(right)", result.processed_source)
        self.assertNotIn("graph[right].append(left)", result.processed_source)
        self.assertNotIn("random_graph", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)

    def test_maze_pathfinding_does_not_invent_path_state(self):
        source = """BEGIN
    INPUT Maze, Start, Goal
    CREATE Queue
    MARK Start as visited
    ENQUEUE Start
    WHILE Queue is not empty
        Current <- DEQUEUE Queue
        IF Current = Goal THEN
            OUTPUT "Path Found"
            STOP
        ENDIF
        FOR EACH Neighbour of Current
            IF Neighbour not visited THEN
                MARK Neighbour as visited
                ENQUEUE Neighbour
            ENDIF
        ENDFOR
    ENDWHILE
    OUTPUT "No Path Found"
END
"""
        result = self.process(source)
        self.assertNotIn("Previous", result.processed_source)
        self.assertNotIn("Path <-", result.processed_source)
        self.assertNotIn("Walk <-", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)

    def test_sort_characters_to_destination(self):
        source = """FUNCTION isAnagram ACCEPTS(str1, str2)
    IF LENGTH OF str1 != LENGTH OF str2 THEN
        RETURN BOOLEAN(False)
    ENDIF
    sort characters of str1 TO sorted1
    sort characters of str2 TO sorted2
    RETURN sorted1 == sorted2
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("sorted1 <- CALL sort_characters(str1)", result.processed_source)
        self.assertIn("sorted2 <- CALL sort_characters(str2)", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("sorted1 = \'\'.join(sorted(str1))", compiled.source_code)
        self.assertIn("sorted2 = \'\'.join(sorted(str2))", compiled.source_code)

    def test_postfix_increment_does_not_trigger_expression_continuation(self):
        source = """FUNCTION intersection(A, B):
    result ← []
    i ← 0, j ← 0
    WHILE i < length(A) AND j < length(B):
        IF A[i] == B[j] THEN
            APPEND A[i] TO result
            i++, j++
        ELSE IF A[i] < B[j] THEN i++
        ELSE j++
    RETURN result
"""
        result = self.process(source)

        self.assertNotIn(
            "i <- i + 1 ELSE IF",
            result.processed_source,
        )
        self.assertIn(
            "ELSE IF A[i] < B[j] THEN\n            i <- i + 1",
            result.processed_source,
        )
        self.assertIn("ELSE\n            j <- j + 1", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("while ((i < len(A)) and (j < len(B))):", compiled.source_code)
        self.assertIn("i = (i + 1)", compiled.source_code)
        self.assertIn("j = (j + 1)", compiled.source_code)

    def test_postfix_decrement_does_not_trigger_expression_continuation(self):
        source = """FUNCTION countdown ACCEPTS(i)
    WHILE i > 0 DO
        i--
        OUTPUT i
    ENDWHILE
    RETURN i
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("i <- i - 1\n        OUTPUT i", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_true_multiline_arithmetic_continuation_still_joins(self):
        source = """FUNCTION total ACCEPTS(a, b)
    result <- a +
        b
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("result <- a + b", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_commas_inside_call_arguments_are_not_split_as_statements(self):
        source = """FUNCTION f ACCEPTS(a, b)
    result <- CALL combine(a, b)
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("result <- CALL combine(a, b)", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_inline_else_if_and_else_bodies(self):
        source = """FUNCTION intersection ACCEPTS(A, B)
    result <- EMPTY LIST
    i <- 0
    j <- 0
    WHILE i < LENGTH OF A AND j < LENGTH OF B DO
        IF A[i] == B[j] THEN
            APPEND A[i] TO result
            i <- i + 1
            j <- j + 1
        ELSE IF A[i] < B[j] THEN i <- i + 1
        ELSE j <- j + 1
        ENDIF
    ENDWHILE
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("ELSE IF A[i] < B[j] THEN\n            i <- i + 1", result.processed_source)
        self.assertIn("ELSE\n            j <- j + 1", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("elif (A[i] < B[j]):", compiled.source_code)
        self.assertIn("else:", compiled.source_code)

    def test_inline_if_statement_body(self):
        source = """FUNCTION splitIntoWords ACCEPTS(sentence)
    words <- EMPTY LIST
    currentWord <- EMPTY STRING
    FOR EACH character IN sentence DO
        IF character == STRING(" ") THEN
            IF currentWord != EMPTY STRING THEN APPEND currentWord TO words THEN
            ENDIF
            currentWord <- EMPTY STRING
        ELSE
            currentWord <- currentWord + character
        ENDIF
    ENDFOR
    IF currentWord != EMPTY STRING THEN APPEND currentWord TO words THEN
    ENDIF
    RETURN words
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            "IF currentWord != EMPTY STRING THEN\n                APPEND currentWord TO words",
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("words.append(currentWord)", compiled.source_code)

    def test_endif_before_else_if_is_removed(self):
        source = """FUNCTION scoreToGrade ACCEPTS(score)
    IF score >= 70 THEN
        RETURN STRING("Distinction")
    ENDIF
    ELSE IF score >= 55 THEN RETURN STRING("Merit") THEN
    ELSE IF score >= 40 THEN RETURN STRING("Pass") THEN
    ELSE RETURN STRING("Fail")
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn('ELSE IF score >= 55 THEN', result.processed_source)
        self.assertNotIn('RETURN STRING("Distinction")\n    ENDIF\n    ELSE IF', result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("elif (score >= 55):", compiled.source_code)
        self.assertIn("elif (score >= 40):", compiled.source_code)
        self.assertIn("else:", compiled.source_code)

    def test_level_order_implied_existing_tree(self):
        source = """FUNCTION levelOrder ACCEPTS(root)
    IF root is NULL THEN
        RETURN EMPTY LIST
    ENDIF
    queue <- [root]
    result <- EMPTY LIST
    WHILE queue is not empty DO
        level <- EMPTY LIST
        nextQueue <- EMPTY LIST
        FOR EACH node IN queue DO
            APPEND node_value TO level
            IF node_left != NULL THEN APPEND node_left TO nextQueue THEN
            ENDIF
            IF node_right != NULL THEN APPEND node_right TO nextQueue THEN
            ENDIF
        ENDFOR
        APPEND level TO result
        queue <- nextQueue
    ENDWHILE
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("root == NULL", result.processed_source)
        self.assertIn("node_value", result.processed_source)
        self.assertIn("node_left", result.processed_source)
        self.assertIn("node_right", result.processed_source)
        self.assertNotIn("node.value", result.processed_source)
        self.assertNotIn("node.left", result.processed_source)
        self.assertNotIn("node.right", result.processed_source)
        self.assertNotIn("build_example_binary_tree", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("level.append(node_value)", compiled.source_code)

    def test_random_list_inference_is_narrow(self):
        source = """INPUT CustomerList
FOR EACH Customer IN CustomerList DO
    OUTPUT Customer
ENDFOR
"""
        result = self.process(source)
        self.assertIn('FUNCTION unnamed_function ACCEPTS(CustomerList)', result.processed_source)
        self.assertNotIn('CustomerList <- INPUT', result.processed_source)
        self.assertNotIn("random_list", result.processed_source)

    def test_reverse_indexed_expression(self):
        source = """FUNCTION rotateMatrix ACCEPTS(matrix, N)
    FOR i <- IN RANGE 0 TO N - 1 DO
        FOR j <- IN RANGE i + 1 TO N - 1 DO
            temp_var <- matrix[i][j]
            matrix[i][j] <- matrix[j][i]
            matrix[j][i] <- temp_var
        ENDFOR
    ENDFOR
    FOR i <- IN RANGE 0 TO N - 1 DO
        REVERSE matrix[i]
    ENDFOR
    RETURN matrix
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn(
            "CALL reverse_list(matrix[i])",
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("matrix[i].reverse()", compiled.source_code)

    def test_sliding_window_deque_shorthand(self):
        source = """FUNCTION slidingWindowMax ACCEPTS(arr, k)
    result <- EMPTY LIST
    deque <- EMPTY LIST   // stores indices
    FOR i <- IN RANGE 0 TO LENGTH OF arr - 1 DO
        WHILE deque not empty AND deque_front < i - k + 1 DO
            REMOVE front of deque
        ENDWHILE
        WHILE deque not empty AND arr[deque_back] < arr[i] DO
            REMOVE back of deque
        ENDWHILE
        APPEND i TO back of deque
        IF i >= k - 1 THEN APPEND arr[deque_front] TO result THEN
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertNotIn("// stores indices", result.processed_source)
        self.assertIn("LENGTH OF deque > 0", result.processed_source)
        self.assertIn("deque[0]", result.processed_source)
        self.assertIn("deque[-1]", result.processed_source)
        self.assertIn("REMOVE FIRST ITEM FROM deque", result.processed_source)
        self.assertIn("REMOVE LAST ITEM FROM deque", result.processed_source)
        self.assertIn("APPEND i TO deque", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("deque.pop(0)", compiled.source_code)
        self.assertIn("deque.pop()", compiled.source_code)
        self.assertIn("deque.append(i)", compiled.source_code)

    def test_convert_to_set_normalisation(self):
        source = """FUNCTION findCommonElements ACCEPTS(list1, list2)
    set1 <- convert list1 to set
    result <- EMPTY LIST
    FOR EACH item IN list2 DO
        IF item IN set1 AND item NOT IN result THEN
            APPEND item TO result
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn(
            "set1 <- CALL to_set(list1)",
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("set1 = set(list1)", compiled.source_code)

    def test_lru_cache_uses_ordered_dictionary_semantics(self):
        source = """FUNCTION LRUCache ACCEPTS(capacity)
    cache <- EMPTY DICTIONARY
    FUNCTION get ACCEPTS(key)
        IF key NOT IN cache THEN
            RETURN -1
        ENDIF
        MOVE key to most recently used position
        RETURN cache[key]
    ENDFUNCTION
    FUNCTION put ACCEPTS(key, value)
        IF key IN cache THEN REMOVE key THEN
        ELSE IF LENGTH OF cache == capacity THEN
            REMOVE least recently used (front) item
        ENDIF
        INSERT key:value at most recently used position
    ENDFUNCTION
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("CALL move_key_to_back(cache, key)", result.processed_source)
        self.assertIn("CALL remove_key(cache, key)", result.processed_source)
        self.assertIn("CALL remove_first_mapping(cache)", result.processed_source)
        self.assertIn("cache[key] <- value", result.processed_source)
        self.assertNotIn("recentlyUsed", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("cache.__setitem__(key, cache.pop(key))", compiled.source_code)
        self.assertIn("cache.pop(next(iter(cache)))", compiled.source_code)
        self.assertIn("cache[key] = value", compiled.source_code)

    def test_stack_function_shorthand(self):
        source = """FUNCTION Stack ACCEPTS()
    data <- EMPTY LIST

    FUNCTION push ACCEPTS(item)
        APPEND item TO data
    ENDFUNCTION

    FUNCTION pop ACCEPTS()
        IF data is empty THEN
            RETURN STRING("Underflow")
        ENDIF
        REMOVE and RETURN last item of data
    ENDFUNCTION

    FUNCTION peek ACCEPTS()
        IF data is empty THEN
            RETURN STRING("Empty")
        ENDIF
        RETURN last item of data
    ENDFUNCTION
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("PROPERTY data AS LIST", result.processed_source)
        self.assertIn("CONSTRUCTOR ACCEPTS()", result.processed_source)
        self.assertIn("PROPERTY THIS.data <- EMPTY LIST", result.processed_source)
        self.assertIn("IF LENGTH OF THIS.data == 0 THEN", result.processed_source)
        self.assertIn("RETURN REMOVE LAST ITEM FROM THIS.data", result.processed_source)
        self.assertIn("RETURN THIS.data[-1]", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("class Stack:", compiled.source_code)
        self.assertIn("return self.data.pop(-1)", compiled.source_code)
        self.assertIn("return self.data[(-1)]", compiled.source_code)

    def test_floyd_flattened_names_are_preserved_as_identifiers(self):
        source = """FUNCTION hasCycle ACCEPTS(head)
    slow <- head
    fast <- head
    WHILE fast != NULL AND fast_next != NULL DO
        slow <- slow_next
        fast <- fast_next.next
        IF slow == fast THEN
            RETURN BOOLEAN(True)
        ENDIF
    ENDWHILE
    RETURN BOOLEAN(False)
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            "WHILE fast != NULL AND fast_next != NULL DO",
            result.processed_source,
        )
        self.assertIn("slow <- slow_next", result.processed_source)
        self.assertIn("fast <- fast_next.next", result.processed_source)
        self.assertNotIn("slow <- slow.next", result.processed_source)
        self.assertNotIn("fast <- fast.next.next", result.processed_source)
        self.assertNotIn("InferredNode", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("Identifier 'slow_next' is read before declaration or assignment", parsed.error)

    def test_queue_function_two_stacks(self):
        source = """FUNCTION Queue ACCEPTS()
    stack1 <- EMPTY LIST
    stack2 <- EMPTY LIST

    FUNCTION enqueue ACCEPTS(item)
        PUSH item ONTO stack1
    ENDFUNCTION

    FUNCTION dequeue ACCEPTS()
        IF stack2 is empty THEN
            WHILE stack1 is not empty DO
                PUSH CALL POP(stack1) ONTO stack2
            ENDWHILE
        ENDIF
        IF stack2 is empty THEN
            RETURN STRING("Underflow")
        ENDIF
        RETURN CALL POP(stack2)
    ENDFUNCTION
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("PROPERTY stack1 AS LIST", result.processed_source)
        self.assertIn("PROPERTY stack2 AS LIST", result.processed_source)
        self.assertIn("CONSTRUCTOR ACCEPTS()", result.processed_source)
        self.assertIn("PROPERTY THIS.stack1 <- EMPTY LIST", result.processed_source)
        self.assertIn("PROPERTY THIS.stack2 <- EMPTY LIST", result.processed_source)
        self.assertIn("APPEND item TO THIS.stack1", result.processed_source)
        self.assertIn("IF LENGTH OF THIS.stack2 == 0 THEN", result.processed_source)
        self.assertIn("WHILE LENGTH OF THIS.stack1 > 0 DO", result.processed_source)
        self.assertIn("Item <- REMOVE LAST ITEM FROM THIS.stack1", result.processed_source)
        self.assertIn("APPEND Item TO THIS.stack2", result.processed_source)
        self.assertIn("RETURN REMOVE LAST ITEM FROM THIS.stack2", result.processed_source)
        self.assertIn('RETURN STRING("Underflow")', result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("class Queue:", compiled.source_code)
        self.assertIn("self.stack1.append(item)", compiled.source_code)
        self.assertIn("Item = self.stack1.pop(-1)", compiled.source_code)
        self.assertIn("self.stack2.append(Item)", compiled.source_code)
        self.assertIn("return self.stack2.pop(-1)", compiled.source_code)
        self.assertIn("return 'Underflow'", compiled.source_code)

    def test_source_b_n_queens_undefined_routines_are_not_reconstructed(self):
        source = """FUNCTION solveNQueens ACCEPTS(N)
    board <- N*N grid of 0s
    CALL placeQueens(board, 0, N)
ENDFUNCTION

FUNCTION placeQueens ACCEPTS(board, row, N)
    IF row == N THEN RECORD solution; RETURN THEN
    ENDIF
    FOR col <- IN RANGE 0 TO N - 1 DO
        IF CALL isSafe(board, row, col, N) THEN
            board[row][col] <- 1
            CALL placeQueens(board, row + 1, N)
            board[row][col] <- 0   // backtrack
        ENDIF
    ENDFOR
ENDFUNCTION

FUNCTION isSafe ACCEPTS(board, row, col, N)
    CHECK column, upper-left diagonal, upper-right diagonal for queens
    RETURN BOOLEAN(True) if no conflicts
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("RECORD solution", result.processed_source)
        self.assertIn(
            "CHECK column, upper-left diagonal, upper-right diagonal for queens",
            result.processed_source,
        )
        self.assertNotIn("checkRow <-", result.processed_source)
        self.assertNotIn("result <- CALL placeQueens", result.processed_source)
        self.assertNotIn("RETURN board", result.processed_source)
        self.assertNotIn("GC142", [item.rule for item in result.transformations])

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)


    def test_call_append_pair_is_statement(self):
        source = """FUNCTION findPairs ACCEPTS(arr, target)
    seen <- EMPTY SET
    pairs <- EMPTY LIST
    FOR EACH num IN arr DO
        complement <- target - num
        IF complement IN seen THEN
            CALL APPEND (complement, num) TO pairs
        ENDIF
        ADD num TO seen
    ENDFOR
    RETURN pairs
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("APPEND TUPLE(complement, num) TO pairs", result.processed_source)
        self.assertNotIn("CALL APPEND", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("pairs.append((complement, num))", compiled.source_code)
        self.assertIn("seen.add(num)", compiled.source_code)

    def test_matrix_addition_preserves_2d_inputs(self):
        source = """FUNCTION addMatrices ACCEPTS(A, B, rows, cols)
    result <- rows * cols matrix of 0s
    FOR i <- IN RANGE 0 TO rows - 1 DO
        FOR j <- IN RANGE 0 TO cols - 1 DO
            result[i][j] <- A[i][j] + B[i][j]
        ENDFOR
    ENDFOR
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("result <- CALL create_matrix(rows, cols, 0)", result.processed_source)
        self.assertIn("result[i][j] <- A[i][j] + B[i][j]", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("result = [[0 for _ in range(cols)] for _ in range(rows)]", compiled.source_code)
        self.assertIn("result[i][j] = (A[i][j] + B[i][j])", compiled.source_code)

    def test_source_b_matrix_multiplication_preserves_2d_inputs(self):
        source = """FUNCTION multiplyMatrices ACCEPTS(A, B, n, m, p)
    COMMENT A is n*m, B is m*p
    result <- n * p matrix of 0s
    FOR i <- IN RANGE 0 TO n - 1 DO
        FOR j <- IN RANGE 0 TO p - 1 DO
            FOR k <- IN RANGE 0 TO m - 1 DO
                result[i][j] <- result[i][j] + A[i][k] * B[k][j]
            ENDFOR
        ENDFOR
    ENDFOR
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("result <- CALL create_matrix(n, p, 0)", result.processed_source)
        self.assertIn(
            "result[i][j] <- result[i][j] + A[i][k] * B[k][j]",
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("result = [[0 for _ in range(p)] for _ in range(n)]", compiled.source_code)
        self.assertIn("A[i][k]", compiled.source_code)
        self.assertIn("B[k][j]", compiled.source_code)

    def test_inventory_update_preserves_flattened_identifiers_without_member_evidence(self):
        source = """FUNCTION updateInventory ACCEPTS(inventory, transactions)
    FOR EACH transaction IN transactions DO
        item <- transaction_item
        type <- transaction_type
        quantity <- transaction_quantity
        IF item NOT IN inventory THEN inventory[item] <- 0 THEN
        ENDIF
        IF type == STRING("purchase") THEN
            inventory[item] <- inventory[item] - quantity
        ELSE IF type == STRING("delivery") THEN
            inventory[item] <- inventory[item] + quantity
        ENDIF
        IF inventory[item] < 0 THEN ALERT STRING("Insufficient stock for ") + item THEN
        ENDIF
    ENDFOR
    RETURN inventory
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("item <- transaction_item", result.processed_source)
        self.assertIn("type <- transaction_type", result.processed_source)
        self.assertIn("quantity <- transaction_quantity", result.processed_source)
        self.assertNotIn("transaction.item", result.processed_source)
        self.assertNotIn("transaction.type", result.processed_source)
        self.assertNotIn("transaction.quantity", result.processed_source)
        self.assertIn('OUTPUT STRING("Insufficient stock for ") + item', result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("transaction_item", parsed.error)

    def test_source_b_maze_bfs_remains_expected_failure_without_navigation_semantics(self):
        source = """FUNCTION solveMaze ACCEPTS(maze, start, end)
    queue <- [(start, [start])]
    visited <- {start}
    WHILE queue is not empty DO
        (current, path) <- DEQUEUE from queue
        IF current == end THEN
            RETURN path
        ENDIF
        FOR each neighbour OF current (up/down/left/right)
            IF neighbour is valid AND not a wall AND not visited THEN
                ADD neighbour TO visited
                CALL ENQUEUE (neighbour, path + [neighbour]) TO queue
            ENDIF
    ENDWHILE
    RETURN STRING("No path found")
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("FOR each neighbour OF current (up/down/left/right)", result.processed_source)
        self.assertIn("neighbour is valid AND not a wall", result.processed_source)
        self.assertNotIn("TUPLE(row - 1, col)", result.processed_source)
        self.assertNotIn("CALL is_traversable", result.processed_source)
        self.assertTrue(all(t.rule != "GC147" for t in result.transformations))
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)

    def test_source_c_anagram_fixed_zero_array(self):
        source = """FUNCTION areAnagrams ACCEPTS(str1, str2)
    IF LENGTH OF str1 != LENGTH OF str2 THEN
        RETURN BOOLEAN(False)
    ENDIF
    countArray <- array of size 256 initialized to 0
    FOR EACH character IN str1 DO
        countArray[CALL ASCII(character)] <- countArray[CALL ASCII(character)] + 1
    ENDFOR
    FOR EACH character IN str2 DO
        countArray[CALL ASCII(character)] <- countArray[CALL ASCII(character)] - 1
        IF countArray[CALL ASCII(character)] < 0 THEN
            RETURN BOOLEAN(False)
        ENDIF
    ENDFOR
    RETURN BOOLEAN(True)
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("countArray <- CALL create_array(256, 0)", result.processed_source)
        self.assertIn("countArray[CHAR(character)]", result.processed_source)
        self.assertNotIn("ASCII", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("countArray = [0 for _ in range(256)]", compiled.source_code)
        self.assertIn("countArray[ord(character)]", compiled.source_code)

    def test_combined_two_assignment_initialiser(self):
        source = """FUNCTION intersectionSorted ACCEPTS(arr1, arr2)
    i <- 0, j = 0
    result <- EMPTY LIST
    WHILE i < LENGTH OF arr1 AND j < LENGTH OF arr2 DO
        IF arr1[i] == arr2[j] THEN
            APPEND arr1[i] TO result
            i <- i + 1
            j <- j + 1
        ELSE IF arr1[i] < arr2[j] THEN
            i <- i + 1
        ELSE
            j <- j + 1
        ENDIF
    ENDWHILE
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("i <- 0", result.processed_source)
        self.assertIn("j <- 0", result.processed_source)
        self.assertNotIn("i <- 0, j = 0", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("i = 0", compiled.source_code)
        self.assertIn("j = 0", compiled.source_code)

    def test_call_set_maps_to_to_set(self):
        source = """FUNCTION removePunctuation ACCEPTS(sentence)
    punctuation <- CALL set(STRING(". , ! ? ; : ' \\" - ( ) [ ] { }"))
    result <- EMPTY STRING
    FOR EACH character IN sentence DO
        IF character NOT IN punctuation THEN
            result <- result + character
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("punctuation <- CALL to_set(", result.processed_source)
        self.assertNotIn("CALL set(", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("punctuation = set(", compiled.source_code)

    def test_negative_infinity_initialiser(self):
        source = """FUNCTION secondLargest ACCEPTS(arr)
    IF LENGTH OF arr < 2 THEN
        RETURN NULL // or error
    ENDIF
    largest <- -infinity
    second <- -infinity
    FOR EACH num IN arr DO
        IF num > largest THEN
            second <- largest
            largest <- num
        ELSE IF num > second AND num != largest THEN
            second <- num
        ENDIF
    ENDFOR
    RETURN second
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("largest <- CALL negative_infinity()", result.processed_source)
        self.assertIn("second <- CALL negative_infinity()", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("largest = float('-inf')", compiled.source_code)
        self.assertIn("second = float('-inf')", compiled.source_code)

    def test_call_return_tuple(self):
        source = """FUNCTION sumAndAverage ACCEPTS(values)
    sum <- 0
    FOR EACH num IN values DO
        sum <- sum + num
    ENDFOR
    average <- sum / LENGTH OF values
    CALL RETURN (sum, average)
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("RETURN TUPLE(sum, average)", result.processed_source)
        self.assertNotIn("CALL RETURN", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("return (sum, average)", compiled.source_code)

    def test_function_header_and_parameters(self):
        source = """FUNCTION SWAP a AND b
    a <- a + b
    b <- a - b
    a <- a - b
    CALL RETURN (a, b)
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("FUNCTION SWAP ACCEPTS(a, b)", result.processed_source)
        self.assertIn("RETURN TUPLE(a, b)", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("def SWAP(a, b):", compiled.source_code)
        self.assertIn("return (a, b)", compiled.source_code)

    def test_seen_remove_maps_to_set_remove(self):
        source = """FUNCTION longestSubstringLength ACCEPTS(str)
    n <- LENGTH OF str
    seen <- EMPTY SET
    maxLen <- 0
    left <- 0
    FOR right <- IN RANGE 0 TO n-1 DO
        WHILE str[right] IN seen DO
            CALL seen_remove(str[left])
            left <- left + 1
        ENDWHILE
        ADD str[right] TO seen
        maxLen <- CALL max(maxLen, right - left + 1)
    ENDFOR
    RETURN maxLen
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("CALL remove_from_set(seen, str[left])", result.processed_source)
        self.assertNotIn("seen_remove", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("seen.remove(str[left])", compiled.source_code)

    def test_source_c_level_order_implied_binary_tree(self):
        source = """FUNCTION levelOrderTraversal ACCEPTS(root)
    IF root IS NULL THEN
        RETURN EMPTY LIST
    ENDIF
    result <- EMPTY LIST
    queue <- EMPTY QUEUE
    ENQUEUE root TO queue
    WHILE queue IS NOT empty DO
        levelSize <- queue~LENGTH
        currentLevel <- EMPTY LIST
        FOR i <- IN RANGE 0 TO levelSize-1 DO
            node <- DEQUEUE FROM queue
            APPEND node_value TO currentLevel
            IF node_left != NULL THEN
                ENQUEUE node_left TO queue
            ENDIF
            IF node_right != NULL THEN
                ENQUEUE node_right TO queue
            ENDIF
        ENDFOR
        APPEND currentLevel TO result
    ENDWHILE
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("root == NULL", result.processed_source)
        self.assertIn("queue <- CALL create_queue()", result.processed_source)
        self.assertIn("CALL ENQUEUE(queue, root)", result.processed_source)
        self.assertIn("WHILE NOT CALL queue_is_empty(queue) DO", result.processed_source)
        self.assertIn("levelSize <- CALL queue_size(queue)", result.processed_source)
        self.assertIn("node <- CALL DEQUEUE(queue)", result.processed_source)
        self.assertIn("APPEND node_value TO currentLevel", result.processed_source)
        self.assertIn("CALL ENQUEUE(queue, node_left)", result.processed_source)
        self.assertIn("CALL ENQUEUE(queue, node_right)", result.processed_source)
        self.assertNotIn("node.value", result.processed_source)
        self.assertNotIn("node.left", result.processed_source)
        self.assertNotIn("node.right", result.processed_source)
        self.assertNotIn("InferredNode", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("node_left", str(parsed.error))

    def test_shared_rules_reuse_across_algorithm_names(self):
        source = """FUNCTION breadthLevels ACCEPTS(root)
    IF root IS NULL THEN
        RETURN EMPTY LIST
    ENDIF
    queue <- EMPTY QUEUE
    ENQUEUE root TO queue
    WHILE queue IS NOT empty DO
        levelSize <- queue~LENGTH
        node <- DEQUEUE FROM queue
        OUTPUT node_value
        IF node_left != NULL THEN
            ENQUEUE node_left TO queue
        ENDIF
    ENDWHILE
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("root == NULL", result.processed_source)
        self.assertIn("queue <- CALL create_queue()", result.processed_source)
        self.assertIn("CALL ENQUEUE(queue, root)", result.processed_source)
        self.assertIn("CALL queue_size(queue)", result.processed_source)
        self.assertIn("node <- CALL DEQUEUE(queue)", result.processed_source)
        self.assertIn("OUTPUT node_value", result.processed_source)
        self.assertIn("CALL ENQUEUE(queue, node_left)", result.processed_source)
        self.assertNotIn("node.value", result.processed_source)
        self.assertNotIn("node.left", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("node_value", str(parsed.error))

    def test_shared_collection_last_and_append_method(self):
        source = """FUNCTION slidingWindowMax ACCEPTS(arr, k)
    result <- EMPTY LIST
    deque <- EMPTY DEQUE
    FOR i <- IN RANGE 0 TO LENGTH OF arr-1 DO
        WHILE deque IS NOT empty AND deque[0] <= i - k DO
            REMOVE FIRST ITEM FROM deque
        ENDWHILE
        WHILE deque IS NOT empty AND arr[deque[LAST]] <= arr[i] DO
            REMOVE LAST ITEM FROM deque
        ENDWHILE
        PUSH i TO deque
        IF i >= k - 1 THEN
            CALL result_append(arr[deque[0]])
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("deque <- CALL create_deque()", result.processed_source)
        self.assertIn("WHILE NOT CALL deque_is_empty(deque)", result.processed_source)
        self.assertIn("arr[CALL deque_back(deque)] <= arr[i]", result.processed_source)
        self.assertIn("CALL deque_push_back(deque, i)", result.processed_source)
        self.assertIn("APPEND arr[CALL deque_front(deque)] TO result", result.processed_source)
        self.assertNotIn("result_append", result.processed_source)
        self.assertNotIn("deque[LAST]", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("deque.pop(0)", compiled.source_code)
        self.assertIn("deque.pop(-1)", compiled.source_code)
        self.assertIn("deque.append(i)", compiled.source_code)
        self.assertIn("result.append(arr[deque[0]])", compiled.source_code)

    def test_comment_payload_is_opaque_verbatim_text(self):
        source = """FUNCTION demo ACCEPTS()
    COMMENT Step 1: x <- y + 1; punctuation ! @ # $ % : ; " ' ( ) [ ] { } ~
    COMMENT (e.g., TF-IDF) / path\\name && whatever...
    RETURN 0
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn(
            "COMMENT Step 1: x <- y + 1; punctuation ! @ # $ % : ; \" ' ( ) [ ] { } ~",
            result.processed_source,
        )
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        comments = [
            node for node in parsed.ast.body[0].body.statements
            if getattr(node, "kind", "") == "CommentNode"
        ]
        self.assertEqual(
            comments[0].text,
            "Step 1: x <- y + 1; punctuation ! @ # $ % : ; \" ' ( ) [ ] { } ~",
        )
        self.assertEqual(
            comments[1].text,
            '(e.g., TF-IDF) / path\\name && whatever...',
        )

    def test_source_c_text_classifier_comments_parse_but_remain_abstract(self):
        source = """FUNCTION trainTextClassifier ACCEPTS(documents, labels)
    COMMENT Step 1: Preprocess each document (tokenization, stopword removal, stemming)
    COMMENT Step 2: Create a vocabulary from the training set
    COMMENT Step 3: Convert each document to a feature vector (e.g., TF-IDF)
    COMMENT Step 4: Train a classifier (e.g., Naive Bayes, SVM, or Neural Network) on the feature vectors
    model <- trainedModel
    RETURN model
ENDFUNCTION
FUNCTION predictCategory ACCEPTS(model, newText)
    COMMENT Preprocess the new text similarly
    COMMENT Convert to feature vector
    COMMENT Use model to predict the category
    RETURN predictedCategory
ENDFUNCTION
"""
        result = self.process(source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("STATIC_SEMANTIC_ANALYSIS", parsed.report.pretty())
        self.assertIn("trainedModel", parsed.error)
        # Comments remain opaque, but their descriptive steps do not create
        # executable bindings for the result placeholders.
        self.assertIn("model <- trainedModel", result.processed_source)
        self.assertIn("RETURN predictedCategory", result.processed_source)

    def test_shared_values_collection_to_list(self):
        source = """FUNCTION commonElements ACCEPTS(list1, list2)
    set1 <- CALL set(list1)
    result <- EMPTY SET
    FOR EACH item IN list2 DO
        IF item IN set1 THEN
            ADD item TO result
        ENDIF
    ENDFOR
    RETURN CALL values(result)
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("set1 <- CALL to_set(list1)", result.processed_source)
        self.assertIn("RETURN CALL to_list(result)", result.processed_source)
        self.assertNotIn("CALL values(result)", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("set1 = set(list1)", compiled.source_code)
        self.assertIn("return list(result)", compiled.source_code)

    def test_source_c_lru_class_capacity_constructor(self):
        source = """CLASS LRUCache
    COMMENT Use a combination of a dictionary and a doubly linked list (or an ordered map)
    cache <- EMPTY DICTIONARY
    capacity <- given capacity
    order <- EMPTY LIST (or a doubly linked values to maintain access order)

    FUNCTION get ACCEPTS(key)
        IF key NOT IN cache THEN
            RETURN -1 // or NULL
        ENDIF
        CALL order_remove(key)
        CALL order_insert_front(key)
        RETURN cache[key]
    ENDFUNCTION

    FUNCTION put ACCEPTS(key, value)
        IF key IN cache THEN
            cache[key] <- value
            CALL order_remove(key)
            CALL order_insert_front(key)
        ELSE
            IF LENGTH OF order >= capacity THEN
                lruKey <- order[LAST]
                CALL order_remove_back()
                CALL cache_remove(lruKey)
            ENDIF
            CALL order_insert_front(key)
            cache[key] <- value
        ENDIF
    ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("CLASS LRUCache ACCEPTS(capacity)", result.processed_source)
        self.assertIn("given_capacity <- capacity", result.processed_source)
        self.assertIn("cache <- EMPTY DICTIONARY", result.processed_source)
        self.assertIn("order <- EMPTY LIST", result.processed_source)
        self.assertIn("CALL remove_from_list(order, key)", result.processed_source)
        self.assertIn("CALL insert_front(order, key)", result.processed_source)
        self.assertIn("lruKey <- order[-1]", result.processed_source)
        self.assertIn("CALL remove_last_from_list(order)", result.processed_source)
        self.assertIn("CALL remove_key(cache, lruKey)", result.processed_source)
        self.assertNotIn("given capacity", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("class LRUCache:", compiled.source_code)
        self.assertIn("def __init__(self, capacity):", compiled.source_code)
        self.assertIn("self.given_capacity = capacity", compiled.source_code)
        self.assertIn("self.cache = {}", compiled.source_code)
        self.assertIn("self.order = []", compiled.source_code)
        self.assertIn("self.order.remove(key)", compiled.source_code)
        self.assertIn("self.order.insert(0, key)", compiled.source_code)
        self.assertIn("self.order.pop()", compiled.source_code)
        self.assertIn("self.cache.pop(lruKey)", compiled.source_code)

    def test_shared_relocates_premature_endif_before_else(self):
        source = """FUNCTION searchRotatedArray ACCEPTS(arr, target)
    low <- 0
    high <- LENGTH OF arr - 1
    WHILE low <= high DO
        mid <- (low + high) INTEGER DIVISION 2
        IF arr[mid] == target THEN
            RETURN mid
        ENDIF
        COMMENT Check if left half is sorted
        IF arr[low] <= arr[mid] THEN
            IF arr[low] <= target AND target <= arr[mid] THEN
                high <- mid - 1
            ELSE
                low <- mid + 1
            ENDIF
        ENDIF
        COMMENT Right half must be sorted
        ELSE
            IF arr[mid] <= target AND target <= arr[high] THEN
                low <- mid + 1
            ELSE
                high <- mid - 1
            ENDIF
    ENDWHILE
    RETURN -1
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("COMMENT Right half must be sorted\n        ELSE", result.processed_source)
        self.assertIn(
            "                high <- mid - 1\n            ENDIF\n        ENDIF\n    ENDWHILE",
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("else:", compiled.source_code)
        self.assertIn("return (-1)", compiled.source_code)

    def test_class_stack_empty_array_shared_declaration(self):
        source = """CLASS Stack
    stackArray <- empty array
    topIndex <- -1

    FUNCTION push ACCEPTS(item)
        topIndex <- topIndex + 1
        stackArray[topIndex] <- item
    ENDFUNCTION

    FUNCTION pop ACCEPTS()
        IF topIndex < 0 THEN
            RETURN NULL // Stack underflow
        ENDIF
        item <- stackArray[topIndex]
        topIndex <- topIndex - 1
        RETURN item
    ENDFUNCTION

    FUNCTION peek ACCEPTS()
        IF topIndex < 0 THEN
            RETURN NULL
        ENDIF
        RETURN stackArray[topIndex]
    ENDFUNCTION
ENDCLASS
"""
        result = self.process(source)
        self.assertIn("CLASS Stack", result.processed_source)
        self.assertIn("stackArray <- CALL create_array(0, NONE)", result.processed_source)
        self.assertIn("RETURN NULL", result.processed_source)
        self.assertNotIn("empty array", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("class Stack:", compiled.source_code)
        self.assertIn("self.stackArray = [None] * 0", compiled.source_code)
        self.assertIn("self.topIndex = (-1)", compiled.source_code)
        self.assertIn("def push(self, item):", compiled.source_code)
        self.assertIn("def pop(self):", compiled.source_code)
        self.assertIn("def peek(self):", compiled.source_code)
        self.assertIn("self.stackArray[self.topIndex]", compiled.source_code)

    def test_shared_dictionary_get_default(self):
        source = """FUNCTION firstNonRepeating ACCEPTS(str)
    freqMap <- EMPTY DICTIONARY
    FOR EACH character IN str DO
        freqMap[character] <- CALL freqMap_get(character, 0) + 1
    ENDFOR
    FOR EACH character IN str DO
        IF freqMap[character] == 1 THEN
            RETURN character
        ENDIF
    ENDFOR
    RETURN NULL // or special character
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            "CALL dictionary_get(freqMap, character, 0)",
            result.processed_source,
        )
        self.assertIn("RETURN NULL", result.processed_source)
        self.assertNotIn("freqMap_get", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn(
            "freqMap.get(character, 0)",
            compiled.source_code,
        )

    def test_shared_floyd_flattened_next_identifiers_are_not_member_inference(self):
        source = """FUNCTION hasCycle ACCEPTS(head)
    slow <- head
    fast <- head
    WHILE fast != NULL AND fast_next != NULL DO
        slow <- slow_next
        fast <- fast_next.next
        IF slow == fast THEN
            RETURN BOOLEAN(True)
        ENDIF
    ENDWHILE
    RETURN BOOLEAN(False)
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("fast != NULL", result.processed_source)
        self.assertIn("fast_next != NULL", result.processed_source)
        self.assertIn("slow <- slow_next", result.processed_source)
        self.assertIn("fast <- fast_next.next", result.processed_source)
        self.assertNotIn("slow <- slow.next", result.processed_source)
        self.assertNotIn("fast <- fast.next.next", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("Identifier 'slow_next' is read before declaration or assignment", parsed.error)

    def test_class_queue_using_two_stacks_shared_rules(self):
        source = """CLASS QueueUsingStacks
    stack1 <- empty CALL stack (for enqueue)
    stack2 <- empty CALL stack (for dequeue)

    FUNCTION enqueue ACCEPTS(item)
        PUSH item TO stack1
    ENDFUNCTION

    FUNCTION dequeue ACCEPTS()
        IF stack2 IS empty THEN
            WHILE stack1 IS NOT empty DO
                CALL stack2_push(CALL stack1_pop())
            ENDWHILE
        ENDIF
        IF stack2 IS empty THEN
            RETURN NULL // Queue is empty
        ENDIF
        RETURN CALL stack2_pop()
    ENDFUNCTION
ENDCLASS
"""
        result = self.process(source)

        self.assertIn("CLASS QueueUsingStacks", result.processed_source)
        self.assertIn("PROPERTY stack1", result.processed_source)
        self.assertIn("PROPERTY stack2", result.processed_source)
        self.assertNotIn("PROPERTY stack1 AS LIST", result.processed_source)
        self.assertNotIn("PROPERTY stack2 AS LIST", result.processed_source)
        self.assertIn("PROPERTY THIS.stack1 <- CALL create_stack()", result.processed_source)
        self.assertIn("PROPERTY THIS.stack2 <- CALL create_stack()", result.processed_source)
        self.assertIn("CALL PUSH(item, THIS.stack1)", result.processed_source)
        self.assertIn(
            "CALL PUSH(CALL POP(THIS.stack1), THIS.stack2)",
            result.processed_source,
        )
        self.assertIn("RETURN CALL POP(THIS.stack2)", result.processed_source)
        self.assertNotIn("stack1_pop", result.processed_source)
        self.assertNotIn("stack2_push", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("class QueueUsingStacks:", compiled.source_code)
        self.assertIn("self.stack1 = []", compiled.source_code)
        self.assertIn("self.stack2 = []", compiled.source_code)
        self.assertIn("self.stack1.append(item)", compiled.source_code)
        self.assertIn("temp = self.stack1.pop(-1)", compiled.source_code)
        self.assertIn("self.stack2.append(temp)", compiled.source_code)
        self.assertIn("return self.stack2.pop(-1)", compiled.source_code)

    def test_nqueens_shared_matrix_assignment_and_copy(self):
        source = """FUNCTION solveNQueens ACCEPTS(N)
    board <- 2D array of size NxN initialized to 0
    solutions <- EMPTY LIST

    FUNCTION isSafe ACCEPTS(board, row, col)
        FOR i <- IN RANGE 0 TO row-1 DO
            IF board[i][col] == 1 THEN
                RETURN BOOLEAN(False)
            ENDIF
        ENDFOR
        i <- row - 1, j = col - 1
        WHILE i >= 0 AND j >= 0 DO
            IF board[i][j] == 1 THEN
                RETURN BOOLEAN(False)
            ENDIF
            i <- i - 1, j = j - 1
        ENDWHILE
        i <- row - 1, j = col + 1
        WHILE i >= 0 AND j < N DO
            IF board[i][j] == 1 THEN
                RETURN BOOLEAN(False)
            ENDIF
            i <- i - 1, j = j + 1
        ENDWHILE
        RETURN BOOLEAN(True)
    ENDFUNCTION

    FUNCTION placeQueen ACCEPTS(board, row)
        IF row == N THEN
            APPEND copy of board TO solutions
            RETURN
        ENDIF
        FOR col <- IN RANGE 0 TO N-1 DO
            IF CALL isSafe(board, row, col) THEN
                board[row][col] = 1
                CALL placeQueen(board, row + 1)
                board[row][col] = 0 // Backtrack
            ENDIF
        ENDFOR
    ENDFUNCTION

    CALL placeQueen(board, 0)
    RETURN solutions
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("board <- CALL create_matrix(N, N, 0)", result.processed_source)
        self.assertIn("board[row][col] <- 1", result.processed_source)
        self.assertIn("board[row][col] <- 0", result.processed_source)
        self.assertIn(
            "APPEND CALL copy_value(board) TO solutions",
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("board = [[0 for _ in range(N)] for _ in range(N)]", compiled.source_code)
        self.assertIn(
            "solutions.append(__import__('copy').deepcopy(board))",
            compiled.source_code,
        )

    def test_shared_append_tuple_literal(self):
        source = """FUNCTION findPairs ACCEPTS(arr, target)
    seen <- EMPTY SET
    result <- EMPTY LIST
    FOR EACH num IN arr DO
        complement <- target - num
        IF complement IN seen THEN
            CALL result_append((num, complement))
        ENDIF
        ADD num TO seen
    ENDFOR
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("APPEND TUPLE(num, complement) TO result", result.processed_source)
        self.assertNotIn("result_append", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("result.append((num, complement))", compiled.source_code)

        grouped = """FUNCTION grouped ACCEPTS(a, b)
    x <- (a + b) * 2
    RETURN x
ENDFUNCTION
"""
        grouped_result = self.process(grouped)
        self.assertIn("x <- (a + b) * 2", grouped_result.processed_source)

    def test_shared_matrix_allocation_without_explicit_fill(self):
        source = """FUNCTION addMatrices ACCEPTS(A, B, rows, cols)
    result <- matrix of size rows x cols
    FOR i <- IN RANGE 0 TO rows-1 DO
        FOR j <- IN RANGE 0 TO cols-1 DO
            result[i][j] = A[i][j] + B[i][j]
        ENDFOR
    ENDFOR
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            "result <- CALL create_matrix(rows, cols, NONE)",
            result.processed_source,
        )
        self.assertIn(
            "result[i][j] <- A[i][j] + B[i][j]",
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn(
            "result = [[None for _ in range(cols)] for _ in range(rows)]",
            compiled.source_code,
        )
        self.assertIn(
            "result[i][j] = (A[i][j] + B[i][j])",
            compiled.source_code,
        )

    def test_shared_matrix_initialised_with_wording(self):
        source = """FUNCTION multiplyMatrices ACCEPTS(A, B, rowsA, colsA, colsB)
    COMMENT Assumes A is rowsA x colsA, B is colsA x colsB
    result <- matrix of size rowsA x colsB initialized with 0
    FOR i <- IN RANGE 0 TO rowsA-1 DO
        FOR j <- IN RANGE 0 TO colsB-1 DO
            sum <- 0
            FOR k <- IN RANGE 0 TO colsA-1 DO
                sum <- sum + A[i][k] * B[k][j]
            ENDFOR
            result[i][j] = sum
        ENDFOR
    ENDFOR
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            "result <- CALL create_matrix(rowsA, colsB, 0)",
            result.processed_source,
        )
        self.assertIn("result[i][j] <- sum", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn(
            "result = [[0 for _ in range(colsB)] for _ in range(rowsA)]",
            compiled.source_code,
        )
        self.assertIn("result[i][j] = sum", compiled.source_code)

    def test_shared_transaction_item_id_and_quantity_remain_identifiers_without_gc146_evidence(self):
        source = """FUNCTION updateInventory ACCEPTS(inventory, transactions)
    FOR EACH transaction IN transactions DO
        itemID <- transaction_itemID
        quantityChange <- transaction_quantity // positive for delivery, negative for purchase
        IF itemID IN inventory THEN
            inventory[itemID] <- inventory[itemID] + quantityChange
        ELSE
            COMMENT Handle new item, maybe set initial stock
            inventory[itemID] <- quantityChange
        ENDIF
    ENDFOR
    COMMENT Ensure no negative inventory (adjust accordingly)
    FOR EACH item IN inventory DO
        IF inventory[item] < 0 THEN
            inventory[item] <- 0 // or raise error
        ENDIF
    ENDFOR
    RETURN inventory
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("itemID <- transaction_itemID", result.processed_source)
        self.assertIn("quantityChange <- transaction_quantity", result.processed_source)
        self.assertNotIn("transaction.itemID", result.processed_source)
        self.assertNotIn("transaction.quantity", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("transaction_itemID", parsed.error)
        self.assertIn("read before declaration or assignment", parsed.error)

    def test_shared_maze_bfs_does_not_invent_bounds_or_wall_convention(self):
        source = """FUNCTION findPath ACCEPTS(maze, start, end)
    queue <- EMPTY QUEUE
    visited <- 2D boolean array same size as maze initialized to BOOLEAN(False)
    parent <- 2D array to store previous cell for reconstruction
    ENQUEUE start TO queue
    visited[start_row][start_col] = BOOLEAN(True)
    directions <- [(0,1), (1,0), (0,-1), (-1,0)]
    WHILE queue IS NOT empty DO
        current <- DEQUEUE FROM queue
        FOR EACH direction IN directions DO
            newRow <- current_row + direction_row
            newCol <- current_col + direction_col
            IF newRow, newCol are within bounds AND maze[newRow][newCol] is not blocked AND visited[newRow][newCol] == BOOLEAN(False) THEN
                visited[newRow][newCol] = BOOLEAN(True)
            ENDIF
        ENDFOR
    ENDWHILE
    RETURN NULL
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("are within bounds", result.processed_source)
        self.assertIn("is not blocked", result.processed_source)
        self.assertNotIn("CALL is_traversable", result.processed_source)
        self.assertNotIn("newRow >= 0", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)

    def test_shared_other_element_object_semantics_are_not_inferred_without_dependency_evidence(self):
        source = """FUNCTION updateDronePositions ACCEPTS(drones)
    FOR EACH drone IN drones DO
        proposedPosition <- drone_position + drone_velocity
        FOR EACH otherDrone IN drones DO
            IF CALL distance(proposedPosition, otherDrone_position) < safeDistance THEN
                drone_velocity <- CALL calculateSafeVelocity(drone_position, otherDrone_position, drone_destination)
                proposedPosition <- drone_position + drone_velocity
                break
            ENDIF
        ENDFOR
        drone_position <- proposedPosition
    ENDFOR
    RETURN drones
ENDFUNCTION
"""
        result = self.process(source)

        # v2.88 deliberately stops before the historical object-semantics
        # recovery.  The source does not define/import distance or
        # calculateSafeVelocity and does not state that underscored names are
        # drone/otherDrone properties, so the compatibility layer must not
        # manufacture those bindings or a self-comparison guard.
        self.assertIn("proposedPosition <- drone_position + drone_velocity", result.processed_source)
        self.assertIn("otherDrone_position", result.processed_source)
        self.assertIn("drone_destination", result.processed_source)
        self.assertIn("drone_position <- proposedPosition", result.processed_source)
        self.assertNotIn("drone.position", result.processed_source)
        self.assertNotIn("drone.velocity", result.processed_source)
        self.assertNotIn("otherDrone.position", result.processed_source)
        self.assertNotIn("drone.destination", result.processed_source)
        self.assertNotIn("IF otherDrone != drone THEN", result.processed_source)
        self.assertNotIn("FUNCTION distance", result.processed_source)
        self.assertNotIn("FUNCTION calculateSafeVelocity", result.processed_source)

    def test_shared_decimal_to_binary_arithmetic_calls(self):
        source = """FUNCTION DECIMAL_TO_BINARY ACCEPTS(n)
    IF n == 0 THEN
        RETURN STRING("0")
    ENDIF
    binary <- EMPTY STRING
    WHILE n > 0 DO
        binary <- CALL MODULUS(n, 2) + binary
        n <- CALL FLOOR(n / 2)
    ENDWHILE
    RETURN binary
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            "binary <- (n MODULUS 2) + binary",
            result.processed_source,
        )
        self.assertNotIn("CALL to_string", result.processed_source)
        self.assertIn(
            "n <- (n INTEGER DIVISION 2)",
            result.processed_source,
        )
        self.assertNotIn("CALL MODULUS", result.processed_source)
        self.assertNotIn("CALL FLOOR", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("binary = ((n % 2) + binary)", compiled.source_code)
        self.assertIn("n = (n // 2)", compiled.source_code)

    def test_shared_boolean_operator_calls(self):
        source = """FUNCTION IS_LEAP_YEAR ACCEPTS(year)
    IF year MODULUS 4 == 0 CALL AND (year MODULUS 100 != 0 OR year MODULUS 400 == 0) THEN
        RETURN BOOLEAN(True)
    ELSE
        RETURN BOOLEAN(False)
    ENDIF
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn(
            "IF year MODULUS 4 == 0 AND (year MODULUS 100 != 0 OR year MODULUS 400 == 0) THEN",
            result.processed_source,
        )
        self.assertNotIn("CALL AND", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("and", compiled.source_code)
        self.assertIn("or", compiled.source_code)

    def test_shared_list_self_concat_singleton_to_append(self):
        source = """FUNCTION INTERSECTION ACCEPTS(arr1, arr2)
    i <- 0
    j <- 0
    intersection <- EMPTY LIST
    WHILE i < LENGTH OF arr1 AND j < LENGTH OF arr2 DO
        IF arr1[i] == arr2[j] THEN
            intersection <- intersection + [arr1[i]]
            i <- i + 1
            j <- j + 1
        ELSE IF arr1[i] < arr2[j] THEN
            i <- i + 1
        ELSE
            j <- j + 1
        ENDIF
    ENDWHILE
    RETURN intersection
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("APPEND arr1[i] TO intersection", result.processed_source)
        self.assertNotIn("intersection <- intersection + [arr1[i]]", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("intersection.append(arr1[i])", compiled.source_code)

    def test_reserved_function_identifier_and_number_of_characters(self):
        source = """FUNCTION LENGTH(s)
    RETURN NUMBER_OF_CHARACTERS(s)
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            "FUNCTION __reserved_keyword__LENGTH ACCEPTS(s)",
            result.processed_source,
        )
        self.assertIn("RETURN LENGTH OF s", result.processed_source)
        self.assertNotIn("NUMBER_OF_CHARACTERS", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn(
            "def __reserved_keyword__LENGTH(s):",
            compiled.source_code,
        )
        self.assertIn("return len(s)", compiled.source_code)

    def test_shared_split_expression_call(self):
        source = """FUNCTION SPLIT_SENTENCE ACCEPTS(sentence)
    RETURN SPLIT(sentence, STRING(" "))
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            'RETURN CALL SPLIT(sentence, STRING(" "))',
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn(
            "return sentence.split(' ')",
            compiled.source_code,
        )

    def test_shared_list_literal_keyword_form(self):
        source = """FUNCTION COUNT_VOWELS ACCEPTS(text)
    vowels <- LIST [STRING("a"), STRING("e"), STRING("i"), STRING("o"), STRING("u")]
    counts <- EMPTY LIST
    FOR EACH v IN vowels DO
        count <- 0
        FOR EACH c IN text DO
            IF c == v THEN
                count <- count + 1
            ENDIF
        ENDFOR
        counts <- counts + [count]
    ENDFOR
    RETURN counts
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            'vowels <- CALL list_value(STRING("a"), STRING("e"), STRING("i"), STRING("o"), STRING("u"))',
            result.processed_source,
        )
        self.assertIn("APPEND count TO counts", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("vowels = ['a', 'e', 'i', 'o', 'u']", compiled.source_code)
        self.assertIn("counts.append(count)", compiled.source_code)

    def test_shared_return_list_literal(self):
        source = """FUNCTION SUM_AND_AVERAGE ACCEPTS(arr)
    sum <- 0
    FOR EACH num IN arr DO
        sum <- sum + num
    ENDFOR
    average <- sum / LENGTH OF arr
    RETURN [sum, average]
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            "RETURN CALL list_value(sum, average)",
            result.processed_source,
        )
        self.assertNotIn("RETURN [sum, average]", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("return [sum, average]", compiled.source_code)

    def test_shared_function_name_param_and_param(self):
        source = """FUNCTION SWAP a AND b
    a <- a + b
    b <- a - b
    a <- a - b
    RETURN [a, b]
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("FUNCTION SWAP ACCEPTS(a, b)", result.processed_source)
        self.assertIn("RETURN CALL list_value(a, b)", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("def SWAP(a, b):", compiled.source_code)
        self.assertIn("return [a, b]", compiled.source_code)

    def test_existing_list_rule_covers_find_divisors(self):
        source = """FUNCTION FIND_DIVISORS ACCEPTS(n)
    divisors <- EMPTY LIST
    FOR i <- IN RANGE 1 TO n DO
        IF n MODULUS i == 0 THEN
            divisors <- divisors + [i]
        ENDIF
    ENDFOR
    RETURN divisors
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("APPEND i TO divisors", result.processed_source)
        self.assertNotIn("divisors <- divisors + [i]", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("divisors.append(i)", compiled.source_code)

    def test_shared_is_a_number_predicate(self):
        source = """FUNCTION CHECK_PASSWORD ACCEPTS(password)
    IF LENGTH OF password < 8 THEN
        RETURN BOOLEAN(False)
    ENDIF
    has_number <- BOOLEAN(False)
    has_uppercase <- BOOLEAN(False)
    FOR EACH c IN password DO
        IF c IS A NUMBER THEN
            has_number <- BOOLEAN(True)
        ELSE IF CALL is_uppercase(c) THEN
            has_uppercase <- BOOLEAN(True)
        ENDIF
    ENDFOR
    IF has_number AND has_uppercase THEN
        RETURN BOOLEAN(True)
    ELSE
        RETURN BOOLEAN(False)
    ENDIF
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("IF CALL is_number(c) THEN", result.processed_source)
        self.assertNotIn("IS A NUMBER", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("c.isdigit()", compiled.source_code)

    def test_trailing_conversation_after_complete_algorithm_occurrence_source_e21(self):
        source = """FUNCTION IS_EVEN ACCEPTS(n)
    IF n MODULUS 2 == 0 THEN
        RETURN BOOLEAN(True)
    ELSE
        RETURN BOOLEAN(False)
    ENDIF
ENDFUNCTION
``

continue from 22

assistant

Here are the pseudocodes for the remaining tasks
"""
        result = self.process(source)
        self.assertIn("FUNCTION IS_EVEN ACCEPTS(n)", result.processed_source)
        self.assertIn("ENDFUNCTION", result.processed_source)
        self.assertNotIn("continue from 22", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_shared_empty_dictionary_braces(self):
        source = """FUNCTION LONGEST_SUBSTRING ACCEPTS(s)
    max_length <- 0
    start <- 0
    char_index <- {}
    FOR i <- IN RANGE 0 TO LENGTH OF s - 1 DO
        IF s[i] IN char_index AND char_index[s[i]] >= start THEN
            start <- char_index[s[i]] + 1
        ENDIF
        char_index[s[i]] = i
        max_length <- CALL max(max_length, i - start + 1)
    ENDFOR
    RETURN max_length
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("char_index <- EMPTY DICTIONARY", result.processed_source)
        self.assertIn("char_index[s[i]] <- i", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_shared_binary_tree_level_order_properties(self):
        source = """FUNCTION LEVEL_ORDER_TRAVERSAL ACCEPTS(root)
    result <- EMPTY LIST
    queue <- LIST [root]
    WHILE queue IS NOT EMPTY DO
        level <- EMPTY LIST
        FOR i <- IN RANGE 0 TO LENGTH OF queue - 1 DO
            node <- CALL DEQUEUE(queue)
            level <- level + [node_value]
            IF node_left IS NOT NULL THEN
                CALL ENQUEUE(queue, node_left)
            ENDIF
            IF node_right IS NOT NULL THEN
                CALL ENQUEUE(queue, node_right)
            ENDIF
        ENDFOR
        result <- result + [level]
    ENDWHILE
    RETURN result
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("APPEND node_value TO level", result.processed_source)
        self.assertIn("node_left != NULL", result.processed_source)
        self.assertIn("node_right != NULL", result.processed_source)
        self.assertIn("APPEND level TO result", result.processed_source)
        self.assertIn("REMOVE FIRST ITEM FROM queue", result.processed_source)
        self.assertIn("APPEND node_left TO queue", result.processed_source)
        self.assertIn("APPEND node_right TO queue", result.processed_source)
        self.assertNotIn("node.value", result.processed_source)
        self.assertNotIn("node.left", result.processed_source)
        self.assertNotIn("node.right", result.processed_source)

        # This historical fixture uses the flattened names only inside APPEND
        # values and compound conditions, which are outside the validator's
        # deliberately conservative direct bare-read subset.  The important
        # compatibility boundary is that the names remain identifiers rather
        # than being silently reinterpreted as node members.
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("level.append(node_value)", compiled.source_code)
        self.assertIn("queue.append(node_left)", compiled.source_code)
        self.assertIn("queue.append(node_right)", compiled.source_code)
        self.assertNotIn("node.value", compiled.source_code)

    def test_shared_midpoint_index_integer_division_and_example_trailing_content(self):
        source = """FUNCTION FIND_TARGET ACCEPTS(rotated_list, target)
    low <- 0
    high <- LENGTH OF rotated_list - 1
    WHILE low <= high DO
        mid <- (low + high) / 2
        IF rotated_list[mid] == target THEN
            RETURN mid
        ELSE IF rotated_list[low] <= rotated_list[mid] THEN
            IF target >= rotated_list[low] AND target < rotated_list[mid] THEN
                high <- mid - 1
            ELSE
                low <- mid + 1
            ENDIF
        ELSE
            IF target > rotated_list[mid] AND target <= rotated_list[high] THEN
                low <- mid + 1
            ELSE
                high <- mid - 1
            ENDIF
        ENDIF
    ENDWHILE
    RETURN -1
ENDFUNCTION

Example: `FIND

continue from 37
"""
        result = self.process(source)
        self.assertIn(
            "mid <- (low + high) INTEGER DIVISION 2",
            result.processed_source,
        )
        self.assertNotIn("Example:", result.processed_source)
        self.assertNotIn("continue from 37", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("mid = ((low + high) // 2)", compiled.source_code)

    def test_stack_constructor_marker_and_spaced_endclass(self):
        source = """CLASS STACK
  CALL Constructor()
    array <- EMPTY LIST
    top <- -1

  FUNCTION PUSH ACCEPTS(element)
    top <- top + 1
    array[top] <- element
  ENDFUNCTION

  FUNCTION POP ACCEPTS()
    IF top == -1 THEN
      RETURN NULL
    ENDIF
    element <- array[top]
    top <- top - 1
    RETURN element
  ENDFUNCTION

  FUNCTION PEEK ACCEPTS()
    IF top == -1 THEN
      RETURN NULL
    ENDIF
    RETURN array[top]
  ENDFUNCTION
END CLASS
"""
        result = self.process(source)

        self.assertIn("CLASS STACK ACCEPTS()", result.processed_source)
        self.assertNotIn("CALL Constructor()", result.processed_source)
        self.assertIn("ENDCLASS", result.processed_source)
        self.assertNotIn("END CLASS", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("class STACK:", compiled.source_code)
        self.assertIn("def __init__(self):", compiled.source_code)
        self.assertIn("self.array = []", compiled.source_code)
        self.assertIn("self.top = (-1)", compiled.source_code)

    def test_contextual_spaced_block_terminators(self):
        source = """FUNCTION sample ACCEPTS(x)
    IF x > 0 THEN
        WHILE x > 1 DO
            x <- x - 1
        END WHILE
    END IF
    RETURN x
END FUNCTION
"""
        result = self.process(source)

        self.assertIn("ENDWHILE", result.processed_source)
        self.assertIn("ENDIF", result.processed_source)
        self.assertIn("ENDFUNCTION", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_shared_floyd_tortoise_hare_flattened_names_remain_identifiers(self):
        source = """FUNCTION HAS_CYCLE ACCEPTS(head)
    tortoise <- head
    hare <- head
    WHILE tortoise != NULL AND hare != NULL AND hare_next != NULL DO
        tortoise <- tortoise_next
        hare <- hare_next.next
        IF tortoise == hare THEN
            RETURN BOOLEAN(True)
        ENDIF
    ENDWHILE
    RETURN BOOLEAN(False)
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("hare_next != NULL", result.processed_source)
        self.assertIn("tortoise <- tortoise_next", result.processed_source)
        self.assertIn("hare <- hare_next.next", result.processed_source)
        self.assertNotIn("tortoise <- tortoise.next", result.processed_source)
        self.assertNotIn("hare <- hare.next.next", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("Identifier 'tortoise_next' is read before declaration or assignment", parsed.error)

    def test_queue_using_two_stacks_push_spelling(self):
        source = """CLASS QUEUE
  stack1 <- EMPTY LIST
  stack2 <- EMPTY LIST

  FUNCTION ENQUEUE ACCEPTS(element)
    PUSH element TO stack1
  ENDFUNCTION

  FUNCTION DEQUEUE ACCEPTS()
    IF stack2 IS EMPTY THEN
      WHILE stack1 IS NOT EMPTY DO
        CALL stack2_push(CALL stack1_pop())
      ENDWHILE
    ENDIF
    RETURN CALL stack2_pop()
  ENDFUNCTION
END CLASS
"""
        result = self.process(source)
        self.assertIn("CLASS QUEUE", result.processed_source)
        self.assertIn("PROPERTY stack1 AS LIST", result.processed_source)
        self.assertIn("PROPERTY stack2 AS LIST", result.processed_source)
        self.assertIn("CONSTRUCTOR ACCEPTS()", result.processed_source)
        self.assertIn("APPEND element TO THIS.stack1", result.processed_source)
        self.assertIn("ENDCLASS", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("class QUEUE:", compiled.source_code)
        self.assertIn("self.stack1.append(element)", compiled.source_code)

    def test_collection_self_addition_append_and_extend_family(self):
        source = """FUNCTION FIND_FILE ACCEPTS(directory, file_type)
    files <- EMPTY LIST
    FOR EACH item IN directory DO
        IF CALL is_file(item) AND CALL item_endswith(file_type) THEN
            files <- files + [item]
        ELSE IF CALL is_directory(item) THEN
            files <- files + CALL FIND_FILE(item, file_type)
        ENDIF
    ENDFOR
    RETURN files
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("APPEND item TO files", result.processed_source)
        self.assertIn(
            "CALL extend_list(files, CALL FIND_FILE(item, file_type))",
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("files.append(item)", compiled.source_code)
        self.assertIn(
            "files.extend(FIND_FILE(item, file_type))",
            compiled.source_code,
        )

        audit = result.to_dict()
        self.assertEqual(audit["audit_schema"], "SEMANTIC_RULE_FAMILIES_V1")
        audit_text = result.to_json()
        self.assertNotIn('"rule": "GC', audit_text)
        self.assertNotIn("GC157", audit_text)
        self.assertNotIn("GC158", audit_text)

    def test_input_prompt_returning_scope_promotes_parameter(self):
        source = """WordList <- INPUT(STRING("Enter WordList"))
FOR i <- IN RANGE 0 TO LENGTH OF WordList-1 DO
    OUTPUT WordList[i]
ENDFOR
RETURN WordList
"""
        result = self.process(source)

        self.assertIn("FUNCTION unnamed_function ACCEPTS(WordList)", result.processed_source)
        self.assertNotIn('WordList <- INPUT(STRING("Enter WordList"))', result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        audit = result.to_dict()
        self.assertEqual(audit["audit_schema"], "SEMANTIC_RULE_FAMILIES_V1")

    def test_swap_indexed_targets_expands_to_three_assignments(self):
        source = """FUNCTION SORT_WORDS ACCEPTS(WordList)
    IF WordList[j] > WordList[j+1] THEN
        SWAP WordList[j], WordList[j+1]
    ENDIF
    RETURN WordList
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("temp_var <- WordList[j]", result.processed_source)
        self.assertIn("WordList[j] <- WordList[j+1]", result.processed_source)
        self.assertIn("WordList[j+1] <- temp_var", result.processed_source)
        self.assertNotIn("SWAP ", result.processed_source)
        self.assertNotIn("CALL swap", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("temp_var = WordList[j]", compiled.source_code)
        self.assertIn("WordList[j] = WordList[(j + 1)]", compiled.source_code)
        self.assertIn("WordList[(j + 1)] = temp_var", compiled.source_code)


    def test_source_a_algorithm_8_preserves_swap_and_inclusive_bounds(self):
        source = """INPUT WordList

FOR i <- 0 TO LENGTH(WordList)-2
    FOR j <- 0 TO LENGTH(WordList)-2-i
        IF WordList[j] > WordList[j+1] THEN
            SWAP WordList[j], WordList[j+1]
        ENDIF
    ENDFOR
ENDFOR

OUTPUT WordList
"""
        result = self.process(source)

        expected = """FUNCTION unnamed_function ACCEPTS(WordList)
    FOR i <- IN RANGE 0 TO (LENGTH OF WordList - 2) + 1 DO
        FOR j <- IN RANGE 0 TO (LENGTH OF WordList - 2 - i) + 1 DO
            IF WordList[j] > WordList[j + 1] THEN
                CALL swap(WordList, j, j + 1)
            ENDIF
        ENDFOR
    ENDFOR

    OUTPUT WordList
ENDFUNCTION"""
        self.assertEqual(result.processed_source.strip(), expected.strip())
        self.assertNotIn("temp_var", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)

        self.assertIn("def unnamed_function(WordList):", compiled.source_code)
        self.assertIn("for i in range(0, len(WordList) - 1):", compiled.source_code)
        self.assertIn("for j in range(0, len(WordList) - 1 - i):", compiled.source_code)
        self.assertIn("temp = WordList[j]", compiled.source_code)
        self.assertIn("WordList[j] = WordList[(j + 1)]", compiled.source_code)
        self.assertIn("WordList[(j + 1)] = temp", compiled.source_code)

    def test_output_scope_inputs_become_parameters_and_reserved_list_is_escaped(self):
        source = """List <- INPUT(STRING("Enter List"))
Target <- INPUT(STRING("Enter Target"))
Found <- BOOLEAN(False)
FOR i <- IN RANGE 0 TO LENGTH OF List-1 DO
    IF List[i] == Target THEN
        OUTPUT TUPLE(STRING("Found at position"), i)
        Found <- BOOLEAN(True)
        EXIT FOR
    ENDIF
ENDFOR
IF Found == BOOLEAN(False) THEN
    OUTPUT STRING("Target not found")
ENDIF
"""
        result = self.process(source)

        self.assertIn(
            "FUNCTION unnamed_function ACCEPTS(__reserved_keyword__List, Target)",
            result.processed_source,
        )
        self.assertNotIn("List <- INPUT", result.processed_source)
        self.assertNotIn("Target <- INPUT", result.processed_source)
        self.assertIn(
            "LENGTH OF __reserved_keyword__List",
            result.processed_source,
        )
        self.assertIn(
            "__reserved_keyword__List[i] == Target",
            result.processed_source,
        )
        self.assertIn("BREAK", result.processed_source)
        self.assertNotIn("RETURN ", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_case_block_rewrites_to_if_chain(self):
        source = """FUNCTION COUNT_VOWELS ACCEPTS(Text)
    A <- 0
    E <- 0
    I <- 0
    O <- 0
    U <- 0
    FOR EACH Character IN CALL lowercase(Text) DO
        CASE Character OF
            STRING("a"): A <- A + 1
            STRING("e"): E <- E + 1
            STRING("i"): I <- I + 1
            STRING("o"): O <- O + 1
            STRING("u"): U <- U + 1
        ENDCASE
    ENDFOR
    OUTPUT TUPLE(A, E, I, O, U)
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn('IF Character == STRING("a") THEN', result.processed_source)
        self.assertIn('ELSE IF Character == STRING("u") THEN', result.processed_source)
        self.assertNotIn("CASE Character OF", result.processed_source)
        self.assertNotIn("ENDCASE", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_anonymous_dictionary_resolves_from_unique_usage(self):
        source = """FUNCTION COUNT_FREQUENCY ACCEPTS(Text)
    CREATE EMPTY DICTIONARY
    FOR EACH Character IN Text DO
        IF Character IN Dictionary THEN
            Dictionary[Character] <- Dictionary[Character] + 1
        ELSE
            Dictionary[Character] <- 1
        ENDIF
    ENDFOR
    OUTPUT Dictionary
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn(
            "Dictionary <- EMPTY DICTIONARY",
            result.processed_source,
        )
        self.assertNotIn(
            "CREATE EMPTY DICTIONARY",
            result.processed_source,
        )

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_text_input_indexing_preserves_string_input(self):
        source = """Text <- INPUT(STRING("Enter Text"))
Reverse <- EMPTY STRING
FOR i <- IN RANGE LENGTH OF Text-1 TO (0) - 1 STEP -1 DO
    Reverse <- Reverse + Text[i]
ENDFOR
OUTPUT Reverse
"""
        result = self.process(source)
        self.assertIn(
            'FUNCTION unnamed_function ACCEPTS(Text)',
            result.processed_source,
        )
        self.assertNotIn('list_from_string', result.processed_source)
        self.assertNotIn('Text <- INPUT', result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_binary_tree_input_root_becomes_wrapper_dependency_without_lookup_abstraction(self):
        source = """BEGIN
    INPUT Root
    CREATE Empty Queue
    ENQUEUE Root
    WHILE Queue is not empty DO
        Node <- DEQUEUE Queue
        OUTPUT Node_Value
        IF Node_Left exists THEN
            ENQUEUE Node_Left
        ENDIF
        IF Node_Right exists THEN
            ENQUEUE Node_Right
        ENDIF
    ENDWHILE
END
"""
        result = self.process(source)

        self.assertIn("FUNCTION unnamed_function ACCEPTS(Root)", result.processed_source)
        self.assertIn("Queue <- CALL create_queue()", result.processed_source)
        self.assertIn("CALL ENQUEUE(Queue, Root)", result.processed_source)
        self.assertIn("Node <- CALL DEQUEUE(Queue)", result.processed_source)
        self.assertRegex(result.processed_source, r"OUTPUT (?i:Node_Value)")
        self.assertRegex(result.processed_source, r"IF (?i:Node_Left) exists THEN")
        self.assertRegex(result.processed_source, r"CALL ENQUEUE\(Queue, (?i:Node_Left)\)")
        self.assertRegex(result.processed_source, r"IF (?i:Node_Right) exists THEN")
        self.assertRegex(result.processed_source, r"CALL ENQUEUE\(Queue, (?i:Node_Right)\)")
        self.assertNotRegex(result.processed_source, r"(?i:Node\.(?:value|left|right))")
        self.assertNotIn("lookup_inferred_node", result.processed_source)
        self.assertNotIn("Root_Key", result.processed_source)
        self.assertNotIn("Anonymous_Queue", result.processed_source)
        self.assertNotIn("INPUT(STRING", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)

    def test_matrix_and_n_inputs_become_wrapper_parameters_without_conversion(self):
        source = """Matrix <- INPUT(STRING("Enter Matrix"))
N <- INPUT(STRING("Enter N"))

TRANSPOSE Matrix

FOR EACH Row IN Matrix DO
    REVERSE Row
ENDFOR

OUTPUT Matrix
"""
        result = self.process(source)

        self.assertIn("FUNCTION unnamed_function ACCEPTS(Matrix)", result.processed_source)
        self.assertIn("CALL transpose_in_place(Matrix)", result.processed_source)
        self.assertIn("CALL reverse_list(Row)", result.processed_source)
        self.assertNotIn("Matrix <- INPUT", result.processed_source)
        self.assertNotIn("N <- INPUT", result.processed_source)
        self.assertNotIn("list_from_string", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("def unnamed_function(Matrix):", compiled.source_code)

    def test_raw_source_a_algorithm_33_infers_integer_input_before_div_normalisation(self):
        source = """# Find the square root of a non-negative integer using binary search.
BEGIN
    INPUT Number

    Low ← 0
    High ← Number
    Answer ← 0

    WHILE Low ≤ High
        Mid ← (Low + High) DIV 2

        IF Mid × Mid = Number THEN
            OUTPUT Mid
            STOP
        ELSE IF Mid × Mid < Number THEN
            Answer ← Mid
            Low ← Mid + 1
        ELSE
            High ← Mid - 1
        ENDIF
    ENDWHILE

    OUTPUT Answer
END
"""
        result = self.process(source)
        self.assertIn(
            'FUNCTION unnamed_function ACCEPTS(Number)',
            result.processed_source,
        )
        self.assertNotIn('Number <- INPUT', result.processed_source)
        self.assertIn(
            'Mid <- (Low + High) INTEGER DIVISION 2',
            result.processed_source,
        )
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_raw_source_a_algorithm_36_stop_becomes_return_in_process_wrapper(self):
        source = """BEGIN
    INPUT Array, Target

    Low ← 0
    High ← LENGTH(Array) - 1

    WHILE Low ≤ High
        Mid ← (Low + High) DIV 2

        IF Array[Mid] = Target THEN
            OUTPUT Mid
            STOP
        ENDIF

        IF Array[Low] ≤ Array[Mid] THEN
            IF Target ≥ Array[Low] AND Target < Array[Mid] THEN
                High ← Mid - 1
            ELSE
                Low ← Mid + 1
            ENDIF
        ELSE
            IF Target > Array[Mid] AND Target ≤ Array[High] THEN
                Low ← Mid + 1
            ELSE
                High ← Mid - 1
            ENDIF
        ENDIF
    ENDWHILE

    OUTPUT "Not Found"
END
"""
        result = self.process(source)
        self.assertIn("FUNCTION unnamed_function ACCEPTS(Array, Target)", result.processed_source)
        self.assertIn("RETURN", result.processed_source)
        self.assertNotIn("STOP", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("return", compiled.source_code)
        self.assertNotIn("quit()", compiled.source_code)

    def test_numeric_input_type_inferred_from_integer_arithmetic(self):
        source = """Number <- INPUT(STRING("Enter Number"))
Low <- 0
High <- Number
Answer <- 0
WHILE Low <= High DO
    Mid <- (Low + High) INTEGER DIVISION 2
    IF Mid * Mid == Number THEN
        OUTPUT Mid
        STOP
    ELSE IF Mid * Mid < Number THEN
        Answer <- Mid
        Low <- Mid + 1
    ELSE
        High <- Mid - 1
    ENDIF
ENDWHILE
OUTPUT Answer
"""
        result = self.process(source)
        self.assertIn(
            'FUNCTION unnamed_function ACCEPTS(Number)',
            result.processed_source,
        )
        self.assertNotIn('Number <- INPUT', result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_source_a_algorithm_7_split_by_spaces_preserves_explicit_space_delimiter(self):
        source = """BEGIN
    INPUT Sentence

    Words <- SPLIT Sentence BY spaces

    OUTPUT Words
END
"""
        result = self.process(source)
        self.assertIn("FUNCTION unnamed_function ACCEPTS(Sentence)", result.processed_source)
        self.assertIn("Words <- CALL split_on_space(Sentence)", result.processed_source)
        self.assertNotIn("CALL split_words(Sentence)", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn('str(Sentence).split(" ")', compiled.source_code)
        self.assertNotIn('str(Sentence).split()', compiled.source_code)

    def test_split_words_helper_retains_generic_whitespace_semantics(self):
        source = """FUNCTION f ACCEPTS(Text)
    Words <- CALL split_words(Text)
    OUTPUT Words
ENDFUNCTION
"""
        parsed = AJParserFacade().parse(source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn('str(Text).split()', compiled.source_code)


if __name__ == '__main__':
    unittest.main()
