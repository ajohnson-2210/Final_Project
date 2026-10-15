# Case-preserving member-access compilation — v2.97

## Problem

Canonical AJ identifiers are case-sensitive, while keywords are case-insensitive. The Python compiler nevertheless lower-cased ordinary `MemberAccessNode` member names. This changed identifiers during compilation, e.g.:

```text
transaction.itemID
```

became:

```python
transaction.itemid
```

That can change program meaning or raise `AttributeError` when the object exposes the case-sensitive member written in the source.

## v2.97 rule

Ordinary member-access identifiers are emitted exactly as represented in canonical AJ:

```text
object.memberName
```

becomes:

```python
object.memberName
```

No case-folding is performed.

This is a compiler correctness rule, not a normalisation inference. It is independent of corpus, file, algorithm, receiver name and member name.

## Boundaries

- `record.itemID`, `record.ItemID` and `record.itemid` remain distinct.
- Member method calls already preserve their spelling and remain unchanged.
- Resolved AJ/Python intrinsics may still have deliberate compatibility lowering. For example, dictionary `values.GET(key, default)` compiles to Python `values.get(key, default)` because `GET` is resolved as the dictionary intrinsic rather than an ordinary member identifier.
- No property-name equivalence is inferred.
- AJ_24038155 Dialect v1.1 is unchanged.
