# GC205 — spaced class terminator surface normalisation

## Rule

A standalone line matching `END\s+CLASS`, case-insensitively, is canonicalised to `ENDCLASS`.

## Boundary

The rule is line-level structural spelling only. It does not match quoted text, comments, longer tokens such as `END CLASSROOM`, or invent a missing class terminator.

The frozen AJ_24038155 Dialect v1.1 grammar remains unchanged; `ENDCLASS` is still the canonical form.
