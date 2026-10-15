# source_b Algorithm 38 — AJ Dialect v1.1 evidence audit — v2.84

## Study occurrence

source_b Algorithm 38, **First Non-Repeating Character**:

```text
FUNCTION firstNonRepeating(str):
    freq ← empty dictionary
    FOR each char IN str:
        freq[char] ← freq.get(char, 0) + 1
    FOR each char IN str:
        IF freq[char] == 1 THEN RETURN char
    RETURN None
```

The algorithm is executable and complete. It explicitly creates a frequency dictionary, increments the count for each character, scans the original string for the first count of one, and explicitly returns `None` when no such character exists.

## v2.83 issue

Two source forms exposed language-design friction rather than missing algorithmic semantics:

1. `freq.get(char, 0)` is conventional method-style dictionary retrieval, while AJ v1.0 used the unusual `freq~GET(char, 0)` spelling.
2. `None` has an unambiguous null-value meaning but AJ v1.0 had no native null literal and relied on compatibility forms such as `CALL NULL()`.

The existing generic CALL-prefix pass also risked turning method syntax into invalid forms such as `freq.CALL get(...)` because AJ v1.0 did not have a general member-call expression.

## Approved language measure

The study evidence motivated a deliberate dialect revision rather than two corpus-specific recovery patches.

AJ_24038155 Dialect **v1.1** adds:

- native `NONE` literal;
- general `object.method(...)` member invocation;
- canonical dictionary `dictionary.GET(key[, default])` syntax;
- semantic distinction between dictionary `GET` and an ordinary user-defined method named `GET`;
- backwards-compatible acceptance of v1.0 `dictionary~GET(...)`.

## Canonical v1.1 form

```text
FUNCTION firstNonRepeating ACCEPTS(str)
    freq <- EMPTY DICTIONARY
    FOR EACH __reserved_keyword__char IN str DO
        freq[__reserved_keyword__char] <- freq.GET(__reserved_keyword__char, 0) + 1
    ENDFOR
    FOR EACH __reserved_keyword__char IN str DO
        IF freq[__reserved_keyword__char] == 1 THEN
            RETURN __reserved_keyword__char
        ENDIF
    ENDFOR
    RETURN NONE
ENDFUNCTION
```

`char` is renamed only because it conflicts with the AJ `CHAR` keyword; that existing reserved-identifier measure is independent of v1.1.

## Expected Python

```python
def firstNonRepeating(str):
    freq = {}
    for __reserved_keyword__char in str:
        freq[__reserved_keyword__char] = freq.get(__reserved_keyword__char, 0) + 1
    for __reserved_keyword__char in str:
        if freq[__reserved_keyword__char] == 1:
            return __reserved_keyword__char
    return None
```

Behavioural checks:

```text
"swiss" -> "w"
"aabb"  -> None
```

## Property/method distinction

v1.1 deliberately distinguishes:

```text
x.item       property access
x.item()     method invocation
```

`x.GET(...)` is not a dictionary operation merely because the method is named `GET`. Static evidence must show that `x` is dictionary-backed. A user-defined `Registry.GET(...)` therefore remains an ordinary method call.

## Backwards compatibility

Strict parsing continues to accept v1.0:

```text
freq~GET(key, default)
```

The v1.1 compatibility profile canonicalises it to:

```text
freq.GET(key, default)
```

## Audit classification

```text
Algorithm:
    source_b 38 — First Non-Repeating Character

status:
    PASS UNDER AJ_24038155 DIALECT v1.1

algorithmic completeness:
    COMPLETE

language-design changes motivated:
    native NONE literal
    general member-method invocation
    canonical dictionary .GET syntax

semantic inference:
    NONE

algorithmic reconstruction:
    NO

control-flow change:
    NO

data structure invented:
    NO

method operation invented:
    NO

backwards compatibility:
    v1.0 ~GET remains accepted
```

## Regression evidence

`tests/test_aj_v11_none_member_get_v2_84.py` verifies:

- `NONE`, `None`, and `none` parse as the native null literal;
- quoted `STRING("None")` is not rewritten;
- `x.item` and `x.item()` remain distinct;
- member calls can appear as standalone statements;
- dictionary `.GET` resolves only with dictionary evidence;
- dictionary-typed parameters and properties resolve correctly;
- a user-defined `GET` method remains an ordinary method;
- v1.0 `~GET` remains accepted and canonicalises to `.GET` under compatibility processing;
- the exact source_b 38 occurrence parses, compiles and behaves correctly.
