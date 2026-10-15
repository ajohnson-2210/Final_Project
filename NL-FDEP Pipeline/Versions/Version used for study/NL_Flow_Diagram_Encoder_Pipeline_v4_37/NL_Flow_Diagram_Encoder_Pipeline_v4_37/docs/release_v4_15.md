# NL-FDEP v4.15 — corpus fixture cleanup

Pipeline: **NL-FDEP v4.15**  
Dialect: **AJ_24038155 Dialect v1.4**

## Scope

v4.15 is a packaging and test-maintenance release. It does not alter AJ v1.4 syntax or semantics and does not change parser, AST, flow, compiler, scoring or study transformation behaviour.

## Changes

- Removed the bundled `tests/corpora/` directory and its source_a/source_e research-response text fixtures.
- Removed the corpus-wide regression test that required those fixtures.
- Removed the source_e Algorithm 37 corpus-backed test while retaining the three independent GC241 unit tests from the same module.
- Research/model-response corpora are now treated exclusively as external study inputs.
- Historical manifests, checksums and release notes from earlier versions may still mention the former corpus fixtures; those documents describe the packages that existed at those versions.

## Dependency boundary

Normal pipeline execution and baseline processing never required the removed corpus files. Their removal affects only the retired corpus-specific regression coverage.
