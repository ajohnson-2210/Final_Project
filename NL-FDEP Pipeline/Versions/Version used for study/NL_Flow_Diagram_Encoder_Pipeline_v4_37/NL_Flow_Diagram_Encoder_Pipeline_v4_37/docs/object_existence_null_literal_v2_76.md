# Object-existence NULL literal correction — v2.76

## Scope

This change applies to binary-tree queue traversal source phrases of the form:

    Node.Left exists
    Node.Right exists

The compatibility layer already interprets these as null-reference existence guards. v2.76 corrects their canonical AJ rendering so that the AJ NULL literal remains explicit rather than being fabricated as a zero-argument call.

## Canonical rule

    Node.Left exists  ->  Node.Left != NULL
    Node.Right exists ->  Node.Right != NULL

`CALL NULL()` is not emitted for these existence predicates.

The Python compiler already has contextual NULL-comparison lowering, so canonical comparisons compile as:

    Node.left is not None
    Node.right is not None

This is a representational correction only. Queue mechanics, tree traversal order, object-property access, and algorithmic control flow are unchanged.
