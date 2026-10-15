# NL-FDEP v3.51 release record

## Scope

v3.51 performs the separately approved semantic tightening of the historical simple collection-method compatibility rules. It does not change the frozen AJ_24038155 Dialect v1.1, parser grammar, Python compiler semantics, or intrinsic set.

## Evidenced simple collection-method dispatch

GC033-GC039 keep their existing transformation IDs and target representations, but each rule now requires independent receiver-type evidence before it may fire:

- GC033 `.append(value)`: evidenced list/stack/queue/deque representation;
- GC034 `.add(value)`: evidenced list or set;
- GC035 `.enqueue(value)`: evidenced queue/list/deque representation;
- GC036 `.dequeue()`: evidenced queue/list/deque representation;
- GC037 `.push(value)` / `.push_back(value)`: evidenced stack/list/deque representation;
- GC038 `.pop_front()`: evidenced deque/list/queue representation;
- GC039 `.pop_back()`: evidenced deque/list/stack representation.

Method spelling is never itself evidence. An arbitrary `obj.append(x)`, `obj.push(x)`, or analogous member call therefore remains visible rather than being silently turned into AJ collection manipulation.

## Shared lexical evidence behaviour

The rules now consume the v3.50 `LexicalEvidenceContext`. Collection evidence is established only by explicit declarations/constructors or explicit type annotations, including canonical/generic list, set, dictionary, queue, deque and stack representations. Direct reassignment invalidates prior collection evidence. Formal parameters shadow inherited evidence unless explicitly typed. Sibling routines regain only their enclosing readable evidence, and class evidence is isolated from unrelated classes.

The pre-existing balanced collection paths GC200, GC202, GC213 and GC221 also use this lexical context rather than the earlier source-wide name set. Their operation meanings and historical IDs are unchanged.

## Behaviour boundary

This release intentionally distinguishes standard-data-structure evidence from domain/helper inference:

- an explicitly evidenced list/stack/queue/deque/set may use its approved conventional compatibility aliases;
- a member name alone does not establish that the receiver is such a structure;
- unresolved user/domain methods remain unresolved rather than acquiring collection semantics.

This is the semantic tightening approved after the v3.50 behaviour-neutral consolidation. It does not attempt the separate broader dependency-policy audit or alter older literal/type-hint rules.

## Differential check

A v3.50-v3.51 probe compared processed source plus historical collection transformation records. Representative evidenced list/set/queue/deque/stack cases, nested list append, two-stack state, and explicitly typed list parameters were exactly identical. Only the deliberate unproven-receiver case changed: v3.50 emitted GC033/GC037 for `obj.append(...)`/`obj.push(...)`, whereas v3.51 emits no collection transformation.

## Validation

- new semantic-tightening/refusal tests: 8 passed;
- full pytest suite: 813 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- fresh-extraction rerun: 813 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
