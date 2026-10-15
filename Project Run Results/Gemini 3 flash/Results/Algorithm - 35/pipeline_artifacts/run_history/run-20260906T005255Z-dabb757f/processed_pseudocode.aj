CLASS LRUCache
    CONSTRUCTOR ACCEPTS(capacity)
        self.capacity <- capacity
        self.map <- EMPTY DICTIONARY
        self.doubly_linked_list <- empty DoublyLinkedList

    ENDCONSTRUCTOR
    METHOD Get ACCEPTS(key)
        IF key NOT IN self.map THEN
            RETURN -1
        ENDIF
        node <- self.map[key]
        self.doubly_linked_list.moveToHead(node)
        RETURN node.value

    ENDMETHOD
    METHOD Put ACCEPTS(key, value)
        IF key IN self.map THEN
            node <- self.map[key]
            node.value <- value
            self.doubly_linked_list.moveToHead(node)
        ELSE
            IF self.map~LENGTH >= self.capacity THEN
                tail_node <- self.doubly_linked_list.removeTail()
                REMOVE tail_node.key FROM self.map
            ENDIF
            new_node <- CALL CreateNode(key, value)
            self.doubly_linked_list.addToHead(new_node)
            self.map[key] <- new_node
        ENDIF
    ENDMETHOD
ENDCLASS