"""Baseline reference pairing and behavioural-oracle support for study runs."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
import tempfile

from aj_test_harness import AJTestHarness, TestCase




def _prepare_reference_execution_source(
    program_path: Path,
    algorithm_title: str | None = None,
) -> tuple[str | None, dict[str, Any]]:
    """Return a syntax-valid execution view without modifying the frozen reference.

    Some supplied baseline ``*.txt`` Python artefacts carry the algorithm title as
    a first-line document heading.  The packaged common-test suite independently
    declares that same title.  When (and only when) the first non-blank line exactly
    matches the declared title, it may be treated as non-code document metadata and
    commented in the in-memory execution view.  The frozen file itself is never
    rewritten and its raw hash remains the provenance anchor.
    """
    source = program_path.read_text(encoding="utf-8")
    raw_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
    meta: dict[str, Any] = {
        "reference_python": str(program_path.resolve()),
        "raw_sha256": raw_hash,
        "raw_syntax_valid": False,
        "execution_syntax_valid": False,
        "normalisation_applied": False,
        "normalisation_rule": None,
    }
    try:
        ast.parse(source)
        meta["raw_syntax_valid"] = True
        meta["execution_syntax_valid"] = True
        meta["execution_sha256"] = raw_hash
        return source, meta
    except SyntaxError as error:
        meta["raw_syntax_error"] = str(error)

    title = str(algorithm_title or "").strip()
    if title:
        lines = source.splitlines(keepends=True)
        first = next((i for i, line in enumerate(lines) if line.strip()), None)
        if first is not None:
            source_heading = lines[first].strip()
            exact_title_match = source_heading == title
            # The frozen Common Tests v1.0/v1.1 metadata contains six long
            # algorithm titles truncated at a stable prefix.  Accept that
            # representation only when the supplied title is itself a long
            # exact prefix of the first non-blank reference line.  This remains
            # a metadata-only execution view: no reference code is rewritten.
            prefix_title_match = (
                not exact_title_match
                and len(title) >= 80
                and source_heading.startswith(title)
                and len(source_heading) > len(title)
            )
            if exact_title_match or prefix_title_match:
                line = lines[first]
                newline = "\n" if line.endswith("\n") else ""
                body = line[:-1] if newline else line
                candidate_lines = list(lines)
                candidate_lines[first] = f"# {body}{newline}"
                candidate = "".join(candidate_lines)
                try:
                    ast.parse(candidate)
                    meta["execution_syntax_valid"] = True
                    meta["normalisation_applied"] = True
                    meta["normalisation_rule"] = (
                        "COMMENT_MATCHED_TEST_SUITE_ALGORITHM_TITLE"
                        if exact_title_match
                        else "COMMENT_PREFIX_MATCHED_TRUNCATED_TEST_SUITE_ALGORITHM_TITLE"
                    )
                    meta["normalised_line_number"] = first + 1
                    meta["declared_algorithm_title"] = title
                    meta["reference_heading"] = source_heading
                    meta["execution_sha256"] = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
                    return candidate, meta
                except SyntaxError as error:
                    meta["execution_syntax_error"] = str(error)

    meta.setdefault("execution_syntax_error", meta.get("raw_syntax_error"))
    return None, meta


def _reference_result_is_oracle_eligible(reference: dict[str, Any], spec: dict[str, Any]) -> bool:
    """Reject infrastructure/runtime faults as inferred behaviour on non-error tests."""
    if reference.get("status") != "COMPLETED":
        return False
    category = str(spec.get("category", "NORMAL")).upper()
    if category != "ERROR_BEHAVIOUR":
        if reference.get("return_code") not in (0, None):
            return False
        if reference.get("error_type") is not None:
            return False
    return True


def _error_type(stderr: str) -> str | None:
    for line in reversed(stderr.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        head = stripped.split(":", 1)[0]
        if head.endswith("Error") or head.endswith("Exception"):
            return head
        break
    return None


def load_test_spec(path: Path) -> list[dict[str, Any]]:
    """Load a study test JSON file.

    Accepted forms are either ``{"tests": [...]}`` or a top-level list.  Each test
    may supply expected output/return-code/error fields.  Missing expected fields can
    later be populated from the baseline reference implementation.
    """
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        tests = data.get("tests", [])
    elif isinstance(data, list):
        tests = data
    else:
        raise ValueError(f"Unsupported test specification in {path}")
    if not isinstance(tests, list):
        raise ValueError(f"'tests' must be a list in {path}")
    return [item for item in tests if isinstance(item, dict)]


def load_test_suite_metadata(path: Path) -> dict[str, Any]:
    """Return non-test metadata from a structured test-suite document."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {key: value for key, value in data.items() if key != "tests"}


