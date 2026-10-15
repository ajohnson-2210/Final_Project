"""Frozen task-semantic behavioural evaluation for Common Tests v1.4.

Experimental scoring is intentionally oracle-free at runtime.  Each enabled test
contains a pre-experiment input fixture, a static expected semantic value and a
declarative observer.  This module executes only the generated experimental
program and normalises what that program actually returns/prints/mutates.  It
must not execute a baseline/reference program or calculate an expected value
from the experimental input.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import math
import os
import re
import subprocess
import sys
import tempfile


@dataclass
class SemanticTestResult:
    name: str
    status: str
    expected_semantic_result: Any
    actual_semantic_result: Any
    semantic_match: bool | None
    reason: str | None
    duration_ms: float | None
    category: str
    semantic_feature: str | None
    fixture_source: str | None
    expectation_policy: str | None
    selected_entrypoint: str | None = None
    invocation_capture: dict[str, Any] | None = None
    score_stream: str = "CORE_BEHAVIOURAL"
    boundary_outcome: str | None = None
    criteria_links: list[str] | None = None


@dataclass
class SemanticTestReport:
    program_path: str
    algorithm_id: int
    contract_version: str
    results: list[SemanticTestResult]

    @property
    def core_results(self) -> list[SemanticTestResult]:
        return [r for r in self.results if r.score_stream == "CORE_BEHAVIOURAL"]

    @property
    def provisional_results(self) -> list[SemanticTestResult]:
        return [r for r in self.results if r.score_stream == "PRE_FREEZE_VALIDATION"]

    @property
    def boundary_results(self) -> list[SemanticTestResult]:
        return [r for r in self.results if r.score_stream == "SEMANTIC_BOUNDARY_PROBE"]

    @property
    def provisional_declared(self) -> int:
        return len(self.provisional_results)

    @property
    def provisional_evaluable(self) -> int:
        return sum(r.status in {"PASSED", "FAILED"} for r in self.provisional_results)

    @property
    def provisional_passed(self) -> int:
        return sum(r.status == "PASSED" for r in self.provisional_results)

    @property
    def provisional_failed(self) -> int:
        return sum(r.status == "FAILED" for r in self.provisional_results)

    @property
    def provisional_not_evaluable(self) -> int:
        return sum(r.status == "NOT_EVALUABLE" for r in self.provisional_results)

    @property
    def provisional_accuracy_percentage(self) -> float | None:
        if not self.provisional_evaluable:
            return None
        return round(self.provisional_passed / self.provisional_evaluable * 100.0, 2)

    @property
    def evaluable_tests(self) -> int:
        return sum(r.status in {"PASSED", "FAILED"} for r in self.core_results)

    @property
    def passed_tests(self) -> int:
        return sum(r.status == "PASSED" for r in self.core_results)

    @property
    def failed_tests(self) -> int:
        return sum(r.status == "FAILED" for r in self.core_results)

    @property
    def not_evaluable_tests(self) -> int:
        return sum(r.status == "NOT_EVALUABLE" for r in self.core_results)

    @property
    def accuracy_percentage(self) -> float | None:
        if not self.evaluable_tests:
            return None
        return round(self.passed_tests / self.evaluable_tests * 100.0, 2)

    @property
    def boundary_probes_declared(self) -> int:
        return len(self.boundary_results)

    @property
    def boundary_probes_evaluable(self) -> int:
        return sum(r.status == "OBSERVED" for r in self.boundary_results)

    @property
    def boundary_probes_accepted(self) -> int:
        return sum(r.boundary_outcome == "OUT_OF_DOMAIN_ACCEPTED" for r in self.boundary_results)

    @property
    def boundary_probes_controlled_rejection(self) -> int:
        return sum(r.boundary_outcome == "CONTROLLED_REJECTION" for r in self.boundary_results)

    @property
    def boundary_probes_incidental_failure(self) -> int:
        return sum(r.boundary_outcome == "INCIDENTAL_FAILURE" for r in self.boundary_results)

    @property
    def boundary_probes_not_evaluable(self) -> int:
        return sum(r.status == "NOT_EVALUABLE" for r in self.boundary_results)

    @property
    def boundary_variance_percentage(self) -> float | None:
        if not self.boundary_probes_evaluable:
            return None
        return round(self.boundary_probes_accepted / self.boundary_probes_evaluable * 100.0, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_report_schema_version": "1.2",
            "runtime_expected_value_generation": False,
            "program_path": self.program_path,
            "algorithm_id": self.algorithm_id,
            "contract_version": self.contract_version,
            "evaluable_tests": self.evaluable_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "not_evaluable_tests": self.not_evaluable_tests,
            "accuracy_percentage": self.accuracy_percentage,
            "pre_freeze_validation": {
                "declared_cases": self.provisional_declared,
                "evaluable_cases": self.provisional_evaluable,
                "passed_cases": self.provisional_passed,
                "failed_cases": self.provisional_failed,
                "not_evaluable": self.provisional_not_evaluable,
                "accuracy_percentage": self.provisional_accuracy_percentage,
                "included_in_core_behavioural_score": False,
                "included_in_baseline_calibration": False,
                "interpretation": "Candidate valid-domain coverage expansions retained for pre-freeze baseline validation. Results are descriptive only until explicitly promoted to CORE_BEHAVIOURAL.",
            },
            "semantic_boundary": {
                "measure": "SEMANTIC_BOUNDARY_VARIANCE",
                "declared_probes": self.boundary_probes_declared,
                "evaluable_probes": self.boundary_probes_evaluable,
                "out_of_domain_accepted": self.boundary_probes_accepted,
                "controlled_rejection": self.boundary_probes_controlled_rejection,
                "incidental_failure": self.boundary_probes_incidental_failure,
                "not_evaluable": self.boundary_probes_not_evaluable,
                "variance_percentage": self.boundary_variance_percentage,
                "interpretation": "Percentage of evaluable out-of-domain probes that the generated implementation accepted and processed. This is a descriptive semantic-domain extension measure and is not included in core behavioural accuracy.",
            },
            "results": [asdict(r) for r in self.results],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


_DRIVER = r'''
import ast, inspect, json, pathlib, sys

program_path = pathlib.Path(sys.argv[1]).resolve()
fixture_path = pathlib.Path(sys.argv[2]).resolve()
fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

captures = []
def capture_print(*args, **kwargs):
    captures.append(list(args))

class SemanticToken(str):
    """Case-insensitive representation of a semantic enum token."""
    def __eq__(self, other):
        return str(self).casefold() == str(other).casefold()
    def __hash__(self):
        return hash(str(self).casefold())


def to_jsonable(value, depth=0):
    if depth > 14:
        return {"$repr": repr(value)}
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, float) and (value != value or value in (float('inf'), float('-inf'))):
            return {"$repr": repr(value)}
        return str(value) if isinstance(value, SemanticToken) else value
    if isinstance(value, dict):
        return {str(k): to_jsonable(v, depth+1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v, depth+1) for v in value]
    if isinstance(value, set):
        vals = [to_jsonable(v, depth+1) for v in value]
        try:
            return sorted(vals, key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
        except Exception:
            return vals
    if hasattr(value, "__dict__"):
        return {"$object": value.__class__.__name__, "attrs": to_jsonable(vars(value), depth+1)}
    return {"$repr": repr(value)}


class Obj:
    pass


def _set_aliases(obj, pairs):
    for a, b, value in pairs:
        setattr(obj, a, value)
        setattr(obj, b, value)


def build(value, shared):
    if isinstance(value, list):
        return [build(v, shared) for v in value]
    if not isinstance(value, dict):
        return value
    if "$ref" in value:
        return shared[value["$ref"]]
    kind = value.get("$type")
    if kind == "ENUM_TOKEN":
        return SemanticToken(str(value.get("value", "")))
    if kind == "BINARY_TREE":
        raw = value.get("level_order", [])
        nodes = [None if v is None else Obj() for v in raw]
        for idx, raw_value in enumerate(raw):
            node = nodes[idx]
            if node is None:
                continue
            li, ri = 2*idx+1, 2*idx+2
            left = nodes[li] if li < len(nodes) else None
            right = nodes[ri] if ri < len(nodes) else None
            _set_aliases(node, [("Value", "value", raw_value), ("Left", "left", left), ("Right", "right", right)])
        return nodes[0] if nodes else None
    if kind == "LINKED_LIST":
        vals = value.get("values", [])
        nodes = []
        for raw_value in vals:
            node = Obj()
            _set_aliases(node, [("Value", "value", raw_value), ("Next", "next", None)])
            nodes.append(node)
        for i in range(len(nodes)-1):
            nodes[i].Next = nodes[i+1]
            nodes[i].next = nodes[i+1]
        cycle = value.get("cycle_to_index")
        if nodes and cycle is not None:
            nodes[-1].Next = nodes[int(cycle)]
            nodes[-1].next = nodes[int(cycle)]
        return nodes[0] if nodes else None
    if kind == "OBJECT":
        obj = Obj()
        for k, v in value.get("attrs", {}).items():
            setattr(obj, k, build(v, shared))
        return obj
    return {str(k): build(v, shared) for k, v in value.items()}


def positional_arities(fn):
    try:
        sig = inspect.signature(fn)
    except Exception:
        return set()
    required = [p for p in sig.parameters.values() if p.default is inspect._empty and p.kind in (p.POSITIONAL_ONLY,p.POSITIONAL_OR_KEYWORD)]
    total = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY,p.POSITIONAL_OR_KEYWORD)]
    if any(p.kind == p.VAR_POSITIONAL for p in sig.parameters.values()):
        return set(range(len(required), max(len(required), 12)+1))
    return set(range(len(required), len(total)+1))


source = program_path.read_text(encoding="utf-8")
try:
    tree = ast.parse(source)
except Exception as exc:
    sys.__stdout__.write(json.dumps({"status":"NOT_EVALUABLE","reason":f"Generated Python is not syntax-valid: {exc}"}))
    raise SystemExit(0)

top_level_function_names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
top_level_class_names = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
unsafe_top_level = []
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
        continue
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        continue
    unsafe_top_level.append(type(node).__name__)
if unsafe_top_level and fixture.get("require_function_only", True):
    sys.__stdout__.write(json.dumps({
        "status":"NOT_EVALUABLE",
        "reason":"Semantic invocation is not used because generated Python contains top-level executable statements.",
        "top_level_statement_kinds":unsafe_top_level,
    }))
    raise SystemExit(0)

ns = {"__name__":"__semantic_test__", "print":capture_print}
try:
    exec(compile(source, str(program_path), "exec"), ns, ns)
except Exception as exc:
    sys.__stdout__.write(json.dumps({"status":"NOT_EVALUABLE","reason":f"Generated Python could not be loaded for semantic invocation: {type(exc).__name__}: {exc}"}))
    raise SystemExit(0)

# Shared values are built once so repeated operations observe the same mutable state.
shared_raw = fixture.get("shared_values") or {}
shared = {name: None for name in shared_raw}
for name, value in shared_raw.items():
    shared[name] = build(value, shared)

execution_target = str(fixture.get("execution_target", "FUNCTION")).upper()
if execution_target == "CLASS":
    required_methods = [str(v) for v in fixture.get("required_methods", [])]
    class_candidates = []
    preferred = [str(v) for v in fixture.get("class_candidates", [])]
    names = preferred + [n for n in top_level_class_names if n not in preferred]
    for name in names:
        cls = ns.get(name)
        if not isinstance(cls, type):
            continue
        if all(callable(getattr(cls, method, None)) for method in required_methods):
            class_candidates.append(cls)
    if len(class_candidates) != 1:
        sys.__stdout__.write(json.dumps({"status":"NOT_EVALUABLE","reason":"No unambiguous task class could be identified.","top_level_classes":top_level_class_names,"required_methods":required_methods}))
        raise SystemExit(0)
    cls = class_candidates[0]
    try:
        obj = cls(*[build(v, shared) for v in fixture.get("constructor_arguments", [])])
    except BaseException as exc:
        sys.__stdout__.write(json.dumps({"status":"ERROR","selected_entrypoint":getattr(cls,"__name__",None),"prints":to_jsonable(captures),"returns":[],"errors":[{"type":type(exc).__name__,"message":str(exc)}]}))
        raise SystemExit(0)
    observed = []
    errors = []
    for op in fixture.get("operations", []):
        method_name = str(op.get("method", ""))
        method = getattr(obj, method_name, None)
        if not callable(method):
            sys.__stdout__.write(json.dumps({"status":"NOT_EVALUABLE","reason":f"Required operation method {method_name!r} was not available.","selected_entrypoint":getattr(cls,"__name__",None)}))
            raise SystemExit(0)
        args = [build(v, shared) for v in op.get("arguments", [])]
        try:
            result = method(*args)
            if op.get("observe"):
                observed.append(to_jsonable(result))
            errors.append(None)
        except BaseException as exc:
            if op.get("observe"):
                observed.append(None)
            errors.append({"type":type(exc).__name__,"message":str(exc)})
            if not fixture.get("continue_after_error", False):
                break
    out = {
        "status":"COMPLETED" if not any(errors) else "ERROR",
        "selected_entrypoint":getattr(cls,"__name__",None),
        "prints":to_jsonable(captures),
        "returns":observed,
        "post_object":to_jsonable(obj),
        "shared_values":to_jsonable(shared),
        "errors":errors,
    }
    sys.__stdout__.write(json.dumps(out, ensure_ascii=False))
    raise SystemExit(0)

allowed_arities = set(int(v) for v in fixture.get("allowed_arities", []) if isinstance(v, int) or str(v).isdigit())
preferred = [str(v) for v in fixture.get("entrypoint_candidates", [])]
# The canonical generic wrapper is a pipeline artefact, not a model-specific name.
if "unnamed_function" in top_level_function_names and "unnamed_function" not in preferred:
    preferred.append("unnamed_function")
possible = []
for name in preferred + [n for n in top_level_function_names if n not in preferred]:
    fn = ns.get(name)
    if not callable(fn):
        continue
    arities = positional_arities(fn)
    if allowed_arities and not (arities & allowed_arities):
        continue
    possible.append(fn)
# Preferred exact wrapper wins; otherwise require a unique arity-compatible task function.
candidate = None
for fn in possible:
    if getattr(fn, "__name__", "") == "unnamed_function":
        candidate = fn
        break
if candidate is None and len(possible) == 1:
    candidate = possible[0]
if candidate is None:
    sys.__stdout__.write(json.dumps({"status":"NOT_EVALUABLE","reason":"No unambiguous task entrypoint function could be identified.","top_level_functions":top_level_function_names,"allowed_arities":sorted(allowed_arities)}))
    raise SystemExit(0)

candidate_arities = positional_arities(candidate)
selected_arity = None
if candidate_arities:
    if allowed_arities:
        matches = sorted(candidate_arities & allowed_arities)
        selected_arity = matches[-1] if matches else None
    else:
        selected_arity = max(candidate_arities)

variant = None
for item in fixture.get("invocation_variants", []):
    variant_arities = {int(v) for v in item.get("arities", [])}
    if selected_arity in variant_arities:
        variant = item
        break
source_fixture = variant or fixture
invocations = source_fixture.get("invocations")
if invocations is None:
    invocations = [{"arguments": source_fixture.get("arguments", [])}]

returns = []
post_arguments = []
errors = []
for inv in invocations:
    args = [build(v, shared) for v in inv.get("arguments", [])]
    try:
        result = candidate(*args)
        returns.append(to_jsonable(result))
        post_arguments.append(to_jsonable(args))
        errors.append(None)
    except BaseException as exc:
        returns.append(None)
        post_arguments.append(to_jsonable(args))
        errors.append({"type":type(exc).__name__,"message":str(exc)})
        if not fixture.get("continue_after_error", False):
            break

out = {
    "status":"COMPLETED" if not any(errors) else "ERROR",
    "selected_entrypoint":getattr(candidate,"__name__",None),
    "selected_arity":selected_arity,
    "prints":to_jsonable(captures),
    "returns":returns,
    "post_arguments":post_arguments,
    "shared_values":to_jsonable(shared),
    "errors":errors,
}
sys.__stdout__.write(json.dumps(out, ensure_ascii=False))
'''


def _run_invocation(program_path: Path, semantic: dict[str, Any], timeout: float, random_seed: int | None, environment: dict[str, str] | None, requires_modules: list[str] | None) -> dict[str, Any]:
    fixture = dict(semantic.get("fixture") or {})
    fixture.setdefault("allowed_arities", semantic.get("allowed_arities") or [])
    fixture.setdefault("require_function_only", True)
    with tempfile.TemporaryDirectory(prefix="nl_fdep_semantic_") as td:
        fixture_path = Path(td) / "fixture.json"
        fixture_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
        env = dict(os.environ)
        for key, value in (environment or {}).items():
            env[str(key)] = str(value)
        if random_seed is not None:
            env.setdefault("PYTHONHASHSEED", str(int(random_seed)))
        cmd = [sys.executable]
        if not requires_modules:
            cmd.append("-S")
        cmd.extend(["-c", _DRIVER, str(Path(program_path).resolve()), str(fixture_path)])
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, check=False)
        except subprocess.TimeoutExpired:
            return {"status":"NOT_EVALUABLE","reason":"Semantic invocation exceeded the configured timeout."}
        if cp.returncode != 0:
            return {"status":"NOT_EVALUABLE","reason":f"Semantic invocation driver failed with return code {cp.returncode}.","stderr":cp.stderr}
        try:
            return json.loads(cp.stdout or "{}")
        except json.JSONDecodeError:
            return {"status":"NOT_EVALUABLE","reason":"Semantic invocation driver did not return valid JSON.","stdout":cp.stdout,"stderr":cp.stderr}


def _rows(capture: dict[str, Any]) -> list[list[Any]]:
    value = capture.get("prints") or []
    return [row if isinstance(row, list) else [row] for row in value]


def _text(capture: dict[str, Any]) -> str:
    return "\n".join(" ".join(str(v) for v in row) for row in _rows(capture))


def _return_raw(capture: dict[str, Any], aggregate: str | None) -> Any:
    values = capture.get("returns") or []
    if str(aggregate or "").upper() == "INVOCATION_SEQUENCE":
        return values
    non_null = [v for v in values if v is not None]
    if len(values) == 1 and values[0] is not None:
        return values[0]
    if non_null:
        return non_null[-1] if len(non_null) == 1 else non_null
    return None


def _print_raw(capture: dict[str, Any]) -> Any:
    rows = _rows(capture)
    if not rows:
        return None
    if len(rows) == 1:
        row = rows[0]
        if len(row) == 1:
            return row[0]
        return row
    if all(len(row) == 1 for row in rows):
        return [row[0] for row in rows]
    return rows


def _raw(capture: dict[str, Any], observer: dict[str, Any]) -> Any:
    ret = _return_raw(capture, observer.get("aggregate"))
    return ret if ret is not None else _print_raw(capture)


def _as_scalar(value: Any) -> Any:
    while isinstance(value, list) and len(value) == 1:
        value = value[0]
    return value


def _token_match(value: Any, tokens: list[str]) -> bool:
    text = str(value).casefold()
    return any(str(token).casefold() in text for token in tokens)


def _normalise_one_search(value: Any, observer: dict[str, Any]) -> Any:
    value = _as_scalar(value)
    if value is None:
        return None
    if value in (observer.get("sentinel_values") or []):
        return None
    if _token_match(value, observer.get("not_found_tokens") or []):
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    m = re.search(r"-?\d+", str(value))
    return int(m.group(0)) if m else value


def _normalise_observed(capture: dict[str, Any], semantic: dict[str, Any]) -> tuple[Any, str | None]:
    observer = semantic.get("observer")
    if not isinstance(observer, dict):
        return None, "No declarative semantic observer is defined for this test."
    kind = str(observer.get("kind") or "").upper()
    raw = _raw(capture, observer)
    text = _text(capture)
    try:
        if kind == "BOOLEAN":
            scalar = _as_scalar(raw)
            if isinstance(scalar, bool):
                return scalar, None
            combined = str(scalar) if scalar is not None else text
            if _token_match(combined, observer.get("negative_tokens") or []): return False, None
            if _token_match(combined, observer.get("positive_tokens") or []): return True, None
            if str(combined).strip().casefold() in {"true","yes"}: return True, None
            if str(combined).strip().casefold() in {"false","no"}: return False, None
        elif kind == "ENUM":
            scalar = _as_scalar(raw)
            combined = str(scalar) if scalar is not None else text
            for canonical, tokens in (observer.get("values") or {}).items():
                if str(combined).strip().casefold() == str(canonical).casefold() or _token_match(combined, list(tokens or [])):
                    return str(canonical), None
        elif kind == "BINARY_STRING":
            scalar = _as_scalar(raw)
            combined = str(scalar) if scalar is not None else text
            parts = re.findall(r"(?:0b\s*)?([01]+)", combined, re.I)
            if parts:
                value = parts[-1]
                return value.lstrip("0") or "0", None
        elif kind == "STRING":
            scalar = _as_scalar(raw)
            if scalar is not None: return str(scalar), None
        elif kind == "INTEGER":
            scalar = _as_scalar(raw)
            if scalar is not None: return int(scalar), None
        elif kind == "NUMBER":
            scalar = _as_scalar(raw)
            if isinstance(scalar, (int,float)): return scalar, None
            if scalar is not None: return float(scalar), None
        elif kind in {"SEQUENCE","MATRIX"}:
            if isinstance(raw, list): return raw, None
        elif kind == "NUMERIC_SEQUENCE":
            if isinstance(raw, list):
                return [float(v) for v in raw], None
        elif kind == "MAP":
            if isinstance(raw, dict): return raw, None
            keys = observer.get("print_keys") or []
            if keys and isinstance(raw, list) and len(raw) >= len(keys) and all(isinstance(v,(int,float)) for v in raw[:len(keys)]):
                return {str(k): int(v) for k,v in zip(keys,raw)}, None
        elif kind == "PAIR":
            if isinstance(raw, list) and len(raw) >= 2: return raw[:2], None
        elif kind == "SEARCH_INDEX":
            if str(observer.get("aggregate") or "").upper() == "INVOCATION_SEQUENCE":
                vals = raw if isinstance(raw,list) else [raw]
                # If all returns were null, use printed values as the per-invocation evidence.
                if vals and all(v is None for v in vals):
                    pr = _print_raw(capture); vals = pr if isinstance(pr,list) else [pr]
                return [_normalise_one_search(v,observer) for v in vals], None
            return _normalise_one_search(raw,observer), None
        elif kind == "NULLABLE_SCALAR":
            vals = raw if isinstance(raw,list) else [raw]
            if str(observer.get("aggregate") or "").upper() != "INVOCATION_SEQUENCE": vals=vals[-1:]
            out=[]
            for v in vals:
                vv=_as_scalar(v)
                if vv is None or _token_match(vv,observer.get("null_tokens") or []): out.append(None)
                else: out.append(vv)
            return out if str(observer.get("aggregate") or "").upper()=="INVOCATION_SEQUENCE" else out[0], None
        elif kind == "EMPTY_AWARE_SEQUENCE":
            # Preserve explicit null returns from operation-sequence observations: an
            # empty pop/peek commonly returns None and that is semantic evidence, not
            # absence of evidence. Fall back to printed observations only when the
            # invocation produced no return records at all.
            vals = list(capture.get("returns") or [])
            if not vals:
                pr = _print_raw(capture)
                vals = pr if isinstance(pr, list) else [pr]
            out=[]
            for v in vals:
                vv=_as_scalar(v)
                if vv is None or _token_match(vv,observer.get("empty_tokens") or []): out.append("EMPTY")
                else: out.append(vv)
            return out, None
        elif kind == "PAIR_SET":
            if isinstance(raw,list):
                if raw and all(isinstance(v,(int,float)) for v in raw) and len(raw)==2: return [raw],None
                return raw,None
        elif kind == "MOVE_SEQUENCE":
            if isinstance(raw,list) and raw and all(isinstance(v,list) and len(v)>=2 for v in raw):
                return [[str(v[0]).upper(),str(v[1]).upper()] for v in raw],None
            pattern = re.compile(str(observer.get("pattern") or r"move\s+dis[ck](?:\s+\d+)?\s+from\s+([A-Za-z])\s+to\s+([A-Za-z])"),re.I)
            moves=[]
            for m in pattern.finditer(text): moves.append([m.group(1).upper(),m.group(2).upper()])
            if moves: return moves,None
        elif kind == "KADANE_RESULT":
            scalar=_as_scalar(raw)
            if isinstance(scalar,dict):
                result=dict(scalar)
                if "range" in result and "ranges" not in result: result["ranges"]=[result["range"]]
                return result,None
            if isinstance(scalar,list) and len(scalar)>=3 and isinstance(scalar[0],(int,float)):
                return {"max_sum":scalar[0],"ranges":[[int(scalar[1]),int(scalar[2])]]},None
            if isinstance(scalar,(int,float)):
                return {"max_sum":scalar},None
        elif kind == "MAP_STATE":
            if isinstance(raw,dict): return raw,None
            state_name=str(observer.get("state_name") or "")
            shared=(capture.get("shared_values") or {}).get(state_name)
            if isinstance(shared,dict): return shared,None
            post=capture.get("post_arguments") or []
            if post and isinstance(post[-1],list) and post[-1] and isinstance(post[-1][0],dict): return post[-1][0],None
    except Exception as exc:
        return None, f"Declarative semantic observer failed: {type(exc).__name__}: {exc}"
    return None, "The declarative semantic observer could not derive the task result from the invocation evidence."


def _deep_equal(actual: Any, expected: Any, mode: str = "EXACT", tolerance: float = 1e-9) -> bool:
    mode = str(mode or "EXACT").upper()
    if mode == "NUMERIC":
        try: return math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance)
        except Exception: return False
    if mode == "NUMERIC_SEQUENCE":
        if not isinstance(actual,list) or not isinstance(expected,list) or len(actual)!=len(expected): return False
        return all(_deep_equal(a,e,"NUMERIC",tolerance) for a,e in zip(actual,expected))
    if mode == "SET":
        try:
            ka=lambda x: json.dumps(x,sort_keys=True,ensure_ascii=False)
            return sorted(actual,key=ka)==sorted(expected,key=ka)
        except Exception: return False
    if mode == "PAIR_SET":
        try:
            def atom(v):
                return float(v) if isinstance(v,(int,float)) and not isinstance(v,bool) else v
            def canon(seq):
                out=[]
                for pair in seq:
                    a,b=atom(pair[0]),atom(pair[1])
                    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
                        p=sorted([float(a),float(b)])
                    else:
                        p=sorted([a,b], key=lambda x:(str(type(x)),str(x)))
                    out.append(p)
                return sorted(out,key=lambda p:json.dumps(p,sort_keys=True,ensure_ascii=False))
            return canon(actual)==canon(expected)
        except Exception: return False
    if mode == "MATRIX_NUMERIC":
        if not isinstance(actual,list) or not isinstance(expected,list) or len(actual)!=len(expected): return False
        return all(_deep_equal(a,e,"NUMERIC_SEQUENCE",tolerance) for a,e in zip(actual,expected))
    if mode == "KADANE_RESULT":
        if not isinstance(actual,dict) or not isinstance(expected,dict): return False
        if not _deep_equal(actual.get("max_sum"),expected.get("max_sum"),"NUMERIC",tolerance): return False
        actual_ranges=actual.get("ranges") or ([] if actual.get("range") is None else [actual.get("range")])
        accepted=expected.get("accepted_ranges") or []
        if not actual_ranges or not accepted: return False
        return any(list(r) in [list(a) for a in accepted] for r in actual_ranges if isinstance(r,(list,tuple)))
    return actual == expected


class SemanticTestHarness:
    """Execute pre-frozen task-semantic tests with declarative observation only."""

    def run(self, program_path: Path, algorithm_id: int, suite_metadata: dict[str, Any], spec_items: list[dict[str, Any]]) -> SemanticTestReport:
        contract = suite_metadata.get("semantic_contract") or {}
        contract_version = str(contract.get("contract_version") or "1.4")
        results: list[SemanticTestResult] = []
        for index, spec in enumerate(spec_items, start=1):
            semantic = spec.get("semantic_test") or {}
            name = str(spec.get("name", f"Test {index}"))
            category = str(spec.get("category", "NORMAL")).upper()
            feature = spec.get("semantic_feature")
            expected = semantic.get("expected_semantic_result")
            fixture_source = semantic.get("fixture_source")
            expectation_policy = semantic.get("expectation_policy")
            score_stream = str(spec.get("score_stream") or semantic.get("score_stream") or "CORE_BEHAVIOURAL").upper()
            criteria_links = [str(v) for v in (spec.get("criteria_links") or [])]

            if score_stream == "SEMANTIC_BOUNDARY_PROBE":
                if not semantic.get("enabled"):
                    results.append(SemanticTestResult(
                        name, "NOT_EVALUABLE", None, None, None,
                        semantic.get("reason") or "This semantic boundary probe is not automatically evaluable.",
                        None, category, feature, fixture_source, expectation_policy,
                        score_stream=score_stream, boundary_outcome="NOT_EVALUABLE", criteria_links=criteria_links,
                    ))
                    continue
                if expectation_policy != "BOUNDARY_OBSERVATION":
                    results.append(SemanticTestResult(
                        name, "NOT_EVALUABLE", None, None, None,
                        "Semantic boundary probes require BOUNDARY_OBSERVATION expectation policy.",
                        None, category, feature, fixture_source, expectation_policy,
                        score_stream=score_stream, boundary_outcome="NOT_EVALUABLE", criteria_links=criteria_links,
                    ))
                    continue
                import time
                start = time.perf_counter()
                capture = _run_invocation(
                    Path(program_path), semantic,
                    float(spec.get("timeout_seconds", 3.0)),
                    int(spec["random_seed"]) if spec.get("random_seed") is not None else None,
                    {str(k): str(v) for k, v in (spec.get("environment") or {}).items()},
                    [str(v) for v in spec.get("requires_modules", [])],
                )
                duration = round((time.perf_counter() - start) * 1000, 3)
                if capture.get("status") not in {"COMPLETED", "ERROR"}:
                    results.append(SemanticTestResult(
                        name, "NOT_EVALUABLE", None, None, None,
                        capture.get("reason") or "Semantic boundary invocation was not evaluable.", duration,
                        category, feature, fixture_source, expectation_policy, capture.get("selected_entrypoint"), capture,
                        score_stream, "NOT_EVALUABLE", criteria_links,
                    ))
                    continue
                if capture.get("status") == "ERROR":
                    configured = {str(v) for v in ((semantic.get("boundary_probe") or {}).get("controlled_rejection_error_types") or [])}
                    actual_types = {str(v.get("type")) for v in (capture.get("errors") or []) if isinstance(v, dict) and v.get("type")}
                    outcome = "CONTROLLED_REJECTION" if configured and bool(configured & actual_types) else "INCIDENTAL_FAILURE"
                    results.append(SemanticTestResult(
                        name, "OBSERVED", None, {"runtime_errors": capture.get("errors")}, None,
                        "Out-of-domain probe was rejected with a configured validation error." if outcome == "CONTROLLED_REJECTION" else "Out-of-domain probe did not complete successfully; the runtime failure is recorded descriptively.",
                        duration, category, feature, fixture_source, expectation_policy, capture.get("selected_entrypoint"), capture,
                        score_stream, outcome, criteria_links,
                    ))
                    continue
                results.append(SemanticTestResult(
                    name, "OBSERVED", None, {
                        "returns": capture.get("returns"),
                        "prints": capture.get("prints"),
                        "mutated_arguments": capture.get("mutated_arguments"),
                    }, None,
                    "The generated implementation accepted and processed an input outside the frozen semantic contract.",
                    duration, category, feature, fixture_source, expectation_policy, capture.get("selected_entrypoint"), capture,
                    score_stream, "OUT_OF_DOMAIN_ACCEPTED", criteria_links,
                ))
                continue

            if not semantic.get("enabled"):
                results.append(SemanticTestResult(name, "NOT_EVALUABLE", expected, None, None, semantic.get("reason") or "This Common Test is not an automated task-semantic test.", None, category, feature, fixture_source, expectation_policy, score_stream=score_stream, criteria_links=criteria_links))
                continue
            required_policy = "PROVISIONAL_PRE_FREEZE_VALUE" if score_stream == "PRE_FREEZE_VALIDATION" else "STATIC_FROZEN_VALUE"
            if expectation_policy != required_policy or "expected_semantic_result" not in semantic:
                results.append(SemanticTestResult(name, "NOT_EVALUABLE", expected, None, None, f"{score_stream} requires an explicit {required_policy} expectation.", None, category, feature, fixture_source, expectation_policy, score_stream=score_stream, criteria_links=criteria_links))
                continue
            import time
            start = time.perf_counter()
            capture = _run_invocation(
                Path(program_path), semantic,
                float(spec.get("timeout_seconds", 3.0)),
                int(spec["random_seed"]) if spec.get("random_seed") is not None else None,
                {str(k): str(v) for k, v in (spec.get("environment") or {}).items()},
                [str(v) for v in spec.get("requires_modules", [])],
            )
            duration = round((time.perf_counter() - start) * 1000, 3)
            if capture.get("status") not in {"COMPLETED", "ERROR"}:
                results.append(SemanticTestResult(name, "NOT_EVALUABLE", expected, None, None, capture.get("reason") or "Semantic invocation was not evaluable.", duration, category, feature, fixture_source, expectation_policy, capture.get("selected_entrypoint"), capture, score_stream, None, criteria_links))
                continue
            if capture.get("status") == "ERROR":
                results.append(SemanticTestResult(name, "FAILED", expected, {"runtime_errors": capture.get("errors")}, False, "The task entrypoint raised a runtime error for the frozen semantic fixture.", duration, category, feature, fixture_source, expectation_policy, capture.get("selected_entrypoint"), capture, score_stream, None, criteria_links))
                continue
            actual, reason = _normalise_observed(capture, semantic)
            if reason is not None:
                results.append(SemanticTestResult(name, "NOT_EVALUABLE", expected, actual, None, reason, duration, category, feature, fixture_source, expectation_policy, capture.get("selected_entrypoint"), capture, score_stream, None, criteria_links))
                continue
            match = _deep_equal(actual, expected, semantic.get("comparison_mode", "EXACT"), float(semantic.get("numeric_tolerance", 1e-9)))
            results.append(SemanticTestResult(name, "PASSED" if match else "FAILED", expected, actual, match, None if match else "Observed task-semantic result did not match the static frozen expected semantic result.", duration, category, feature, fixture_source, expectation_policy, capture.get("selected_entrypoint"), capture, score_stream, None, criteria_links))
        return SemanticTestReport(str(Path(program_path).resolve()), int(algorithm_id), contract_version, results)
