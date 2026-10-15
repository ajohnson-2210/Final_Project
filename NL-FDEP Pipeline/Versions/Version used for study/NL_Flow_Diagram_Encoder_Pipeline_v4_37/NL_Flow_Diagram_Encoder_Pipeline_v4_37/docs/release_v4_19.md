# NL-FDEP v4.19 — frozen baseline Python reference discovery

Pipeline: **NL-FDEP v4.19**  
Dialect: **AJ_24038155 Dialect v1.4 (unchanged)**  
Rubric: **v1.0 (criteria unchanged)**

v4.19 updates baseline/reference discovery so the pipeline accepts the frozen study naming convention without changing baseline files.

Accepted explicit reference filenames for Algorithm `n` are:

- `Algorithm n Baseline Python code.py`
- `Algorithm n Baseline Python code.txt`
- legacy `Algorithm n Python.py`

A `.txt` reference is read and executed as Python source without being renamed or rewritten. If more than one explicitly recognised reference filename exists in the same algorithm folder, discovery fails closed as ambiguous. If none exists, the historical fallback of exactly one `.py` file remains supported.

Reference discovery and test discovery remain independent. Therefore, when a baseline Python source is found but `Algorithm n Tests.json` is absent, preflight reports `TESTS_MISSING` rather than incorrectly reporting the reference Python as missing.

No AJ grammar, canonicalisation, AST, flow, lowering, scoring-criterion or behavioural-oracle semantics are changed.
