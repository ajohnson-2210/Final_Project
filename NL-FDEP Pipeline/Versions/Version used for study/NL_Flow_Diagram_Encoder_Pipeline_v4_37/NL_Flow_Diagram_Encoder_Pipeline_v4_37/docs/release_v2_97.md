# NL-FDEP v2.97 release record

## Scope

v2.97 fixes ordinary member-access compilation so canonical AJ identifier case is preserved exactly in generated Python. The compiler no longer lower-cases `MemberAccessNode.member`.

No source-specific normalisation rule was added.

## source_c 47 classification

```text
status: PASS AFTER CASE-PRESERVING MEMBER-ACCESS COMPILATION
semantic inference: NO
algorithmic reconstruction: NO
source logic correction: NO
compiler correctness fix: YES
dialect change: NO
```

## Regression evidence

- Exact source_c 47 occurrence preserves `transaction.itemID`, parses, compiles and executes correctly.
- Generic `record.itemID`, `record.ItemID` and `record.itemid` remain distinct.
- Assignment-expression member access preserves case.
- Member method call spelling remains preserved.
- Resolved dictionary `GET` remains intentionally lowered to Python `.get(...)`.
- Legacy assertions that expected compiler-created lower-case aliases were corrected to the case-sensitive canonical AJ spelling.

## Validation

Working tree:

```text
pytest: 431 passed, 3 skipped, 5 subtests passed
unittest: 255 passed, 1 skipped
```

Fresh extraction of the packaged ZIP:

```text
pytest: 431 passed, 3 skipped, 5 subtests passed
unittest: 255 passed, 1 skipped
AJ v1.1 SHA-256: 0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598
```
