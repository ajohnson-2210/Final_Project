# v3.93 — Python compiler generated-temporary hygiene

v3.93 extends the approved generated-identifier hygiene rule from canonical `SWAP` normalisation to compiler-only Python temporaries used by destructive primitives.

## Change

The affected explicit source abstractions are unchanged:

```text
CALL PUSH(CALL POP(source), target)
CALL ENQUEUE(target, CALL DEQUEUE(source))
CALL swap(collection, left_index, right_index)
```

Their Python lowering may require a temporary to preserve destructive evaluation order. That temporary is compiler implementation state, not source state, and must therefore never capture or overwrite a source-authored identifier.

The compiler now chooses a deterministic fresh Python identifier from the `temp` family. It retains `temp` when free; otherwise it selects `temp_1`, `temp_2`, and so on until the name is absent from the structured source identifier set and is not a Python reserved word.

For example, source containing parameters `temp` and `temp_1` causes a nested stack transfer to lower through `temp_2` rather than overwriting either parameter.

This is identifier hygiene only. It does not change PUSH/POP, ENQUEUE/DEQUEUE, or indexed SWAP semantics and does not add an AJ grammar form.

## Regression coverage

New tests verify that:

- nested `PUSH(POP(...), ...)` skips source parameters named `temp` and `temp_1`;
- nested `ENQUEUE(..., DEQUEUE(...))` preserves an existing source `temp` value;
- indexed `swap(collection, left, right)` preserves an existing source `temp` value;
- generated suffixes are deterministic;
- the historical `temp` spelling is retained when it is genuinely free;
- the generated Python executes with the expected transfer/swap result and unchanged source temporaries.

## Validation

- pytest: 980 passed, 3 skipped, 5 subtests passed
- unittest: 327 passed, 1 skipped
- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`
- dialect change: none
- compiler change: yes (generated identifier freshness only)
- compatibility normaliser change: none
