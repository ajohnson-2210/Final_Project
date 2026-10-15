# NL-FDEP v3.44 release record

## Scope

v3.44 implements the approved source_d Algorithm 41 non-mutating singleton-set extension recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC245 evidenced non-mutating singleton-set extension

When a canonical call to a routine explicitly supplies `EMPTY SET` at a formal-parameter position, GC245 may treat that formal as set-backed within that same routine. An exact source expression such as:

```text
cols + {col}
```

is represented as:

```text
CALL to_set(CALL to_list(cols) + CALL list_value(col))
```

The same rule preserves supplied arithmetic inside the singleton value, for example `diag1 + {row - col}` and `diag2 + {row + col}`. This constructs a new set and therefore preserves the recursive/backtracking source shape without mutating the original set or inventing any compensating removal operation.

The rule refuses multi-member braces, dictionary-shaped braces, parameters without explicit `EMPTY SET` call evidence, evidence from a different routine, duplicate/ambiguous routine declarations, and member-qualified receivers. No new set syntax, parser feature, compiler primitive or dialect rule is added.

source_d Algorithm 41 now advances past the three singleton-set expressions. Its next independent failure remains visible at `board = N x N grid initialized to 0`; v3.44 does not repair or reinterpret that allocation surface.

## Validation

- targeted GC245 regression/refusal-boundary tests: 5 passed;
- full pytest suite: 772 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 772 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
