# source_c Algorithm 35 parenthetical-comment / LRU surface recovery — v3.24

## Source issue

source_c explicitly chooses an empty list for recency state, then adds a parenthesised explanation of an alternative representation:

```text
order = empty list (or a doubly linked list to maintain access order)
```

The parenthetical is commentary, not executable syntax. Before v3.24, later collection compatibility could misread the explanatory `list` token as constructor syntax.

## GC226

GC226 detaches only trailing `(or ...)` / `(for ...)` prose after an otherwise complete `empty <collection>` assignment. It does not strip arithmetic/grouping parentheses or arbitrary parenthesised expressions.

## LRU recovery

Once the comment is detached, the existing source_c LRU structural recovery is able to use the explicitly supplied state and operations. v3.24 additionally accepts the legacy method-header surface at that recogniser, before later generic header canonicalisation.

No LRU algorithm is invented. The source itself establishes dictionary-backed key/value state, a given capacity, recency order, move-to-front on access/update, and back eviction when full.

## Classification

**PASS AFTER TRAILING EXPLANATORY COMMENT NORMALISATION / SOURCE-EVIDENCED LRU CLASS RECOVERY — TRUSTWORTHY EXECUTABLE FOR POSITIVE CAPACITY**
