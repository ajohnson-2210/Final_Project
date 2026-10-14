CLASS Node
    PROPERTY value
    PROPERTY left
    PROPERTY right
    CONSTRUCTOR ACCEPTS(value)
        PROPERTY THIS.value <- value
        PROPERTY THIS.left <- NONE
        PROPERTY THIS.right <- NONE
    ENDCONSTRUCTOR
    METHOD set_left ACCEPTS(node)
        PROPERTY THIS.left <- node
    ENDMETHOD
    METHOD set_right ACCEPTS(node)
        PROPERTY THIS.right <- node
    ENDMETHOD
ENDCLASS

FUNCTION levelOrderTraversal ACCEPTS(root)
    IF root == NONE THEN
        RETURN EMPTY LIST
    ENDIF
    depth <- LIST [root]
    results <- EMPTY LIST
    loop <- BOOLEAN(TRUE)
    WHILE loop DO
        level <- EMPTY LIST
        nextdepth <- EMPTY LIST
        index <- 0
        innerloop <- BOOLEAN(TRUE)
        WHILE innerloop DO
            TRY
                node <- depth[index]
                APPEND node.value TO level
                IF node.left != NONE THEN
                    APPEND node.left TO nextdepth
                ENDIF
                IF node.right != NONE THEN
                    APPEND node.right TO nextdepth
                ENDIF
                index <- index + 1
            CATCH
                innerloop <- BOOLEAN(FALSE)
            ENDTRY
        ENDWHILE
        APPEND level TO results
        depth <- nextdepth
        IF LENGTH OF depth == 0 THEN
            loop <- BOOLEAN(FALSE)
        ENDIF
    ENDWHILE
    RETURN results
ENDFUNCTION

root <- CALL Node(1)
root.set_left(CALL Node(2))
root.set_right(CALL Node(3))
root.left.set_left(CALL Node(4))
root.left.set_right(CALL Node(5))
OUTPUT STRING("Node Values Grouped by Depth")
index <- 0
loop <- BOOLEAN(TRUE)
WHILE loop DO
    TRY
        level <- CALL levelOrderTraversal(root)[index]
        OUTPUT STRING("Level {index}: {level}")
        index <- index + 1
    CATCH
        loop <- BOOLEAN(FALSE)
    ENDTRY
ENDWHILE