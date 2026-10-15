# v3.84 explicit NULL source-preservation

v3.84 removes the generic compatibility rewrite that converted an explicitly authored `NULL` token into the legacy `CALL NULL()` representation.

The compatibility boundary is now source-faithful:

- explicit source `NULL` remains textually `NULL` in processed/canonical compatibility AJ;
- `IS NULL` and `IS NOT NULL` normalise only the relation, becoming `== NULL` and `!= NULL`;
- native `None`, `none`, and `NONE` continue to canonicalise to the AJ v1.2 native `NONE` literal;
- an explicitly authored legacy `CALL NULL()` remains accepted as that compatibility form;
- quoted text such as `STRING("NULL")` is unchanged.

Python lowering treats both the preserved `NULL` compatibility sentinel and native `NONE` as Python `None`. Equality and inequality guards against either null form use `is None` / `is not None` semantics. This preserves the source spelling in AJ without emitting an undefined Python `NULL` name.

This is a compatibility/compiler change only. It does not alter the AJ v1.1 or v1.2 dialect specifications.

Validation: 944 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped.

Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

Active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
