# NL-FDEP v4.12

v4.12 keeps AJ_24038155 Dialect v1.3 unchanged and fixes one source-proven reserved-identifier propagation defect discovered while auditing the baseline corpus. When a source variable is legally named `list` or `set`, indexed uses such as `list[i]` / `set[i]` are now recognised as identifier indexing rather than the canonical `LIST [...]` / `SET [...]` literal syntax. The source spelling remains unchanged in baseline files; the normaliser applies and logs the existing `__reserved_keyword__...` representation internally. No new AJ syntax or semantics are introduced.
