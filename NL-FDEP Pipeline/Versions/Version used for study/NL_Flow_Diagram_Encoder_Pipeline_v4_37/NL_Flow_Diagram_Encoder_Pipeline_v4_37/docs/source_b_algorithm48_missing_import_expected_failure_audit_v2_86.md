# source_b Algorithm 48 — missing import/definition expected-failure audit — v2.86

## Study occurrence

source_b Algorithm 48 supplies this recursive file-search response:

```text
FUNCTION findFilesByType(folder, targetExtension):
    results ← []
    FOR each item IN folder.contents:
        IF item is a file AND item.extension == targetExtension THEN
            APPEND item.path TO results
        ELSE IF item is a folder THEN
            results ← results + findFilesByType(item, targetExtension)
    RETURN results
```

The recursion, collection accumulation, and property accesses are explicit. The branch-driving environmental predicates `item is a file` and `item is a folder` are not executable routines in the supplied response.

## Audit classification

**EXPECTED FAIL — MISSING IMPORT / DEFINITION FOR ENVIRONMENTAL FILE-TYPE PREDICATES**

The source provides no dependency evidence establishing how the file/folder tests are evaluated:

- no import statement identifying or binding the required predicate routines;
- no explicit `is_file` / `is_directory` function definition;
- no explicit v1.1 member call such as `item.is_file()` / `item.is_directory()`; and
- no other runtime binding for the predicates.

The audit does not claim that a particular library such as `os.path` or `pathlib` is missing. The source does not identify which filesystem representation or API was intended. What is missing is an import or definition that supplies the required executable predicate semantics.

## v2.85 false-pass behaviour

Before v2.86, the general GC104 predicate conversion could rename the descriptive conditions to:

```text
CALL is_file(item)
CALL is_directory(item)
```

That produced syntactically compilable Python containing calls to undefined names. Execution therefore failed with `NameError` unless an external environment happened to inject those helpers.

Renaming an undefined environmental predicate is not semantic recovery. It hides the missing dependency and creates a false pass.

## v2.86 measure

v2.86 generalises the existing semantic-integrity guard so it is independent of model, function name, wrapper style, and surrounding algorithm.

Any descriptive condition matching the family:

```text
X is a file
X is a folder
X is a directory
```

is prevented from reaching the GC104 free-helper conversion unless the supplied source contains executable evidence for the exact helper dependency required by that conversion.

For the historical free-call mapping this means:

- file predicate -> exact `is_file` helper is defined or explicitly imported;
- folder/directory predicate -> exact `is_directory` helper is defined or explicitly imported.

If either required dependency is absent, the descriptive predicate remains visible and strict AJ parsing fails as expected.

Explicit AJ v1.1 member calls such as `entry.is_file()` are not descriptive predicates and are unaffected.

## Non-invention guarantees

The compatibility layer must not silently choose or fabricate any of the following on the source's behalf:

```text
os.path.isfile(...)
pathlib.Path(...).is_file()
is_file(...)
is_directory(...)
```

unless the executable dependency is supplied by the source under the existing recovery boundary.

## Regression evidence

`tests/test_source_b_algorithm48_missing_import_expected_failure_v2_86.py` retains the exact motivating study occurrence and verifies:

1. the source_b source remains an expected parse failure;
2. `is_file` / `is_directory` calls are not invented;
3. no `os.path` or `pathlib` implementation is selected;
4. the guard also applies to a differently shaped synthetic source;
5. explicit definitions of both exact helpers allow the existing conversion;
6. explicit AJ v1.1 member calls remain valid;
7. explicit imports of both exact helpers count as dependency evidence at the guard boundary; and
8. partial import evidence does not hide a still-missing predicate dependency.

## Dialect status

AJ_24038155 Dialect v1.1 is frozen. v2.86 makes no dialect change.

## Cross-corpus generalisation check

The guard is not a source_b-specific measure. During the same audit, equivalent descriptive file/folder predicates were confirmed in separate source_a, source_e, and source_c study outputs. These occurrences use different wrappers and surrounding operations, yet must receive the same expected-failure treatment when no executable dependency is supplied.

Accordingly, source_b Algorithm 48 remains the motivating audit record, while the implementation and regression boundary are corpus-wide. No runtime branch consults a model label, filename, algorithm number, or function name.
