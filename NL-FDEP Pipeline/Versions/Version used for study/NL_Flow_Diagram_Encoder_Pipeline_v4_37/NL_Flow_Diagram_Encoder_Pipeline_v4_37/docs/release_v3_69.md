# Release v3.69 — GC122 abstract character-frequency rescue retired

v3.69 retires the early GC122 compatibility rule that operationalised the abstract source instruction `COUNT frequency of each character` by supplying a complete dictionary-counting algorithm.

## Change

Earlier versions recognised this source shape:

```text
COUNT frequency of each character
```

followed by `Frequency(Character)` and expanded it into executable pseudocode containing:

```text
Frequency <- EMPTY DICTIONARY
FOR EACH Character IN Text DO
    IF Character IN Frequency THEN
        Frequency[Character] <- Frequency[Character] + 1
    ELSE
        Frequency[Character] <- 1
    ENDIF
ENDFOR
```

That expansion chose the data structure, traversal, membership test, increment operation, initialisation branch and loop structure on behalf of the source. Those are missing algorithmic operations rather than surface canonicalisation.

GC122 now performs no operationalisation. The abstract `COUNT frequency of each character` instruction remains visible after ordinary structural normalisation and fails strict AJ v1.1 parsing. No Python AST or generated Python is produced for that unresolved historical corpus item.

## Expected-failure boundary

source_a corpus Algorithm 38 is now intentionally recorded as an expected failure. The source_a aggregate parse floor therefore changes from 38 to 37 successful items; the test also asserts specifically that Algorithm 38 is the failed item so the reduced floor cannot conceal an unrelated regression.

Other generic compatibility processing may still normalise surrounding syntax, but no rule supplies a frequency-count implementation merely to make this source executable.

## Regression coverage

Updated regression coverage verifies that:

- `COUNT frequency of each character` remains present;
- no `Frequency <- EMPTY DICTIONARY` algorithm is inserted;
- no extra counting loop is inserted;
- GC122 records no transformation;
- strict AJ parsing fails on the unresolved abstract operation;
- the corpus regression gate records source_a Algorithm 38 as expected-fail;
- Python generation is not attempted from a valid AJ AST because no valid AST exists.

## Validation

- pytest: 897 passed, 3 skipped, 5 subtests passed;
- unittest: 301 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
