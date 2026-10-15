# NL-FDEP v3.46 release record

## Scope

v3.46 implements the approved source_d Algorithm 41 evidenced 2D-array copy recovery while leaving frozen AJ_24038155 Dialect v1.1 unchanged.

## GC247 evidenced 2D list row copy

An exact free call of the form:

```text
Copy(board)
```

is recovered only when `board` is already evidenced as matrix-backed by a canonical direct assignment from `CALL create_matrix(...)` in the current lexical scope or a readable enclosing lexical scope. The AJ compatibility representation is:

```text
CALL copy_2d_list(board)
```

and deterministic Python lowering is:

```python
list(map(list, board))
```

This creates a new outer list and a new list for every matrix row, which preserves the source-required N-Queens solution snapshot while the live board continues to be mutated during backtracking. It is deliberately not a general deep-copy rule. Formal-parameter shadowing and later direct rebinds invalidate inherited matrix evidence; unproven values, member calls, wrong arities, comments and quoted text remain unchanged.

GC247 composes with GC245 singleton-set extension and GC246 square-grid allocation. source_d Algorithm 41 now parses, compiles and executes for representative N-Queens sizes without any dialect change.

## Validation

- targeted GC247/GC246 regression and refusal-boundary tests: 11 passed;
- full pytest suite: 783 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 783 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