def _run_reference(
    program_path: Path,
    spec: dict[str, Any],
    algorithm_title: str | None = None,
) -> dict[str, Any]:
    standard_input = [str(v) for v in spec.get("standard_input", [])]
    required_modules = [str(v) for v in spec.get("requires_modules", [])]
    missing_modules = [name for name in required_modules if importlib.util.find_spec(name) is None]
    if missing_modules:
        return {
            "status": "MISSING_DEPENDENCY",
            "standard_input": standard_input,
            "stdout": [],
            "stderr": f"Required module(s) unavailable: {', '.join(missing_modules)}",
            "return_code": None,
            "error_type": None,
            "duration_ms": 0.0,
            "missing_modules": missing_modules,
            "requires_modules": required_modules,
        }

    execution_source, preparation = _prepare_reference_execution_source(program_path, algorithm_title)
    if execution_source is None:
        return {
            "status": "INVALID_REFERENCE_SOURCE",
            "standard_input": standard_input,
            "stdout": [],
            "stderr": preparation.get("execution_syntax_error") or preparation.get("raw_syntax_error") or "Reference Python is not syntax-valid.",
            "return_code": None,
            "error_type": "SyntaxError",
            "duration_ms": 0.0,
            "category": str(spec.get("category", "NORMAL")).upper(),
            "semantic_feature": spec.get("semantic_feature"),
            "criteria_links": [str(v) for v in spec.get("criteria_links", [])],
            "random_seed": int(spec["random_seed"]) if spec.get("random_seed") is not None else None,
            "environment": {str(k): str(v) for k, v in (spec.get("environment") or {}).items()},
            "requires_modules": required_modules,
            "reference_source_preparation": preparation,
        }

    # ``quit`` and ``exit`` normally come from Python's site module, which the
    # study harness deliberately disables with ``-S``.  Supply deterministic
    # equivalents only in the temporary execution view of the trusted reference.
    prelude = (
        "def quit(code=None):\n"
        "    raise SystemExit(code)\n"
        "def exit(code=None):\n"
        "    raise SystemExit(code)\n\n"
    )
    execution_source = prelude + execution_source
    case = TestCase(
        name=str(spec.get("name", "Reference test")),
        standard_input=standard_input,
        timeout_seconds=float(spec.get("timeout_seconds", 3.0)),
        category=str(spec.get("category", "NORMAL")).upper(),
        semantic_feature=spec.get("semantic_feature"),
        criteria_links=[str(v) for v in spec.get("criteria_links", [])],
        random_seed=int(spec["random_seed"]) if spec.get("random_seed") is not None else None,
        environment={str(k): str(v) for k, v in (spec.get("environment") or {}).items()},
        requires_modules=required_modules,
    )
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="nl_fdep_reference_") as temp_dir:
        execution_path = Path(temp_dir) / "reference_execution.py"
        execution_path.write_text(execution_source, encoding="utf-8")
        result = AJTestHarness().run(
            execution_path,
            [case],
            working_directory=program_path.parent,
        ).results[0]
    return {
        "status": "TIMEOUT" if result.status == "TIMEOUT" else "COMPLETED",
        "standard_input": standard_input,
        "stdout": result.actual_output,
        "stderr": result.standard_error,
        "return_code": result.return_code,
        "error_type": result.actual_error_type,
        "duration_ms": result.duration_ms or round((time.perf_counter() - start) * 1000, 3),
        "category": result.category,
        "semantic_feature": result.semantic_feature,
        "criteria_links": result.criteria_links,
        "random_seed": result.random_seed,
        "environment": result.environment,
        "requires_modules": result.requires_modules,
        "reference_source_preparation": preparation,
    }


