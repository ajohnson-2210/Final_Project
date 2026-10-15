# NL-FDEP v3.32 release record

## Scope

v3.32 implements the approved source_d Algorithm 10 quoted-dictionary-key refinement to the existing GC097 compatibility rule while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC097 quoted string-scalar key refinement

GC097 already expands a simple Python-style dictionary literal into `EMPTY DICTIONARY` followed by indexed assignments. Before v3.32, bare identifier keys were canonicalised as AJ `STRING(...)`, but explicitly quoted string keys were copied into the emitted indexed assignment unchanged. Because GC097 returns those expanded lines immediately, the later raw-string wrapper never sees those keys.

v3.32 now recognises an explicitly quoted string-scalar key during the existing GC097 expansion and renders that key directly with the established AJ string-literal renderer. For example:

```text
{'a': 0, "e": 0}
```

expands to indexed assignments using:

```text
[STRING("a")]
[STRING("e")]
```

The existing bare-key behaviour is unchanged. Escaped quote characters supported by the frozen AJ string surface are preserved. This is a representation refinement inside GC097 only; it does not add a new dictionary form, infer missing keys, alter values, or change the strict AJ parser.

## source_d Algorithm 10

The supplied vowel-frequency routine now canonicalises its explicit quoted dictionary keys, parses, encodes to a flow diagram, compiles deterministically to Python, and executes with the supplied case-insensitive vowel-counting behaviour.

## Validation

- targeted source_d 10 / GC097 regression and boundary tests: 4 passed;
- full pytest suite: 719 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 719 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
