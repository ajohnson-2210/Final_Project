# source_c Algorithm 1 — ASCII/CHAR representational recovery — v2.89

## Motivating study occurrence

source_c Algorithm 1 uses a fixed 256-slot count array and indexes it with the form `ASCII(char)` while iterating over characters in each input string:

```text
FUNCTION areAnagrams(str1, str2):
    IF length(str1) != length(str2):
        RETURN False
    countArray = array of size 256 initialized to 0
    FOR each char in str1:
        countArray[ASCII(char)] = countArray[ASCII(char)] + 1
    FOR each char in str2:
        countArray[ASCII(char)] = countArray[ASCII(char)] - 1
        IF countArray[ASCII(char)] < 0:
            RETURN False
    RETURN True
```

The study occurrence is evidence for a general source-surface rule only. The implementation does not inspect model name, corpus filename, algorithm number, or function name.

## Audit decision

`ASCII(x)` is treated as a representational overstatement of the existing AJ/Python compatibility conversion `CHAR(x)`. This is not a new AJ dialect construct and does not modify frozen AJ_24038155 Dialect v1.1.

The canonical recovery is:

```text
ASCII(x)      -> CHAR(x)
CALL ASCII(x) -> CHAR(x)
```

For the motivating source, the loop identifier `char` collides with the case-insensitive reserved AJ keyword `CHAR`. The existing corpus-wide reserved-identifier policy therefore preserves the source identifier mechanically as:

```text
char -> __reserved_keyword__char
```

The combined canonical form is consequently:

```text
countArray[CHAR(__reserved_keyword__char)]
```

The Python compiler lowers the existing `CHAR(expression)` compatibility representation to `ord(expression)`, so the generated Python indexes the 256-slot array with:

```python
countArray[ord(__reserved_keyword__char)]
```

## Source constraint retained

The source itself explicitly selects a 256-element array. The pipeline does not widen that storage, replace it with a dictionary, or otherwise alter the algorithm. The behavioural regression therefore verifies ordinary ASCII inputs, consistent with the source's explicit 256-slot representation.

## Generality safeguards

v2.89 removes a legacy `areAnagrams`-named fallback and uses one general recovery rule instead. Regressions prove that:

- raw `ASCII(x)` is accepted;
- already-prefixed `CALL ASCII(x)` is accepted;
- keyword case is irrelevant for the source wrapper;
- identifiers named `char` are escaped with `__reserved_keyword__` consistently;
- unrelated calls such as `characterCode(x)` are not reclassified.

## Classification

```text
status: PASS AFTER CONSERVATIVE REPRESENTATIONAL RECOVERY
semantic inference: NO
algorithmic reconstruction: NO
control-flow change: NO
dialect change: NO
```