def test_cases_from_spec(
    spec_items: list[dict[str, Any]],
    reference_python: Path | None = None,
    reference_title: str | None = None,
) -> tuple[list[TestCase], list[dict[str, Any]]]:
    """Create harness cases without inventing omitted behavioural expectations.

    Explicit researcher expectations are always preserved.  Omitted fields are
    derived only from a supplied reference that actually completes.  If a test
    has no explicit expectations and the reference cannot provide a completed
    result, that test is recorded as ``NOT_EVALUABLE`` and is not executed
    against generated Python.
    """
    cases: list[TestCase] = []
    oracle_records: list[dict[str, Any]] = []
    expectation_names = ("expected_output", "expected_return_code", "expected_error_type")

    for index, spec in enumerate(spec_items, start=1):
        name = str(spec.get("name", f"Test {index}"))
        explicit_fields = [field for field in expectation_names if field in spec and spec.get(field) is not None]
        reference = _run_reference(reference_python, spec, reference_title) if reference_python is not None else None

        expected_output = spec.get("expected_output") if "expected_output" in explicit_fields else None
        expected_return_code = spec.get("expected_return_code") if "expected_return_code" in explicit_fields else None
        expected_error_type = spec.get("expected_error_type") if "expected_error_type" in explicit_fields else None
        derived_fields: list[str] = []

        reference_eligible = reference is not None and _reference_result_is_oracle_eligible(reference, spec)
        if reference_eligible:
            if "expected_output" not in explicit_fields:
                expected_output = reference.get("stdout")
                derived_fields.append("expected_output")
            if "expected_return_code" not in explicit_fields:
                expected_return_code = reference.get("return_code")
                derived_fields.append("expected_return_code")
            if "expected_error_type" not in explicit_fields and reference.get("error_type") is not None:
                expected_error_type = reference.get("error_type")
                derived_fields.append("expected_error_type")

        evaluable_fields = list(explicit_fields) + [field for field in derived_fields if field not in explicit_fields]
        record: dict[str, Any] = {
            "name": name,
            "reference": reference,
            "expected_result_source": (
                "MIXED_RESEARCHER_AND_REFERENCE" if explicit_fields and derived_fields
                else "RESEARCHER_VERIFIED" if explicit_fields
                else "REFERENCE_PYTHON" if derived_fields
                else "NONE"
            ),
            "explicit_expectation_fields": explicit_fields,
            "derived_expectation_fields": derived_fields,
            "evaluable_expectation_fields": evaluable_fields,
        }

        if not evaluable_fields:
            record["test_case_status"] = "NOT_EVALUABLE"
            if reference is None:
                record["reason"] = "No explicit behavioural expectation and no eligible reference oracle were supplied."
            elif reference.get("status") != "COMPLETED":
                record["reason"] = f"Reference oracle did not complete (status={reference.get('status')}); omitted expectations were not invented."
            elif not reference_eligible:
                record["reason"] = (
                    "Reference execution completed with a non-zero/error outcome on a non-error behavioural test; "
                    "that infrastructure/runtime fault was not adopted as expected behaviour."
                )
            else:
                record["reason"] = "No evaluable behavioural expectation was available."
            oracle_records.append(record)
            continue

        record["test_case_status"] = "EVALUABLE"
        oracle_records.append(record)
        cases.append(TestCase(
            name=name,
            standard_input=[str(v) for v in spec.get("standard_input", [])],
            expected_output=[str(v) for v in expected_output] if expected_output is not None else None,
            timeout_seconds=float(spec.get("timeout_seconds", 3.0)),
            category=str(spec.get("category", "NORMAL")).upper(),
            semantic_feature=spec.get("semantic_feature"),
            expected_return_code=int(expected_return_code) if expected_return_code is not None else None,
            expected_error_type=str(expected_error_type) if expected_error_type is not None else None,
            criteria_links=[str(v) for v in spec.get("criteria_links", [])],
            random_seed=int(spec["random_seed"]) if spec.get("random_seed") is not None else None,
            environment={str(k): str(v) for k, v in (spec.get("environment") or {}).items()},
            requires_modules=[str(v) for v in spec.get("requires_modules", [])],
        ))
    return cases, oracle_records

