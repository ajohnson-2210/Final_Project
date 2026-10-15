# v3.77 — GC196 evidence gate tightened for AJ v1.2 nested functions

GC196 remains an evidence-backed compatibility recovery for source that is strongly shaped like a stateful ADT/class but is written as a zero-argument outer function containing nested operations.

AJ v1.2 now supports genuine nested/local functions, so v3.77 tightens the boundary between those two interpretations rather than retiring GC196.

GC196 class recovery now requires all of the existing safeguards plus two additional signals:

1. the outer zero-argument function has a type-like, capitalised source name; and
2. at least one nested operation explicitly mutates declared shared state.

Mere shared-state reads are no longer sufficient. A container such as `FUNCTION Formatter()` whose nested helpers only read a common `prefix` therefore remains a nested-function program. Likewise, a lower-case ordinary function container such as `FUNCTION manager()` remains a function even if nested helpers mutate a shared collection.

The existing safeguards remain in force: at least one explicit state initialiser must precede at least two nested functions; every nested function must reference declared shared state; and the outer body may not call, return, output, or otherwise execute logic outside the state declarations and nested function definitions. An outer return that could expose a closure/factory representation therefore prevents class recovery.

source_b Algorithm 37 still satisfies the complete class-recovery evidence pattern: `Stack` is type-like, `data` is explicit shared state, `push`/`pop`/`peek` all use that state, `push`/`pop` visibly mutate it, and the outer function neither calls nor returns the nested operations. Its canonical AJ class and Python class behaviour are unchanged.

The general positive `Bag` regression also remains class-recovered, while new negative tests cover read-only shared-state helpers and lower-case stateful containers.

Validation:

- 919 pytest passed, 3 skipped, 5 subtests passed.
- 315 unittest passed, 1 skipped.
- historical AJ v1.1 SHA-256 unchanged: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- active AJ v1.2 SHA-256 unchanged: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
