# Environmental file-type predicate dependency boundary — v2.86

## Rule

Natural-language environmental type predicates are not executable merely because their intended meaning is familiar.

A compatibility layer may convert a descriptive file/folder predicate to a free helper call only when the exact helper dependency used by that conversion is explicitly defined or imported by the supplied pseudocode. Otherwise, the source must remain an expected failure rather than becoming a false executable pass.

This is a source-evidence rule, not a model-specific rule.

## Covered descriptive forms

```text
X is a file
X is a folder
X is a directory
```

These forms require external/environmental semantics. Python has filesystem APIs, but there is no bare built-in `is_file` or `is_directory` function whose use can be assumed for an arbitrary object `X`.

## Accepted evidence at this guard

For the existing historical free-helper conversion, executable evidence means the exact helper is supplied by the source:

```text
FUNCTION is_file ACCEPTS(...)
...
ENDFUNCTION
```

or an explicit import/binding of `is_file`, and correspondingly for `is_directory`.

Explicit member syntax such as:

```text
item.is_file()
item.is_directory()
```

is already executable AJ v1.1 member-call syntax and does not require this descriptive-predicate recovery.

## Missing-dependency response

If the exact dependency is absent, the pipeline preserves the unresolved descriptive predicate and returns an expected strict-parse failure. It must not invent a filesystem library, helper body, path conversion, object representation, or runtime binding.

## Relationship to v2.85

This is an application of the v2.85 undefined-routine recovery boundary. It generalises an earlier source_a Algorithm 48 shape-specific guard after source_b Algorithm 48 demonstrated that the same semantic-integrity problem could bypass protection through a different source structure.

## Corpus-wide evidence

The same unresolved predicate family occurs independently in multiple empirical study files, including source_a, source_b, source_e, and source_c outputs.  Their surrounding syntax differs (wrapper programs, property-based traversal, uppercase pseudo-keywords, nested branches, and member-style operations), but the semantic defect is the same: the source does not bind the environmental file/folder predicate to an executable dependency.

The implementation therefore contains **one predicate-level guard**.  It does not inspect model names, corpus filenames, algorithm numbers, function names, or prompt-specific markers.  Versioned regressions exercise the same guard against multiple corpus-derived shapes plus synthetic unrelated names so future changes cannot collapse it back into a source-specific patch.