def validate_reference_python(
    reference_python: Path | None,
    spec_items: list[dict[str, Any]],
    reference_title: str | None = None,
) -> dict[str, Any]:
    """Assess the trusted baseline reference and any independent expectations.

    When researcher-specified expected outcomes are present they independently validate
    the reference.  When they are absent, the frozen baseline Python is explicitly
    recorded as ``TRUSTED_REFERENCE`` under the study design rather than pretending it
    has been independently validated.  That trusted reference may then define expected
    behaviour for the common calibration test inputs.
    """
    base={"validation_schema_version":"1.0","reference_python":str(reference_python.resolve()) if reference_python and reference_python.exists() else None}
    if reference_python is None or not reference_python.exists():
        return {**base,"status":"NOT_EVALUATED","reason":"Reference Python implementation was not found.","explicit_tests_total":0}
    _, preparation = _prepare_reference_execution_source(reference_python, reference_title)
    base["reference_source_preparation"] = preparation
    if not preparation.get("execution_syntax_valid"):
        return {
            **base,
            "status": "NOT_EVALUATED",
            "reason": "Reference Python has no syntax-valid executable view under the controlled reference-source policy.",
            "explicit_tests_total": 0,
        }
    explicit=[]
    for index,spec in enumerate(spec_items,start=1):
        fields=[k for k in ("expected_output","expected_return_code","expected_error_type") if k in spec and spec.get(k) is not None]
        if not fields: continue
        run=_run_reference(reference_python,spec,reference_title); checks=[]
        if "expected_output" in fields:
            exp=[str(v) for v in (spec.get("expected_output") or [])]; checks.append(("expected_output",run.get("stdout")==exp,exp,run.get("stdout")))
        if "expected_return_code" in fields:
            exp=spec.get("expected_return_code"); checks.append(("expected_return_code",run.get("return_code")==exp,exp,run.get("return_code")))
        if "expected_error_type" in fields:
            exp=spec.get("expected_error_type"); checks.append(("expected_error_type",run.get("error_type")==exp,exp,run.get("error_type")))
        explicit.append({"name":spec.get("name",f"Test {index}"),"fields":fields,"passed":all(c[1] for c in checks),
                         "checks":[{"field":c[0],"passed":c[1],"expected":c[2],"actual":c[3]} for c in checks],"reference_run":run})
    if not explicit:
        return {**base,"status":"TRUSTED_REFERENCE","reason":"No independent expected outcomes are present. The frozen baseline Python is accepted as the trusted behavioural reference by the study design; this is not an independent validation claim.","explicit_tests_total":0,"tests":[]}
    passed=sum(t["passed"] for t in explicit)
    return {**base,"status":"VALIDATED" if passed==len(explicit) else "FAILED","explicit_tests_total":len(explicit),"explicit_tests_passed":passed,
            "validation_percentage":round(passed/len(explicit)*100,2),"tests":explicit}


