# Release v3.67 — GC161 preserves source-written LRU method bodies

v3.67 narrows GC161 so its source_c `LRUCache` recogniser performs structural recovery without replacing algorithmic method bodies.

## Change

When the source explicitly provides:

- `CLASS LRUCache`;
- `cache <- EMPTY DICTIONARY`;
- `capacity <- GIVEN CAPACITY`;
- `order <- EMPTY LIST`;
- `get(key)` and `put(key, value)` method headers;

GC161 may still recover the constructor-scoped class surface as `CLASS LRUCache ACCEPTS(capacity)`, retain `cache` and `order` state, canonicalise the two method headers, and close their explicit structural blocks.

It no longer emits a stock LRU implementation in place of the supplied method bodies.

For example, source bodies containing `RETURN 999` and `OUTPUT value` remain those bodies and compile to `return 999` and `print(value)` respectively.

## Explicit operation surface mappings retained

Inside the preserved method bodies GC161 may still map source-explicit collection operations to existing compatibility intrinsics:

- `order.remove(x)` / `CALL order_remove(x)` -> `CALL remove_from_list(order, x)`;
- `order.insert_front(x)` / `CALL order_insert_front(x)` -> `CALL insert_front(order, x)`;
- `order.remove_back()` / `CALL order_remove_back()` -> `CALL remove_last_from_list(order)`;
- `cache.remove(x)` / `CALL cache_remove(x)` -> `CALL remove_key(cache, x)`.

These transformations represent operations already present in the source. They do not add missing-key branches, recency steps, eviction conditions, cache assignments, or any other LRU behaviour that was not supplied.

## Regression coverage

`tests/test_gc161_lru_body_preservation_v3_67.py` verifies that:

- arbitrary source-written `get`/`put` logic is preserved;
- the historical stock implementation is not manufactured;
- explicit LRU operations continue to lower through existing AJ/Python intrinsics;
- no missing-key or eviction behaviour is added when absent from the source.

The exact source_c Algorithm 35 regression remains executable and behaviourally equivalent because its LRU operations are explicitly present in that source.

## Validation

- pytest: 891 passed, 3 skipped, 5 subtests passed;
- unittest: 301 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
