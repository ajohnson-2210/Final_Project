CLASS Node
    PROPERTY value
    PROPERTY next
    CONSTRUCTOR ACCEPTS(value)
        PROPERTY THIS.value <- value
        PROPERTY THIS.next <- NONE
    ENDCONSTRUCTOR
    METHOD set_next ACCEPTS(node)
        PROPERTY THIS.next <- node
    ENDMETHOD
ENDCLASS

CLASS LinkedList
    PROPERTY head
    PROPERTY tail
    PROPERTY nodes
    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.head <- NONE
        PROPERTY THIS.tail <- NONE
        PROPERTY THIS.nodes <- EMPTY LIST
        OUTPUT STRING("Linked List Created\n")
    ENDCONSTRUCTOR
    METHOD __reserved_keyword__append ACCEPTS(value)
        new_node <- CALL Node(value)
        OUTPUT STRING("Appended Value {value}")
        IF THIS.head == NONE THEN
            PROPERTY THIS.head <- new_node
            PROPERTY THIS.tail <- new_node
        ELSE
            THIS.tail.set_next(new_node)
            PROPERTY THIS.tail <- new_node
        ENDIF
        APPEND new_node TO THIS.nodes
    ENDMETHOD
    METHOD prepend ACCEPTS(value)
        OUTPUT STRING("Prepended Value {value} To The Front")
        new_node <- CALL Node(value)
        IF THIS.head == NONE THEN
            PROPERTY THIS.head <- new_node
            PROPERTY THIS.tail <- new_node
        ELSE
            new_node.set_next(THIS.head)
            PROPERTY THIS.head <- new_node
        ENDIF
        INSERT new_node INTO THIS.nodes AT 0
    ENDMETHOD
    METHOD insert_at ACCEPTS(index, value)
        OUTPUT STRING("Inserting Value {value} at Index {index}")
        IF index == 0 THEN
            THIS.prepend(value)
            RETURN
        ENDIF
        new_node <- CALL Node(value)
        temp <- THIS.head
        i <- 0
        WHILE temp != NONE AND ((i < (index - 1))) DO
            temp <- temp.next
            i <- i + 1
        ENDWHILE
        IF temp == NONE THEN
            OUTPUT STRING("Insert Failed: Index out of range")
            RETURN
        ENDIF
        new_node.set_next(temp.next)
        temp.set_next(new_node)
        IF new_node.next == NONE THEN
            PROPERTY THIS.tail <- new_node
        ENDIF
        INSERT new_node INTO THIS.nodes AT index
        OUTPUT STRING("Insert Successful: {value} Inserted at Index {index}")
    ENDMETHOD
    METHOD create_cycle ACCEPTS(start_index, end_index)
        OUTPUT STRING("\nCycle Created: Loop Start index {start_index} → End index  {end_index}")
        IF start_index < 0 OR end_index < 0 THEN
            OUTPUT STRING("Cycle Creation Failed: Invalid Index")
            RETURN
        ENDIF
        IF start_index >= LENGTH OF THIS.nodes OR end_index >= LENGTH OF THIS.nodes THEN
            OUTPUT STRING("Cycle Creation Failed: Index Out Of Range")
            RETURN
        ENDIF
        start_node <- THIS.nodes[start_index]
        end_node <- THIS.nodes[end_index]
        end_node.set_next(start_node)
        OUTPUT STRING("\nCycle Created: Node {start_index} now points to node {end_index}")
    ENDMETHOD
    METHOD remove_cycle ACCEPTS()
        OUTPUT STRING("Remove Cycle Requested")
        slow <- THIS.head
        fast <- THIS.head
        cycle_found <- BOOLEAN(FALSE)
        WHILE (fast) AND (fast.next) DO
            slow <- slow.next
            fast <- fast.next.next
            IF slow == fast THEN
                cycle_found <- BOOLEAN(TRUE)
                OUTPUT STRING("Cycle Detected: Proceeding with Removal")
                BREAK
            ENDIF
        ENDWHILE
        IF NOT cycle_found THEN
            OUTPUT STRING("No cycle found — nothing to remove")
            RETURN
        ENDIF
        slow <- THIS.head
        WHILE slow != fast DO
            slow <- slow.next
            fast <- fast.next
        ENDWHILE
        cycle_start <- slow
        temp <- cycle_start
        WHILE temp.next != cycle_start DO
            temp <- temp.next
        ENDWHILE
        temp.set_next(NONE)
        PROPERTY THIS.tail <- THIS.nodes[-1]
        cycle_start_value <- cycle_start.value
        OUTPUT STRING("Cycle Removed Successfully: Loop started at Node with Value {cycle_start_value}")
    ENDMETHOD
    METHOD loop_diagram ACCEPTS()
        OUTPUT STRING("\nGenerating Loop Diagram...\n")
        nodes <- THIS.nodes
        visited <- EMPTY DICTIONARY
        temp <- THIS.head
        index <- 0
        cycle_start <- -1
        cycle_end <- -1
        WHILE temp != NONE DO
            IF temp IN visited THEN
                cycle_start <- visited[temp]
                cycle_end <- index - 1
                BREAK
            ENDIF
            visited[temp] <- index
            temp <- temp.next
            index <- index + 1
        ENDWHILE
        parts <- EMPTY LIST
        FOR EACH node IN nodes DO
            APPEND CALL STRING(node.value) TO parts
        ENDFOR
                sep <- STRING(" → ")
        chain <- JOIN(parts, sep)
        OUTPUT chain
        IF cycle_start == -1 THEN
            OUTPUT STRING("No Cycle Detected\n")
            RETURN
        ENDIF
        start_char <- 0
        FOR EACH i IN CALL range(cycle_start) DO
            start_char <- start_char + (LENGTH OF parts[i] + LENGTH OF sep)
        ENDFOR
                start_center <- start_char + (LENGTH OF parts[cycle_start] INTEGER DIVISION 2)
        end_char <- 0
        FOR EACH i IN CALL range(cycle_end) DO
            end_char <- end_char + (LENGTH OF parts[i] + LENGTH OF sep)
        ENDFOR
                end_center <- end_char + (LENGTH OF parts[cycle_end] INTEGER DIVISION 2)
        connector <- EMPTY STRING
        i <- 0
        WHILE i < start_center DO
            connector <- connector + STRING(" ")
            i <- i + 1
        ENDWHILE
        connector <- connector + STRING("└")
        dash_count <- (end_center - start_center) - 1
        i <- 0
        WHILE i < dash_count DO
            connector <- connector + STRING("─")
            i <- i + 1
        ENDWHILE
        connector <- connector + STRING("┘")
        OUTPUT connector
        OUTPUT STRING("Cycle Detected From Node {cycle_start} to Node {cycle_end}\n")
    ENDMETHOD
ENDCLASS

OUTPUT STRING("Detect Cycle in Singly Linked List\n")
l <- CALL LinkedList()
l.__reserved_keyword__append(10)
l.__reserved_keyword__append(20)
l.__reserved_keyword__append(30)
l.__reserved_keyword__append(40)
l.__reserved_keyword__append(50)
l.__reserved_keyword__append(60)
l.loop_diagram()
l.remove_cycle()
l.loop_diagram()
l.__reserved_keyword__append(40)
l.__reserved_keyword__append(50)
l.create_cycle(1, 6)
l.loop_diagram()
l.remove_cycle()
OUTPUT STRING("\nAfter Removing Cycle:")
l.loop_diagram()