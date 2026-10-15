# Bare RETURN ERROR string-sentinel representation — v3.01

## Rule

A bare error sentinel used exactly as a return value:

```text
RETURN ERROR
```

is a compatibility surface for the literal AJ string return:

```text
RETURN STRING("ERROR")
```

The transformation is recorded as `GC204`.

## Boundary

This is deliberately **return-position only**. It does not create a global `ERROR` constant and does not infer exception semantics.

Therefore the following are not covered by GC204:

```text
status <- ERROR
RETURN ERROR_CODE
object.ERROR
```

An unbound `ERROR` used outside the approved return-sentinel position remains subject to the normal AJ binding/static-semantic rules.

## Python lowering

The existing compiler lowers:

```text
RETURN STRING("ERROR")
```

to a returned Python string equivalent to:

```python
return "ERROR"
```

No exception type, message, output statement, or control-flow change is invented.

## Semantic classification

- representation recovery: YES
- semantic inference: NO beyond the explicitly approved sentinel representation
- exception inference: NO
- algorithmic reconstruction: NO
- dialect change: NO
