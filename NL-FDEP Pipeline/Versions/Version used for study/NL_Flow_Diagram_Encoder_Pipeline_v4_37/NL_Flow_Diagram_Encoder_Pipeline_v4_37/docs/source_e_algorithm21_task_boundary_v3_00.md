# source_e Algorithm 21 audit — v3.00

## Motivating occurrence

The source_e corpus places the next numbered task heading directly between two function bodies:

```text
FUNCTION IS_EVEN(n)
  IF n MOD 2 == 0 THEN
    RETURN TRUE
  ELSE
    RETURN FALSE
  END IF
END FUNCTION
22. Design a procedure that computes the factorial of a positive integer
FUNCTION FACTORIAL(n)
```

The pseudocode for Algorithm 21 is complete. The extraction defect was that `ExampleSectionAdapter` used the next `FUNCTION`/`CLASS` as the body boundary, causing the numbered heading for the next task to be appended to the preceding source block.

## Correction

v3.00 treats a line-start numbered task heading (`<1-2 digits>. <title>`) found between the current code start and the next code start as a corpus-item boundary. The heading itself is not pseudocode and is not sent to the compatibility normaliser.

This is extraction tolerance only. The normaliser, AJ parser and compiler are unchanged.

Negative controls retain decimal literals such as `22.5` and numbered text inside quoted strings/comments.

## Classification

**PASS AFTER CORPUS-ADAPTER TASK-BOUNDARY CORRECTION**

- semantic inference: NO
- algorithmic reconstruction: NO
- source logic correction: NO
- dialect change: NO
