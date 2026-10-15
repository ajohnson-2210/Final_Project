# Generic lossy assignment source recovery — v2.71

GC193 is an upstream source-integrity rule for text exports in which a Unicode
assignment arrow has been replaced by ASCII `?`.

It may recover `?` to source `←` only when the token position is structurally
unambiguous:

- standalone assignment targets, including indexed/member targets;
- `FOR <iterator> ? <start> TO|DOWNTO <end>` initialisers;
- inline CASE-arm assignments.

The ordinary character normaliser then converts `←` to canonical AJ `<-`.

GC193 does **not** recover relational/control-flow uses such as `WHILE B ? 0`
or `IF A ? B THEN`. Those remain unresolved unless independent source evidence
supports a separate narrow source-integrity recovery.

`?` is not part of AJ_24038155 Dialect v1.0 and the strict AJ parser continues
to reject it. Downstream canonicalisation rules do not accept `?` as an
assignment alternative to `<-`.
