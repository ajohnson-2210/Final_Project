# NL-FDEP v3.52 release record

## Scope

v3.52 performs the approved cleanup of weak collection-type evidence for ambiguous bare `{}` source initialisers. It does not change the frozen AJ_24038155 Dialect v1.1, parser grammar, Python compiler semantics, or intrinsic set.

## Evidence-only empty-brace resolution

Historical GC092/GC093 inferred set or dictionary meaning from identifier spelling. Those name hints are retired. An exact `name = {}` / `name <- {}` declaration is now resolved only from later structural use in the same lexical scope before any direct rebind:

- indexed access, `.get(...)`, `.keys(...)`, `.values(...)`, `.items(...)`, `.setdefault(...)`, `.popitem(...)`, or the canonical `dictionary_get(...)` form prove dictionary semantics;
- `.add(...)`, `ADD value TO receiver`, or canonical `add_to_set(...)` prove set semantics;
- membership, iteration, return/use, and identifier spelling alone prove neither kind;
- conflicting set and dictionary evidence leaves the declaration unresolved;
- quoted operation text is ignored;
- evidence does not leak across sibling routines/classes;
- a direct rebind ends evidence collection for the original declaration.

A later indexed write keeps the historical GC220 audit ID. Other uniquely structural bare-brace resolutions use GC250.

## Standing regression corpus

The normal pytest gate now contains an internal source_f-shaped regression corpus. It includes the four audited source_f bare-brace examples (Unique IP Addresses, Character Frequency, Longest Substring Without Repeating Chars, and Find Pairs Summing to Target) plus negative cases for name-only hints, membership-only use, iteration-only use, conflicting evidence, rebind invalidation, scope isolation, and quoted operation text. The fixture is extracted through `StructuredExportAdapter`, so corpus extraction and evidence resolution are checked together.

The original external study corpus remains external and unmodified.

## Validation

- evidence/refusal unit and regression-corpus checks: green;
- full pytest suite: 826 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- fresh-extraction rerun: 826 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