def write_reference_validation(
    path: Path,
    reference_python: Path | None,
    spec_items: list[dict[str, Any]],
    reference_title: str | None = None,
) -> dict[str, Any]:
    doc=validate_reference_python(reference_python,spec_items,reference_title); Path(path).write_text(json.dumps(doc,indent=2),encoding="utf-8"); return doc



def _python_structural_comparison(
    generated_python: Path | None,
    reference_python: Path | None,
    reference_title: str | None = None,
) -> dict[str, Any]:
    if generated_python is None or not generated_python.exists() or reference_python is None or not reference_python.exists():
        return {
            "status": "NOT_EVALUATED",
            "reason": "Both generated and reference Python files are required for structural comparison.",
        }
    generated_source = generated_python.read_text(encoding="utf-8")
    reference_source = reference_python.read_text(encoding="utf-8")
    result: dict[str, Any] = {
        "status": "EVALUATED",
        "generated_python": str(generated_python.resolve()),
        "reference_python": str(reference_python.resolve()),
        "exact_source_match": generated_source == reference_source,
        "generated_sha256": hashlib.sha256(generated_source.encode("utf-8")).hexdigest(),
        "reference_sha256": hashlib.sha256(reference_source.encode("utf-8")).hexdigest(),
        "note": (
            "Exact-source and normalised-AST comparisons are descriptive only. A structural mismatch is not scored as incorrect, "
            "because behaviourally equivalent Python implementations may differ syntactically."
        ),
    }
    try:
        generated_ast = ast.dump(ast.parse(generated_source), include_attributes=False)
        result["generated_syntax_valid"] = True
    except SyntaxError as error:
        generated_ast = None
        result["generated_syntax_valid"] = False
        result["generated_syntax_error"] = str(error)
    try:
        reference_ast = ast.dump(ast.parse(reference_source), include_attributes=False)
        result["reference_syntax_valid"] = True
        result["reference_execution_syntax_valid"] = True
        result["reference_execution_normalisation_applied"] = False
    except SyntaxError as error:
        result["reference_syntax_valid"] = False
        result["reference_syntax_error"] = str(error)
        execution_source, preparation = _prepare_reference_execution_source(reference_python, reference_title)
        result["reference_execution_syntax_valid"] = bool(preparation.get("execution_syntax_valid"))
        result["reference_execution_normalisation_applied"] = bool(preparation.get("normalisation_applied"))
        result["reference_execution_normalisation_rule"] = preparation.get("normalisation_rule")
        if execution_source is not None:
            reference_ast = ast.dump(ast.parse(execution_source), include_attributes=False)
        else:
            reference_ast = None
    result["normalised_python_ast_match"] = (
        generated_ast is not None and reference_ast is not None and generated_ast == reference_ast
    )
    return result


def build_baseline_comparison(
    generated_test_report: dict[str, Any] | None,
    reference_python: Path | None,
    tests_path: Path | None,
    oracle_records: list[dict[str, Any]] | None = None,
    generated_python: Path | None = None,
    reference_title: str | None = None,
) -> dict[str, Any]:
    structural = _python_structural_comparison(generated_python, reference_python, reference_title)
    base = {
        "comparison_schema_version": "1.1",
        "comparison_role": "PIPELINE_CALIBRATION",
        "is_baseline": True,
        "reference_python": str(reference_python.resolve()) if reference_python and reference_python.exists() else None,
        "structural_comparison": structural,
        "interpretation_note": (
            "This comparison calibrates the pipeline by comparing Python generated from frozen baseline pseudocode "
            "with the trusted baseline Python on the common behavioural test set. Source-text equality is not required."
        ),
    }
    if reference_python is None or not reference_python.exists():
        return {
            **base,
            "status": "NOT_EVALUATED",
            "reason": "Reference Python implementation was not found.",
        }
    if tests_path is None or not tests_path.exists():
        return {
            **base,
            "status": "STRUCTURAL_ONLY",
            "reason": "No baseline test specification was found; behavioural correctness is not inferred from source similarity.",
        }
    if generated_test_report is None:
        return {
            **base,
            "status": "STRUCTURAL_ONLY",
            "tests_file": str(tests_path.resolve()),
            "reason": "Generated Python was not behaviourally tested.",
            "reference_oracle_runs": oracle_records or [],
        }

    total = int(generated_test_report.get("total_tests", 0) or 0)
    passed = int(generated_test_report.get("passed_tests", 0) or 0)
    return {
        **base,
        "status": "EVALUATED" if total else "STRUCTURAL_ONLY",
        "tests_file": str(tests_path.resolve()),
        "tests_total": total,
        "behaviour_matches": passed,
        "behaviour_mismatches": max(total - passed, 0),
        "behavioural_agreement_percentage": round((passed / total) * 100, 2) if total else None,
        "calibration_score_percentage": round((passed / total) * 100, 2) if total else None,
        "reference_oracle_runs": oracle_records or [],
    }


