# NL-FDEP v3.25 release record

## Summary

v3.25 implements the approved source_e 5 regex `REPLACE_ALL` compatibility recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC227 — evidenced regex `REPLACE_ALL`

GC227 recognises a free three-argument `REPLACE_ALL(text, pattern, replacement)` only when the quoted pattern itself contains direct regex syntax evidence. It does not reinterpret plain literal replacements, member methods, or calls of other arities.

The rule protects source regex backslashes across compatibility-to-AJ representation, so escapes such as `\s` are not consumed by the frozen AJ string lexer. It then routes the supplied operation through the internal `regex_replace` compatibility intrinsic, which lowers to Python `re.sub(pattern, replacement, text)`.

No punctuation-removal algorithm is invented: the text, regex pattern, and replacement are all supplied by source_e.

AJ_24038155 Dialect v1.1 is unchanged.

## Validation

- targeted source_e 5 regression: **5 passed**
- full pytest: **681 passed, 3 skipped, 5 subtests passed**
- full unittest: **260 passed, 1 skipped**
