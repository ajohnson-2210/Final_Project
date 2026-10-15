# NL-FDEP v4.11

Dialect: **AJ_24038155 Dialect v1.3** (unchanged)

## Purpose

Complete the v4.09 source-proven reserved-keyword identifier escape so baseline source pseudocode can preserve original Python/source names rather than being pre-normalised.

## Changes

1. A reserved identifier proven by source binding syntax is now propagated into a simple AJ `STRING("{identifier}")` placeholder. The surrounding string text is unchanged.
2. A reserved spelling in member/property position after `.` is treated as structural evidence of identifier intent. Examples include `os.path.join(...)` and `swarm.step(...)`; these normalise internally to the protected `__reserved_keyword__...` representation without changing the baseline source file.
3. Existing literal constructors, range `STEP`, `JOIN(...)`, casts, and other genuine AJ keyword syntax remain protected from accidental rewriting.
4. No dialect syntax or semantic capability is added; the frozen language version remains v1.3.

## Study consequence

Baseline pseudocode should retain source identifiers exactly. Keyword collision handling is an auditable pipeline transformation rather than a researcher-authored baseline edit.
