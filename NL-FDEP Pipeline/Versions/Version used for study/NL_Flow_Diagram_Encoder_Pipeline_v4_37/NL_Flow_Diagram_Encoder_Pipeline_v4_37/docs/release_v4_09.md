# NL-FDEP v4.09 — Source-proven reserved identifier escape

## Scope

v4.09 is a narrow semantic-preservation fix discovered during the first baseline pilot. It does not add AJ syntax or broaden compiler semantics.

## Problem

AJ keywords are case-insensitive. A strict source line such as `string <- STRING("1a23")` was therefore lexed with the left-hand `string` as the `STRING` keyword, causing the parser to expect `(` and fail at `<-`. The same issue applies to other reserved spellings used in unambiguous identifier-binding positions, including loop variables such as `char`.

## Rule

When source syntax itself proves that an AJ reserved word is being used as an identifier, the normalisation layer applies the established protected-name convention:

`name` -> `__reserved_keyword__name`

Evidence-bearing binding positions include simple assignment LHSs, canonical loop binders, and declaration binders. Corresponding exact source-spelled identifier uses are escaped outside quoted text. Recognised AJ keyword syntax and constructors are preserved.

The processing audit records these transformations as:

- rule family: `RESERVED_IDENTIFIER_ESCAPE`
- branch: `SOURCE_PROVEN_BINDING_ESCAPE`
- confidence: `source_proven`
- semantic_change: `false`

## Semantic boundary

The rule does not infer identifiers from read-only occurrences and does not repair independent source-semantic errors. In the motivating anagram baseline, the keyword collision is removed, after which strict parsing correctly reaches the separate AJ v1.2 rule that a top-level `RETURN` is invalid outside a function/method.
