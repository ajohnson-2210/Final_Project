# source_f Algorithm 42 pair deduplication recovery — v3.20

Source shape:

```text
INPUT arr, target
seen = {}
pairs = []
FOR num in arr:
    comp = target - num
    IF comp in seen:
        pairs.add((MIN(num, comp), MAX(num, comp)))
    seen[num] = true
RETURN unique(pairs)
```

Approved interpretation:

1. `seen = {}` is dictionary-backed because later `seen[num] = true` provides decisive indexed-write evidence.
2. `pairs = []` is explicit list evidence; nested `.add(...)` is a list insertion spelling, not evidence to retype the receiver as a set.
3. The pair expression is completely source supplied and canonicalises to a tuple of existing MIN/MAX calls.
4. `unique(pairs)` explicitly requests deduplication and lowers through the compatibility `to_set` intrinsic to Python `set(pairs)`.

The pair-search logic is unchanged. Duplicate pair discovery is intentionally allowed during the scan and removed only at the final source-requested deduplication step.
