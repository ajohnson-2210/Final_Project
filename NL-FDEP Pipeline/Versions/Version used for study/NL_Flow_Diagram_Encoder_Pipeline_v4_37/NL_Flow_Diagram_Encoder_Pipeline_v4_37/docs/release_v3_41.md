# NL-FDEP v3.41 release record

## Scope

v3.41 implements the user-approved contextual class-routine interpretation identified during the source_d Algorithm 37 audit while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC241 contextual class-routine recovery

When an isolated source is explicitly one `CLASS`, supplies a direct-child `CONSTRUCTOR(...)`, and also supplies direct-child `PROCEDURE name(...)` and/or `FUNCTION name(...)` routines, the class context makes those declarations unambiguous class routines. GC241 therefore represents them using the frozen AJ v1.1 class surface:

```text
CONSTRUCTOR(parameters):
-> CONSTRUCTOR ACCEPTS(parameters)
   ...
   ENDCONSTRUCTOR

PROCEDURE/ FUNCTION name(parameters):
-> METHOD name ACCEPTS(parameters)
   ...
   ENDMETHOD
```

A missing terminal `ENDCLASS` is added only when the source contains no unindented executable material after the class. Existing explicit routine/class terminators are canonicalised without duplication. The rule is deliberately limited to classes that explicitly provide a constructor so it does not pre-empt existing GC203 stateful-class recovery or established expected-failure boundaries.

Two composition guards accompany GC241: canonical `METHOD`/`CONSTRUCTOR` declarations are excluded from generic free-call prefixing, and a top-level `CLASS` is treated as a declaration by the functionless-return wrapper so method-local `RETURN` statements do not cause a synthetic outer function to be invented.

GC241 does not infer properties, rewrite `self`, repair assignment syntax, or change method return behaviour. source_d Algorithm 37 therefore advances to the independently visible `self.arr[self.top_index] = item` assignment-surface boundary.

## Validation

- targeted GC241 regression/boundary tests: 5 passed;
- full pytest suite: 758 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 758 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
