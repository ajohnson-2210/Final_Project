# source_e numbered task-boundary tolerance — v3.00

## General rule

`ExampleSectionAdapter` already discovers task bodies from line-start `FUNCTION` / `CLASS` markers and strips trailing `Example:` sections. v3.00 adds a corpus-boundary check within the region before the next code start:

```text
<number>. <task title>
```

When this appears at line start, it terminates the current extracted body. This prevents formatting/separator mistakes in the research corpus from becoming pseudocode statements.

## Boundary

The rule is deliberately adapter-local and does not modify pseudocode language semantics.

It does not match:

- decimal values such as `22.5`;
- quoted text containing `22. ...`;
- comments prefixed before a number;
- arbitrary numeric expressions.

The existing `Example:` truncation remains active and takes the earliest valid boundary.