def build_experimental_comparison(
    generated_test_report: dict[str, Any] | None,
    baseline_calibration: dict[str, Any] | None,
    reference_validation: dict[str, Any] | None,
    reference_python: Path | None,
    tests_path: Path | None,
    oracle_records: list[dict[str, Any]] | None = None,
    semantic_test_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare one experimental/model pipeline result with baseline calibration.

    Both percentages are behavioural scores on the same baseline-owned test set.
    The delta is descriptive (experimental minus baseline) and must not be interpreted
    as a causal estimate of model quality independent of the pipeline.
    """
    baseline_calibration = baseline_calibration or {}
    baseline_score = baseline_calibration.get("calibration_score_percentage")
    if baseline_score is None:
        baseline_score = baseline_calibration.get("behavioural_agreement_percentage")
    semantic_mode = semantic_test_report is not None
    if semantic_mode:
        total = int((semantic_test_report or {}).get("evaluable_tests", 0) or 0)
        passed = int((semantic_test_report or {}).get("passed_tests", 0) or 0)
        experimental_score = (semantic_test_report or {}).get("accuracy_percentage")
        if experimental_score is not None:
            experimental_score = round(float(experimental_score), 2)
    else:
        total = int((generated_test_report or {}).get("total_tests", 0) or 0)
        passed = int((generated_test_report or {}).get("passed_tests", 0) or 0)
        experimental_score = round((passed / total) * 100, 2) if total else None
    comparable = (
        baseline_calibration.get("status") == "EVALUATED"
        and baseline_score is not None
        and experimental_score is not None
        and tests_path is not None
        and tests_path.exists()
    )
    delta = round(experimental_score - float(baseline_score), 2) if comparable else None
    if delta is None:
        effect = "NOT_EVALUABLE"
    elif delta > 0:
        effect = "ABOVE_BASELINE"
    elif delta < 0:
        effect = "BELOW_BASELINE"
    else:
        effect = "AT_BASELINE"
    return {
        "comparison_schema_version": "1.1",
        "comparison_role": "EXPERIMENTAL_SEMANTIC_VS_PIPELINE_CALIBRATION" if semantic_mode else "EXPERIMENTAL_VS_PIPELINE_CALIBRATION",
        "is_baseline": False,
        "reference_python": str(reference_python.resolve()) if reference_python and reference_python.exists() else None,
        "tests_file": str(tests_path.resolve()) if tests_path and tests_path.exists() else None,
        "common_test_set": bool(tests_path and tests_path.exists()),
        "baseline_reference_validation": reference_validation,
        "baseline_calibration_status": baseline_calibration.get("status"),
        "baseline_calibration_score_percentage": baseline_score,
        "experimental_behavioural_score_percentage": experimental_score,
        "experimental_tests_total": total,
        "experimental_tests_passed": passed,
        "experimental_observation_mode": "TASK_SEMANTIC_FUNCTION" if semantic_mode else "PROGRAM_STDOUT_REFERENCE",
        "semantic_test_report": semantic_test_report,
        "delta_from_baseline_percentage_points": delta,
        "comparison_to_baseline": effect,
        "comparison_status": "COMPARABLE" if comparable else "NOT_EVALUABLE",
        "oracle_records": oracle_records or [],
        "interpretation_note": (
            "The baseline score measures pipeline calibration on frozen baseline pseudocode. "
            + (
                "The experimental score measures task-semantic correctness using the Common Tests semantic contract and explicit baseline-derived fixtures; "
                "legacy PROGRAM/stdout execution is not used as the experimental accuracy metric. "
                if semantic_mode else
                "The experimental score measures the experimental pseudocode through the same pipeline against the same trusted baseline Python/test set. "
            )
            + "The percentage-point delta is descriptive and is not a causal correction or adjusted accuracy score."
        ),
    }


def build_frozen_semantic_comparison(
    semantic_test_report: dict[str, Any] | None,
    tests_path: Path | None,
) -> dict[str, Any]:
    """Score experimental semantics against the pre-frozen static test pack.

    No baseline program, reference Python file, or executable oracle participates
    in this comparison.  The frozen semantic reference is 100% of the evaluable
    static expectations declared by the test pack.
    """
    report = semantic_test_report or {}
    total = int(report.get("evaluable_tests", 0) or 0)
    passed = int(report.get("passed_tests", 0) or 0)
    score = report.get("accuracy_percentage")
    if score is not None:
        score = round(float(score), 2)
    comparable = bool(score is not None and total > 0 and tests_path is not None and Path(tests_path).exists())
    delta = round(float(score) - 100.0, 2) if comparable else None
    if delta is None:
        effect = "NOT_EVALUABLE"
    elif delta == 0:
        effect = "AT_REFERENCE"
    else:
        effect = "BELOW_REFERENCE"
    return {
        "comparison_schema_version": "1.3",
        "comparison_role": "EXPERIMENTAL_VS_FROZEN_STATIC_SEMANTIC_REFERENCE",
        "is_baseline": False,
        "reference_python": None,
        "tests_file": str(Path(tests_path).resolve()) if tests_path and Path(tests_path).exists() else None,
        "common_test_set": bool(tests_path and Path(tests_path).exists()),
        "expected_value_policy": "STATIC_PREEXPERIMENT_EXPECTATIONS",
        "runtime_expected_value_generation": False,
        "runtime_baseline_reference_used": False,
        "frozen_reference_score_percentage": 100.0 if comparable else None,
        "experimental_behavioural_score_percentage": score,
        "experimental_tests_total": total,
        "experimental_tests_passed": passed,
        "experimental_observation_mode": "FROZEN_TASK_SEMANTIC",
        "semantic_test_report": report,
        "semantic_boundary": report.get("semantic_boundary"),
        "delta_from_frozen_reference_percentage_points": delta,
        "comparison_to_frozen_reference": effect,
        "comparison_status": "COMPARABLE" if comparable else "NOT_EVALUABLE",
        "interpretation_note": (
            "The experimental score is calculated only from static pre-experiment semantic fixtures and expected values. "
            "No baseline/reference implementation or executable oracle is run to derive expected outcomes during experimental evaluation."
        ),
        # Compatibility aliases retained for existing analysis consumers.  These
        # fields do not imply that a baseline artefact was consulted at runtime.
        "baseline_calibration_score_percentage": 100.0 if comparable else None,
        "delta_from_baseline_percentage_points": delta,
        "comparison_to_baseline": (
            "AT_BASELINE" if effect == "AT_REFERENCE" else
            "BELOW_BASELINE" if effect == "BELOW_REFERENCE" else
            "NOT_EVALUABLE"
        ),
    }
