# Release v3.74 — AJ_24038155 Dialect v1.2 nested functions

## Summary

v3.74 advances the active language baseline from **AJ_24038155 Dialect v1.1** to **AJ_24038155 Dialect v1.2**.

The normative v1.2 delta is recorded in `docs/AJ_24038155_Dialect_v1_2.md`. The historical v1.1 delta file remains unchanged.

## AJ v1.2 language change

AJ v1.2 makes lexical nested/local `FUNCTION ... ENDFUNCTION` declarations canonical inside another function body.

Example:

```text
FUNCTION outer ACCEPTS(N)
    FUNCTION helper ACCEPTS(value)
        OUTPUT value
    ENDFUNCTION

    CALL helper(N)
ENDFUNCTION
```

The deterministic Python compiler preserves the lexical nesting:

```python
def outer(N):
    def helper(value):
        print(value)

    helper(N)
```

The compiler must not hoist the local helper to module scope.

Nested functions may recursively call themselves. Their lexical scope remains local to the enclosing function.

## Callback boundary

v1.2 adds declaration nesting only. It does **not** add callbacks, first-class function values, anonymous functions, function references, callable-value typing, function-value storage, or callback parameter semantics. Those remain reserved for a later dialect revision.

## GC170 Tower of Hanoi alignment

source_a Algorithm 43 supplies `INPUT N`, a nested `Hanoi(...)` helper, and a final `Hanoi(N, "A", "B", "C")` call.

Earlier GC170 flattened that structure and invented an interactive numeric input:

```text
N <- CALL integer_value(INPUT(STRING("Enter N")))
FUNCTION Hanoi ...
...
CALL Hanoi(...)
```

v3.74 now preserves the source scope under AJ v1.2:

```text
FUNCTION unnamed_function ACCEPTS(N)
    FUNCTION Hanoi ACCEPTS(Discs, Source, Auxiliary, Destination)
        ...
    ENDFUNCTION

    CALL Hanoi(N, STRING("A"), STRING("B"), STRING("C"))
ENDFUNCTION
```

Python therefore has the intended structure:

```python
def unnamed_function(N):
    def Hanoi(Discs, Source, Auxiliary, Destination):
        ...

    Hanoi(N, "A", "B", "C")
```

`N` remains externally supplied. GC170 no longer invents `input("Enter N")`, `int(...)`, or top-level scope for `Hanoi`.

The move output is represented with the existing canonical placeholder string:

```text
OUTPUT STRING("Move disk from {Source} to {Destination}")
```

and compiles to a Python f-string.

## Validation

- pytest: **910 passed, 3 skipped, 5 subtests passed**
- unittest: **306 passed, 1 skipped**
- AJ v1.1 historical SHA-256 remains: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 active SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`
