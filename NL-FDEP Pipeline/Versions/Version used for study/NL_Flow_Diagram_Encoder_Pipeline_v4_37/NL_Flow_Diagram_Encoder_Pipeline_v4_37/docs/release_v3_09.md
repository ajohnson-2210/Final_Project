# NL-FDEP v3.09 release record

## Scope

v3.09 records the approved one-off source_f Algorithm 15 research-corpus transcription correction from `-?` to `-infinity`.

## Production changes

**None.**

No normaliser, parser, compiler, corpus adapter, runtime mapping, or dialect production behaviour is changed. The corrected occurrence reuses existing GC151 negative-infinity handling.

## source_f Algorithm 15

Corrected corpus initialisers:

```text
first = -infinity
second = -infinity
```

canonicalise through existing rules to:

```text
first <- CALL negative_infinity()
second <- CALL negative_infinity()
```

and Python:

```python
first = float('-inf')
second = float('-inf')
```

The lossy `-?` spelling remains invalid outside separately evidenced corpus correction.

## Audit boundary

- one-off corpus transcription correction: **YES**
- generic `-?` alias introduced: **NO**
- semantic inference by pipeline: **NO**
- algorithmic reconstruction: **NO**
- dialect change: **NO**

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **551 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **551 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
