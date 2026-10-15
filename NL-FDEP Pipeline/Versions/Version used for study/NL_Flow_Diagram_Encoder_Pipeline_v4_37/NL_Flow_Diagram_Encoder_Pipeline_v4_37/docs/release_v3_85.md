# v3.85 explicit empty-array abstraction preservation

v3.85 stops explicitly authored empty arrays from canonicalising as `EMPTY LIST`.

Assignment-style forms such as `data = empty array` / `data <- empty array` now canonicalise to `data <- CALL create_array(0, NONE)`. Command-style forms such as `CREATE empty array data` use the same representation. Explicit empty lists remain `EMPTY LIST`.

The source-provided fact that the array is empty establishes a size of zero, so no capacity is invented. Python lowers `CALL create_array(0, NONE)` to `[None] * 0`, which is an empty mutable sequence backing. Indexed writes into that zero-length storage remain indexed writes and still raise `IndexError`; normalisation does not invent append/growth behaviour or hidden capacity.

This keeps the earlier missing-capacity array-stack semantic boundary intact: an empty array may be represented faithfully, but it is not automatically made large enough for later indexed writes.

Full validation: 948 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped.

Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

Active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
