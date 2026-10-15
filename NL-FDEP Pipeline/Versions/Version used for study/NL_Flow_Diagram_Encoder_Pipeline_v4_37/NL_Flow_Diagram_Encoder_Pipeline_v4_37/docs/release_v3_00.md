# NL-FDEP v3.00 release record

## Scope

v3.00 corrects source_e corpus extraction when a numbered task heading appears between the end of one `FUNCTION`/`CLASS` body and the next code start without an otherwise useful separator.

The motivating occurrence is source_e Algorithm 21 (even/odd). The correction is generic to source_e numbered task boundaries and contains no algorithm/routine-name special case.

## Behaviour

- line-start `<number>. <task title>` between code starts terminates the preceding extracted source;
- the heading is not sent to pseudocode normalisation;
- existing `Example:` truncation is preserved and the earliest valid boundary wins;
- decimal literals, strings and comments are not reclassified as task headings.

## Audit classification

source_e 21: **PASS AFTER CORPUS-ADAPTER TASK-BOUNDARY CORRECTION**.

- semantic inference: NO
- algorithmic reconstruction: NO
- source logic correction: NO
- dialect change: NO

## Validation

Working tree:

- pytest: **461 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **461 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
