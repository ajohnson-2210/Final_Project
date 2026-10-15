# NL-FDEP v4.10 — AJ_24038155 Dialect v1.3 explicit casts and QUIT

## Scope

v4.10 advances the active language from AJ_24038155 Dialect v1.2 to **v1.3**. The change is intentionally narrow and was motivated by baseline algorithms whose supplied Python explicitly performs runtime primitive conversion and whole-program `quit()` termination.

## Language additions

### Explicit primitive runtime casts

Canonical v1.3 supports:

- `CALL INTEGER(expression)` -> Python `int(expression)`
- `CALL FLOAT(expression)` -> Python `float(expression)`
- `CALL STRING(expression)` -> Python `str(expression)`

The parser emits a dedicated `CastNode`. The preceding `CALL` distinguishes runtime conversion from the pre-existing typed-literal constructors such as `INTEGER(23)` and `STRING("text")`. Casts are never inserted implicitly.

### QUIT statement

Canonical v1.3 supports:

```text
QUIT
```

`QUIT` emits a dedicated `QuitNode`, is valid at top level or inside blocks, terminates the current program, lowers to Python `quit()`, and is terminal in the flow graph. It is deliberately distinct from function `RETURN`, loop `BREAK`, loop `CONTINUE`, and the older pipeline `STOP` compatibility surface.

## Reserved identifiers

`QUIT` is included in the existing source-proven reserved-identifier escape mechanism. If source binding syntax proves that `quit` is being used as a variable identifier, it is protected using the established `__reserved_keyword__...` convention. This does not alter standalone canonical `QUIT` syntax.

## Audit representation

The new constructs remain explicit through the study artefacts:

- `CastNode` preserves conversion target and operand;
- `QuitNode` preserves explicit program-termination intent;
- flow-diagram structured-program JSON retains those node kinds;
- semantic signatures and flow validation recognise `QUIT` as executable terminal control.

## Semantic boundary

v4.10 does not add runtime type inspection, implicit casts, substring operations, Boolean/CHAR casts, callbacks or first-class functions. Invalid explicit numeric conversion continues to raise a runtime error and may be caught by existing `TRY/CATCH` semantics.

See `docs/AJ_24038155_Dialect_v1_3.md` for the normative language delta.
