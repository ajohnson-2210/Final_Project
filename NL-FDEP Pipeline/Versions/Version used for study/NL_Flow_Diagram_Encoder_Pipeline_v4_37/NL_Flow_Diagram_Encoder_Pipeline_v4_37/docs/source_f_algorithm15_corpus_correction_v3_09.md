# source_f Algorithm 15 corpus correction audit evidence — v3.09

## Stored TXT occurrence before correction

The DOCX-to-TXT research export stored the two initialisers as:

```text
first = -?
second = -?
```

The user confirmed that this was an export/transcription artefact and approved a one-off correction of this corpus occurrence to negative infinity. The pipeline must not learn `-?` as a general token or alias.

## Approved corrected corpus occurrence

```text
INPUT arr

first = -infinity
second = -infinity

FOR num in arr:
    IF num > first:
        second = first
        first = num
    ELSE IF num > second AND num != first:
        second = num

RETURN second
```

The corrected occurrence then uses the already-established GC151 negative-infinity representation without any new production recovery:

```text
first <- CALL negative_infinity()
second <- CALL negative_infinity()
```

Python therefore contains:

```python
first = float('-inf')
second = float('-inf')
```

## Classification

- status: **PASS AFTER ONE-OFF CORPUS TRANSCRIPTION CORRECTION**
- corpus issue: **DOCX-to-TXT loss/corruption of negative-infinity representation**
- approved corrected source: `-infinity`
- new generic `-?` interpretation: **NO**
- new production rule: **NO**
- semantic inference by pipeline: **NO**
- algorithmic reconstruction: **NO**
- dialect change: **NO**

The original lossy spelling is retained only in audit evidence/regressions so future changes cannot accidentally make `-?` a global negative-infinity synonym.
