# NL-FDEP v3.49 release record

## Scope

v3.49 refines the existing GC220 bare-empty-braces dictionary-evidence rule for source_f Algorithm 25 while leaving frozen AJ_24038155 Dialect v1.1 unchanged.

## GC220 balanced nested indexed-write evidence

GC220 already resolves a direct bare-braces declaration such as:

```text
seen = {}
```

to `EMPTY DICTIONARY` when a later indexed assignment to the same receiver independently proves mapping semantics. Before v3.49, the evidence matcher assumed the index expression itself contained no closing bracket, so this valid nested-index target was missed:

```text
seen[s[i]] = i
```

v3.49 replaces that flat target matcher with a balanced square-bracket scan. The outer receiver must still be the declared bare-braces name, the bracketed target must close cleanly, and the first token after the outer closing bracket must be `<-` or a single assignment `=` with a non-empty right-hand side. Quoted text inside the index is handled conservatively.

Accordingly, source_f Algorithm 25 now canonicalises:

```text
seen = {}
...
seen[s[i]] = i
```

as:

```text
seen <- EMPTY DICTIONARY
...
seen[s[i]] <- i
```

and deterministic Python uses an ordinary dictionary. Indexed reads, equality comparisons, writes to another receiver, membership-only use, and unrelated expressions remain insufficient evidence. No new dictionary semantics, parser behaviour, compiler behaviour, or dialect syntax is introduced.

## Validation

- targeted source_f Algorithm 25 / GC220 nested-index regression and refusal-boundary tests: 5 new tests passed;
- existing GC220/source_f Algorithm 42 regression coverage remains green;
- full pytest suite: 798 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 798 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
