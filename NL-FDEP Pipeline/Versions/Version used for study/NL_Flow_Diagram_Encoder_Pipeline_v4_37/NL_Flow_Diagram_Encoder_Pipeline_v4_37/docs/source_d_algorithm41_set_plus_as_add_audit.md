# source_d Algorithm 41 — interpreting `set + {item}` as non-mutating ADD — audit note

## Audit question

source_d Algorithm 41 uses the recursive call:

```text
Backtrack(row + 1, cols + {col}, diag1 + {row - col}, diag2 + {row + col})
```

The question is whether the `+` tokens must be preserved as ordinary arithmetic/addition operators, which would make a direct Python set translation invalid, or whether the source supplies enough independent evidence to interpret each expression as a **non-mutating ADD/extension of a set by one element**.

This audit concludes that the latter interpretation is justified **only for the evidence-gated GC245 pattern**. It is not a general rule that `+` means set union or ADD.

## Source evidence

The same routine is invoked initially as:

```text
Backtrack(0, empty Set, empty Set, empty Set)
```

This explicitly supplies SET values to the formal-parameter positions `cols`, `diag1`, and `diag2`. Within that same `Backtrack` routine, those parameters are then used in membership tests:

```text
IF col IN cols OR (row - col) IN diag1 OR (row + col) IN diag2 THEN
    CONTINUE
END IF
```

The recursive call extends each of those same values with a brace expression containing exactly one element:

```text
cols + {col}
diag1 + {row - col}
diag2 + {row + col}
```

The source therefore provides converging evidence that:

1. `cols`, `diag1`, and `diag2` are SET-valued state;
2. `{col}`, `{row - col}`, and `{row + col}` are singleton SET values rather than dictionaries or multi-element collection literals;
3. the recursive call requires a new state value that contains the previous members plus the new singleton member;
4. the parent call must retain its original state for subsequent loop iterations, so the operation must be non-mutating;
5. no compensating removal operation appears after recursion, which is consistent with passing extended copies rather than mutating the existing sets.

Taken together, this is sufficient to interpret the source `+` as pseudocode shorthand for **ADD one element to a copy of the established set state**.

## Canonical interpretation

GC245 currently represents the non-mutating ADD using existing compatibility intrinsics rather than inventing a new AJ primitive:

```text
cols + {col}
```

becomes:

```text
CALL to_set(CALL to_list(cols) + CALL list_value(col))
```

and analogously:

```text
diag1 + {row - col}
```

becomes:

```text
CALL to_set(CALL to_list(diag1) + CALL list_value(row - col))
```

while:

```text
diag2 + {row + col}
```

becomes:

```text
CALL to_set(CALL to_list(diag2) + CALL list_value(row + col))
```

The arithmetic inside the singleton element (`row - col`, `row + col`) is preserved exactly. Only the collection-combination surface is interpreted.

## Python meaning

The compatibility representation lowers to behaviour equivalent to:

```python
Backtrack(
    row + 1,
    set(list(cols) + [col]),
    set(list(diag1) + [row - col]),
    set(list(diag2) + [row + col]),
)
```

This is semantically equivalent, for the evidenced set operands, to the clearer Python set-copy extensions:

```python
Backtrack(
    row + 1,
    cols | {col},
    diag1 | {row - col},
    diag2 | {row + col},
)
```

The second form is shown only as an explanatory equivalent. The pipeline does not need to rewrite the source to Python `|`, nor does this audit introduce a new compiler rule.

## Why this is not treated as an expected source failure

A direct Python reading of:

```python
cols + {col}
```

would raise a `TypeError`, because Python does not define `+` for sets. However, the input is pseudocode rather than Python, and the meaning of an operator may be established by the surrounding pseudocode semantics when the evidence is sufficiently specific.

Here, interpreting `+` as non-mutating set ADD does not repair an otherwise ambiguous arithmetic mistake. The source independently establishes both operands as SET values and uses singleton-brace extensions in exactly the recursive state positions required by the algorithm. The interpretation therefore recovers an explicit collection operation rather than inventing missing algorithmic logic.

This differs from cases such as ordinary `/` used as an invalid integer loop bound or numeric values concatenated directly with strings. In those cases, the source explicitly supplies a well-defined arithmetic/string operation whose runtime consequences are erroneous, so the pipeline must preserve the error. In source_d Algorithm 41, the operator's collection meaning is itself recoverable from the source context.

## Required refusal boundary

The interpretation must remain narrow. GC245 must **not** establish a general rule that `+` means ADD, union, or set extension.

It is justified only when all required evidence is present, including:

- the relevant formal parameter is independently evidenced as SET-backed by an explicit matching call position such as `EMPTY SET`;
- the evidence belongs to the same routine and the same parameter position;
- the right-hand brace expression contains exactly one member;
- the brace expression is not dictionary-shaped;
- the receiver is the evidenced parameter rather than an unrelated or member-qualified value;
- duplicate/ambiguous routine declarations do not make the caller-to-formal mapping uncertain.

Without that evidence, an expression such as:

```text
values + {item}
```

must remain uninterpreted rather than being silently converted into set ADD.

## Audit classification

**Accepted evidence-based normalisation — not an expected failure.**

For source_d Algorithm 41, `cols + {col}`, `diag1 + {row - col}`, and `diag2 + {row + col}` are interpreted as non-mutating ADD/extension of explicitly evidenced SET state. The decision is source-context-specific and does not license generic reinterpretation of `+` elsewhere in the corpus.
