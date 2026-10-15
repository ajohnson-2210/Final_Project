# v3.92 — SWAP generated-temporary hygiene

v3.92 implements the approved audit clarification that `temp_var` in the compatibility lowering for `SWAP` is a placeholder/metavariable, not a fixed identifier that may overwrite source state.

## Change

The existing source abstraction remains:

```text
SWAP a AND b
SWAP a, b
```

and still lowers to the ordinary three-assignment exchange:

```text
<fresh_temp> <- a
a <- b
b <- <fresh_temp>
```

The compatibility layer now chooses `<fresh_temp>` deterministically from the `temp_var` family. It uses `temp_var` when that identifier is absent from the algorithm; otherwise it tries `temp_var_1`, `temp_var_2`, and so on until a source-fresh, non-keyword identifier is available.

This is identifier hygiene only. It does not add a new AJ grammar form, infer new algorithmic behaviour, or change the meaning of `SWAP`.

## Regression coverage

New tests verify that:

- an existing source variable named `temp_var` remains unchanged after a swap;
- already-used suffixes are skipped (`temp_var`, `temp_var_1` -> generated `temp_var_2`);
- both `SWAP a AND b` and `SWAP a, b` use the same fresh-name rule;
- the historical `temp_var` spelling is retained when it is genuinely free;
- compiled Python preserves both the swap result and pre-existing source temporary values.

## Validation

- pytest: 976 passed, 3 skipped, 5 subtests passed
- unittest: 323 passed, 1 skipped
- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`
- dialect change: none
- compiler change: none
- compatibility normaliser change: yes (generated identifier freshness only)
