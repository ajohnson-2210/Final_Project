"""Study pre-flight validation, hashing and immutable-run provenance."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import csv, hashlib, importlib.metadata, importlib.util, json, re, uuid

from common_test_resources import DEFAULT_COMMON_TESTS_ROOT, find_common_test_file, validate_common_test_pack

ALGORITHM_FOLDER_RE = re.compile(r"^Algorithm\s*-\s*(\d+)$", re.IGNORECASE)


def sha256_file(path: Path | None) -> str | None:
    if path is None or not Path(path).is_file():
        return None
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(document: Any) -> str:
    payload=json.dumps(document,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()




def declared_dependency_environment(tests_file: Path | None) -> dict[str, Any]:
    """Fingerprint external modules explicitly declared by the selected test suite.

    Resume/currentness must change when an optional dependency moves between unavailable
    and available (or its installed distribution version changes), otherwise a prior
    MISSING_DEPENDENCY calibration can be incorrectly reused after the environment is fixed.
    """
    modules: set[str] = set()
    if tests_file is not None and Path(tests_file).is_file():
        try:
            document = json.loads(Path(tests_file).read_text(encoding="utf-8"))
            tests = document.get("tests", []) if isinstance(document, dict) else document if isinstance(document, list) else []
            for spec in tests:
                if isinstance(spec, dict):
                    for name in spec.get("requires_modules", []) or []:
                        if str(name).strip():
                            modules.add(str(name).strip())
        except Exception:
            # Test-file content itself is already covered by tests_sha256; if it cannot be
            # decoded here, preserve the normal provenance decision rather than crashing.
            modules = set()

    state: dict[str, Any] = {}
    for name in sorted(modules):
        available = importlib.util.find_spec(name) is not None
        version = None
        if available:
            try:
                version = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                version = None
            except Exception:
                version = None
        state[name] = {"available": available, "distribution_version": version}
    return {"declared_modules": sorted(modules), "modules": state}

def new_run_id() -> str:
    return f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def _algorithm_dirs(parent: Path) -> dict[int,Path]:
    found={}
    if not parent.is_dir(): return found
    for child in parent.iterdir():
        if not child.is_dir(): continue
        m=ALGORITHM_FOLDER_RE.match(child.name)
        if m: found[int(m.group(1))]=child
    return found


def _expected_source(folder: Path, aid: int) -> Path | None:
    name=f"Algorithm {aid} Pseudocode.txt"
    exact=folder/name
    if exact.is_file(): return exact
    matches=[p for p in folder.glob('*') if p.is_file() and p.name.casefold()==name.casefold()]
    return matches[0] if len(matches)==1 else None


def find_reference_python(folder: Path, aid: int) -> Path | None:
    """Discover one unambiguous baseline/reference Python source file.

    Preferred study filenames are accepted with either a ``.py`` or ``.txt``
    extension because some frozen baseline sources are deliberately stored as
    plain-text Python.  Legacy ``Algorithm n Python.py`` remains supported.
    If more than one explicitly recognised filename is present, discovery
    fails closed rather than guessing.  Only when no recognised filename is
    present is the historical single-``.py`` fallback used.
    """
    folder=Path(folder)
    if not folder.is_dir():
        return None

    recognised_names=(
        f"Algorithm {aid} Baseline Python code.py",
        f"Algorithm {aid} Baseline Python code.txt",
        f"Algorithm {aid} Python.py",
    )
    files=[p for p in folder.iterdir() if p.is_file()]
    recognised=[]
    for expected_name in recognised_names:
        matches=[p for p in files if p.name.casefold()==expected_name.casefold()]
        recognised.extend(matches)

    # Deduplicate defensively while preserving filesystem paths.
    recognised=list(dict.fromkeys(recognised))
    if len(recognised)==1:
        return recognised[0]
    if len(recognised)>1:
        return None

    py_candidates=[p for p in files if p.suffix.casefold()=='.py']
    return py_candidates[0] if len(py_candidates)==1 else None


# Backwards-compatible private alias used by older callers/tests.
def _reference_python(folder: Path, aid: int) -> Path | None:
    return find_reference_python(folder, aid)


def _tests_file(*folders: Path, aid: int) -> Path | None:
    name=f"Algorithm {aid} Tests.json"
    for folder in folders:
        if not folder or not folder.is_dir(): continue
        exact=folder/name
        if exact.is_file(): return exact
        ms=[p for p in folder.glob('*.json') if p.name.casefold()==name.casefold()]
        if len(ms)==1: return ms[0]
    return None




def baseline_algorithm_design(baseline_root: Path) -> dict[str, Any]:
    """Infer the Baseline denominator B and validate its algorithm-ID sequence.

    Baseline B is independent of the experimental LLM denominator N.  B is the
    larger of the pseudocode/reference-Python folder counts in the submitted
    baseline.  A valid baseline must then contain exactly Algorithm 1..B in both
    folders.  This makes gaps, shifted numbering and one-sided extras explicit
    instead of silently redefining the benchmark.
    """
    baseline_root = Path(baseline_root)
    pseudo = baseline_root / "pseudocode"
    python_root = baseline_root / "python"
    pseudo_ids = sorted(_algorithm_dirs(pseudo))
    python_ids = sorted(_algorithm_dirs(python_root))
    baseline_count = max(len(pseudo_ids), len(python_ids))
    expected_ids = list(range(1, baseline_count + 1)) if baseline_count > 0 else []
    expected = set(expected_ids)
    pseudo_set = set(pseudo_ids)
    python_set = set(python_ids)
    missing_pseudocode = sorted(expected - pseudo_set)
    missing_python = sorted(expected - python_set)
    extra_pseudocode = sorted(pseudo_set - expected)
    extra_python = sorted(python_set - expected)
    issues = []
    if baseline_count <= 0:
        issues.append("NO_BASELINE_ALGORITHMS_FOUND")
    if missing_pseudocode:
        issues.append("BASELINE_PSEUDOCODE_IDS_NOT_CONTIGUOUS_1_TO_B")
    if missing_python:
        issues.append("BASELINE_PYTHON_IDS_NOT_CONTIGUOUS_1_TO_B")
    if extra_pseudocode:
        issues.append("BASELINE_PSEUDOCODE_IDS_OUTSIDE_1_TO_B")
    if extra_python:
        issues.append("BASELINE_PYTHON_IDS_OUTSIDE_1_TO_B")
    if pseudo_set != python_set:
        issues.append("BASELINE_PSEUDOCODE_PYTHON_ID_SET_MISMATCH")
    return {
        "baseline_algorithm_count": baseline_count,
        "expected_algorithm_ids": expected_ids,
        "pseudocode_algorithm_ids": pseudo_ids,
        "python_algorithm_ids": python_ids,
        "missing_pseudocode_algorithm_ids": missing_pseudocode,
        "missing_python_algorithm_ids": missing_python,
        "extra_pseudocode_algorithm_ids": extra_pseudocode,
        "extra_python_algorithm_ids": extra_python,
        "status": "MATCH" if not issues else "MISMATCH",
        "issues": issues,
    }

def validate_llm_results(results_root: Path, baseline_root: Path|None=None, expected_ids=range(1,51), common_tests_root: Path|None=None) -> dict[str,Any]:
    results_root=Path(results_root); dirs=_algorithm_dirs(results_root); expected=set(expected_ids)
    rows=[]
    for aid in sorted(expected | set(dirs)):
        folder=dirs.get(aid); source=_expected_source(folder,aid) if folder else None
        bpython=btests=None
        if baseline_root:
            bp=Path(baseline_root)/'python'/f'Algorithm - {aid}'
            bq=Path(baseline_root)/'pseudocode'/f'Algorithm - {aid}'
            bpython=_reference_python(bp,aid); btests=find_common_test_file(aid, common_tests_root or DEFAULT_COMMON_TESTS_ROOT) or _tests_file(bp,bq,aid=aid)
        issues=[]
        if not folder: issues.append('ALGORITHM_FOLDER_MISSING')
        elif not source: issues.append('PSEUDOCODE_FILE_MISSING_OR_MISNAMED')
        if baseline_root and not bpython: issues.append('BASELINE_REFERENCE_PYTHON_MISSING')
        if baseline_root and not btests: issues.append('BASELINE_TESTS_MISSING')
        rows.append({'algorithm_id':aid,'folder':str(folder.resolve()) if folder else None,'source_file':str(source.resolve()) if source else None,
                     'source_sha256':sha256_file(source),'reference_python':str(bpython.resolve()) if bpython else None,
                     'tests_file':str(btests.resolve()) if btests else None,'status':'READY' if not issues else 'ISSUES','issues':issues})
    report=_report('LLM_RESULTS',results_root,rows)
    report['common_test_pack']=validate_common_test_pack(common_tests_root or DEFAULT_COMMON_TESTS_ROOT).to_dict()
    return report


def validate_baseline(baseline_root: Path, expected_ids=None, common_tests_root: Path|None=None) -> dict[str,Any]:
    baseline_root=Path(baseline_root); pseudo=baseline_root/'pseudocode'; py=baseline_root/'python'
    design=baseline_algorithm_design(baseline_root)
    if expected_ids is None:
        expected_ids=design['expected_algorithm_ids']
    pd=_algorithm_dirs(pseudo); yd=_algorithm_dirs(py); expected=set(expected_ids); rows=[]
    for aid in sorted(expected | set(pd) | set(yd)):
        pdir=pd.get(aid); ydir=yd.get(aid); source=_expected_source(pdir,aid) if pdir else None
        ref=_reference_python(ydir,aid) if ydir else None
        packaged_tests=find_common_test_file(aid, common_tests_root or DEFAULT_COMMON_TESTS_ROOT)
        tests=packaged_tests or _tests_file(ydir,pdir,aid=aid)
        issues=[]
        if not pdir: issues.append('PSEUDOCODE_FOLDER_MISSING')
        if not ydir: issues.append('PYTHON_FOLDER_MISSING')
        if pdir and not source: issues.append('PSEUDOCODE_FILE_MISSING_OR_MISNAMED')
        if ydir and not ref: issues.append('REFERENCE_PYTHON_MISSING_OR_AMBIGUOUS')
        if not tests: issues.append('TESTS_MISSING')
        rows.append({'algorithm_id':aid,'pseudocode_folder':str(pdir.resolve()) if pdir else None,'python_folder':str(ydir.resolve()) if ydir else None,
                     'source_file':str(source.resolve()) if source else None,'source_sha256':sha256_file(source),
                     'reference_python':str(ref.resolve()) if ref else None,'reference_python_sha256':sha256_file(ref),
                     'tests_file':str(tests.resolve()) if tests else None,'tests_sha256':sha256_file(tests),
                     'tests_source':'BUNDLED_COMMON_TESTS_V1_1' if packaged_tests else ('BASELINE_LOCAL_FALLBACK' if tests else None),
                     'status':'READY' if not issues else 'ISSUES','issues':issues})
    report=_report('BASELINE',baseline_root,rows)
    report['baseline_root_structure_valid']=pseudo.is_dir() and py.is_dir()
    report['baseline_algorithm_count']=design['baseline_algorithm_count']
    report['baseline_expected_algorithm_ids']=design['expected_algorithm_ids']
    report['baseline_design_status']=design['status']
    report['baseline_design']=design
    # A numbering/set mismatch is a preflight issue even when all discovered
    # folders contain otherwise well-formed files.
    if design['issues'] and not any(r.get('status') != 'READY' for r in rows):
        report['issue_count'] += 1
    report['common_test_pack']=validate_common_test_pack(common_tests_root or DEFAULT_COMMON_TESTS_ROOT).to_dict()
    return report


def _report(kind: str, root: Path, rows: list[dict[str,Any]]) -> dict[str,Any]:
    return {'preflight_schema_version':'1.0','kind':kind,'root':str(root.resolve()),'generated_at_utc':datetime.now(timezone.utc).isoformat(),
            'algorithm_count':len(rows),'ready_count':sum(r['status']=='READY' for r in rows),'issue_count':sum(r['status']!='READY' for r in rows),
            'algorithms':rows}


def write_preflight(report: dict[str,Any], output_dir: Path) -> dict[str,str]:
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    jp=output_dir/'study_preflight.json'; cp=output_dir/'study_preflight.csv'
    jp.write_text(json.dumps(report,indent=2),encoding='utf-8')
    flat=[]
    for row in report.get('algorithms',[]):
        item=dict(row); item['issues']=';'.join(item.get('issues') or []); flat.append(item)
    fields=[]
    for row in flat:
        for k in row:
            if k not in fields: fields.append(k)
    with cp.open('w',encoding='utf-8',newline='') as f:
        if fields:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(flat)
    return {'preflight_json':str(jp.resolve()),'preflight_csv':str(cp.resolve())}


def manifest_is_current(manifest_path: Path, *, source_file: Path, pipeline_version: str, rubric_version: str, rubric_sha256: str,
                        reference_python: Path|None=None, tests_file: Path|None=None, pseudocode_profile: str|None=None) -> bool:
    try: m=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    except Exception: return False
    dependency_environment = declared_dependency_environment(tests_file)
    dependency_hash = sha256_json(dependency_environment)
    dependency_current = (m.get('dependency_environment_sha256')==dependency_hash or
                          (not dependency_environment.get('declared_modules') and m.get('dependency_environment_sha256') is None))
    return (m.get('pipeline_version')==pipeline_version and m.get('rubric_version')==rubric_version and
            (pseudocode_profile is None or m.get('pseudocode_profile')==pseudocode_profile) and
            m.get('source_pseudocode_sha256')==sha256_file(source_file) and m.get('reference_python_sha256')==sha256_file(reference_python) and
            m.get('tests_sha256')==sha256_file(tests_file) and m.get('rubric_sha256')==rubric_sha256 and dependency_current)
