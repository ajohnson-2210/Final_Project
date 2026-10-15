"""Batch orchestration for model-result and baseline study folders."""
from __future__ import annotations
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import csv, json, re, shutil
from xml.etree import ElementTree

from adjudication import adjudicate_files
from common_test_resources import DEFAULT_COMMON_TESTS_ROOT, TEST_DESIGN_VERSION, find_common_test_file, validate_common_test_pack
from baseline_benchmark import build_baseline_comparison, build_frozen_semantic_comparison, load_test_spec, load_test_suite_metadata, test_cases_from_spec, write_reference_validation
from flow_mediation import write_flow_mediation
from flow_diagram import FlowDiagram
from human_review import HumanReviewQuestionnaireGenerator
from nl_flow_pipeline import NLFlowDiagramEncoderPipeline
from pseudocode_profiles import PseudocodeProfile
from scoring_engine import StudyScoringEngine
from semantic_evaluation import SemanticTestHarness
from study_rubric import LANGUAGE_VERSION, PIPELINE_VERSION, RUBRIC_VERSION, rubric_document
from study_analysis import aggregate_algorithm_folders
from dashboard_generation import generate_dashboards_for_completed_batch
from study_provenance import (declared_dependency_environment,find_reference_python,manifest_is_current,new_run_id,sha256_file,sha256_json,validate_baseline,validate_llm_results,write_preflight)

ALGORITHM_FOLDER_RE=re.compile(r"^Algorithm\s*-\s*(\d+)$",re.IGNORECASE)
BASELINE_SEMANTICALLY_COMPATIBLE_PIPELINE_VERSIONS=frozenset({"4.36", PIPELINE_VERSION})
# The scoring rubric document embeds pipeline_version, so its provenance hash changes
# even when the rubric content/semantics are otherwise identical. v4.36 and v4.37
# have identical rubric content apart from that embedded version field. Preserve the
# exact released v4.36 hash so real v4.36 baseline manifests can be recognised as
# current without weakening any of the source/reference/tests/dependency checks.
BASELINE_COMPATIBLE_RUBRIC_SHA256={
    "4.36":"72c285d390630dc4e1d341537de06f025b4a49b4eb023f94215f70ee0d6dfb72",
    PIPELINE_VERSION:sha256_json(rubric_document()),
}

@dataclass
class AlgorithmRunRecord:
    algorithm_id:int; dataset:str; source_file:str|None; artifact_directory:str; status:str; pipeline_success:bool
    action:str='PROCESSED'; error:str|None=None; reference_python:str|None=None; tests_file:str|None=None; score_file:str|None=None; questionnaire_file:str|None=None
    calibration_status:str|None=None; reference_validation_status:str|None=None; behavioural_agreement_percentage:float|None=None
    baseline_calibration_percentage:float|None=None; experimental_behavioural_percentage:float|None=None
    delta_from_baseline_percentage_points:float|None=None; comparison_to_baseline:str|None=None
    semantic_tests_evaluable:int|None=None; semantic_tests_passed:int|None=None; semantic_tests_not_evaluable:int|None=None
    semantic_boundary_probes_evaluable:int|None=None; semantic_boundary_probes_accepted:int|None=None
    semantic_boundary_probes_controlled_rejection:int|None=None; semantic_boundary_probes_incidental_failure:int|None=None
    semantic_boundary_probes_not_evaluable:int|None=None; semantic_boundary_variance_percentage:float|None=None

class StudyFolderError(ValueError): pass

def discover_algorithm_folders(parent:Path)->list[tuple[int,Path]]:
    parent=Path(parent)
    if not parent.is_dir(): raise StudyFolderError(f"Study folder does not exist: {parent}")
    found=[]
    for child in parent.iterdir():
        if child.is_dir() and (m:=ALGORITHM_FOLDER_RE.match(child.name)): found.append((int(m.group(1)),child))
    return sorted(found)

def _normalised_filename(name:str)->str:
    return " ".join(str(name).split()).casefold()

def expected_pseudocode_file(folder:Path,algorithm_id:int)->Path:
    expected_name=f"Algorithm {algorithm_id} Pseudocode.txt"; exact=folder/expected_name
    if exact.exists(): return exact
    target=_normalised_filename(expected_name)
    matches=[p for p in folder.iterdir() if p.is_file() and _normalised_filename(p.name)==target]
    if len(matches)==1: return matches[0]
    if len(matches)>1:
        raise StudyFolderError(f"Multiple files inside '{folder.name}' collapse to the expected pseudocode filename '{expected_name}'.")
    raise StudyFolderError(f"Expected '{expected_name}' inside '{folder.name}'.")

def _find_reference_python(folder:Path,algorithm_id:int)->Path|None:
    return find_reference_python(folder,algorithm_id)

def _find_tests_file(*folders:Path,algorithm_id:int)->Path|None:
    expected_name=f"Algorithm {algorithm_id} Tests.json"
    for folder in folders:
        if folder is None or not folder.exists(): continue
        exact=folder/expected_name
        if exact.exists(): return exact
        matches=[p for p in folder.glob('*.json') if p.name.casefold()==expected_name.casefold()]
        if len(matches)==1:return matches[0]
    return None

def _read_json(path:Path)->dict[str,Any]|None:
    try:
        v=json.loads(path.read_text(encoding='utf-8')); return v if isinstance(v,dict) else None
    except Exception:return None

def _archive_review_if_forced(artifact_directory:Path)->None:
    scoring=artifact_directory/'scoring'; review=scoring/'human_review.json'
    if not review.exists(): return
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'); archive=scoring/'review_archive'/stamp; archive.mkdir(parents=True,exist_ok=True)
    for name in ('human_review.json','final_score.json'):
        src=scoring/name
        if src.exists(): shutil.copy2(src,archive/name)

def _write_manifest(artifact_directory:Path,*,algorithm_id:int,dataset:str,source_type:str,source_file:Path,profile:PseudocodeProfile,is_baseline:bool,
                    reference_python:Path|None=None,tests_file:Path|None=None,processing_status:str='PENDING',run_id:str|None=None)->Path:
    artifact_directory.mkdir(parents=True,exist_ok=True); path=artifact_directory/'manifest.json'; previous=_read_json(path) or {}
    rubric_hash=sha256_json(rubric_document()); now=datetime.now(timezone.utc).isoformat()
    effective_run_id=run_id or previous.get('run_id') or new_run_id()
    same_run=previous.get('run_id')==effective_run_id
    dependency_environment=declared_dependency_environment(tests_file)
    manifest={'manifest_schema_version':'1.2','algorithm_id':algorithm_id,'dataset':dataset,'source_type':source_type,'source_file':source_file.name,
              'source_file_resolved':str(source_file.resolve()),'source_pseudocode_sha256':sha256_file(source_file),'artifact_directory':str(artifact_directory.resolve()),
              'pipeline_version':PIPELINE_VERSION,'language_version':LANGUAGE_VERSION,'rubric_version':RUBRIC_VERSION,'rubric_sha256':rubric_hash,'pseudocode_profile':profile.value,
              'is_baseline':is_baseline,'reference_python':str(reference_python.resolve()) if reference_python else None,'reference_python_sha256':sha256_file(reference_python),
              'tests_file':str(tests_file.resolve()) if tests_file else None,'tests_sha256':sha256_file(tests_file),
              'dependency_environment':dependency_environment,'dependency_environment_sha256':sha256_json(dependency_environment),'processing_status':processing_status,
              'run_id':effective_run_id,'started_at_utc':previous.get('started_at_utc') if same_run and previous.get('started_at_utc') else now,
              'completed_at_utc':now if processing_status not in {'PENDING','RUNNING'} else None,'updated_at_utc':now}
    path.write_text(json.dumps(manifest,indent=2),encoding='utf-8'); return path

def _has_explicit_expectation(spec:dict[str,Any])->bool:
    return any(k in spec and spec.get(k) is not None for k in ("expected_output","expected_return_code","expected_error_type"))


def _write_test_suite_evidence(artifact_directory:Path, tests_file:Path|None, specs:list[dict[str,Any]])->dict[str,Any]:
    metadata=load_test_suite_metadata(tests_file) if tests_file is not None else {}
    core_specs=[spec for spec in specs if str(spec.get("score_stream") or ((spec.get("semantic_test") or {}).get("score_stream")) or "CORE_BEHAVIOURAL").upper() == "CORE_BEHAVIOURAL"]
    categories=Counter(str(spec.get("category","NORMAL")).upper() for spec in core_specs)
    linked=Counter()
    seeded=0
    environment_controlled=0
    semantic_enabled=0
    semantic_disabled=0
    semantic_boundary_declared=0
    semantic_boundary_enabled=0
    pre_freeze_declared=0
    pre_freeze_enabled=0
    for spec in specs:
        semantic=spec.get("semantic_test")
        score_stream=str(spec.get("score_stream") or (semantic or {}).get("score_stream") or "CORE_BEHAVIOURAL").upper()
        if score_stream == "CORE_BEHAVIOURAL":
            for criterion in spec.get("criteria_links",[]) or []:
                linked[str(criterion)]+=1
        if spec.get("random_seed") is not None:
            seeded+=1
        if spec.get("environment"):
            environment_controlled+=1
        if score_stream == "SEMANTIC_BOUNDARY_PROBE":
            semantic_boundary_declared += 1
            if isinstance(semantic,dict) and semantic.get("enabled"):
                semantic_boundary_enabled += 1
            continue
        if score_stream == "PRE_FREEZE_VALIDATION":
            pre_freeze_declared += 1
            if isinstance(semantic,dict) and semantic.get("enabled"):
                pre_freeze_enabled += 1
            continue
        if isinstance(semantic,dict):
            if semantic.get("enabled"):
                semantic_enabled+=1
            else:
                semantic_disabled+=1
    evidence={
        'test_evidence_schema_version':'1.2',
        'test_design_version':metadata.get('test_design_version'),
        'test_spec_schema_version':metadata.get('test_spec_schema_version'),
        'tests_file':str(tests_file.resolve()) if tests_file is not None else None,
        'semantic_contract':metadata.get('semantic_contract'),
        'semantic_test_count':semantic_enabled,
        'interaction_or_reference_only_test_count':semantic_disabled,
        'semantic_boundary_probe_count':semantic_boundary_declared,
        'semantic_boundary_probe_enabled_count':semantic_boundary_enabled,
        'pre_freeze_validation_count':pre_freeze_declared,
        'pre_freeze_validation_enabled_count':pre_freeze_enabled,
        'core_test_count':len(core_specs),
        'declared_evidence_adequacy':metadata.get('evidence_adequacy','NOT_DECLARED'),
        'declared_evidence_summary':metadata.get('evidence_summary'),
        'declared_coverage_dimensions':metadata.get('coverage_dimensions',{}),
        'coverage_basis':metadata.get('coverage_basis'),
        'interpretation_guidance':metadata.get('interpretation_guidance'),
        'coverage_limitations':metadata.get('coverage_limitations',[]),
        'manual_review_targets':metadata.get('manual_review_targets',[]),
        'requires_pipeline_features':metadata.get('requires_pipeline_features',[]),
        'test_count':len(specs),
        'category_counts':dict(sorted(categories.items())),
        'criteria_link_counts':dict(sorted(linked.items())),
        'seeded_test_count':seeded,
        'environment_controlled_test_count':environment_controlled,
        'has_normal_or_branch_test':bool(categories.get('NORMAL') or categories.get('BRANCH')),
        'has_boundary_error_or_termination_test':bool(categories.get('BOUNDARY') or categories.get('ERROR_BEHAVIOUR') or categories.get('TERMINATION')),
        'has_state_mutation_test':bool(categories.get('STATE_MUTATION')),
    }
    artifact_directory.mkdir(parents=True,exist_ok=True)
    (artifact_directory/'test_suite_evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    return evidence


def _reference_oracle_eligible(validation:dict[str,Any]|None)->bool:
    """Return whether the frozen baseline reference is acceptable as a behavioural oracle."""
    return bool(validation and validation.get("status") in {"VALIDATED", "TRUSTED_REFERENCE"})


def _experimental_oracle_eligible(validation:dict[str,Any]|None, calibration:dict[str,Any]|None)->bool:
    """Experimental runs require both an accepted reference and a current evaluated baseline calibration."""
    return bool(
        _reference_oracle_eligible(validation)
        and calibration
        and calibration.get("status") == "EVALUATED"
        and calibration.get("calibration_score_percentage") is not None
    )


def _baseline_calibration_status(pipeline_status:str, validation:dict[str,Any]|None, benchmark:dict[str,Any]|None)->str:
    """Classify calibration availability independently from behavioural agreement.

    A measured calibration remains CALIBRATED even when behavioural tests disagree
    with the trusted reference. Pipeline FAILURE can therefore be a legitimate
    behavioural outcome when compilation succeeded and an evaluated calibration
    score was produced. PIPELINE_FAILURE is reserved for runs that never produced
    an evaluable calibration measurement.
    """
    validation_status=(validation or {}).get("status") or "NOT_EVALUATED"
    if validation_status == "FAILED":
        return "REFERENCE_FAILED"
    if validation_status == "NOT_EVALUATED":
        return "REFERENCE_NOT_EVALUATED"
    benchmark=benchmark or {}
    if benchmark.get("status") == "EVALUATED" and benchmark.get("calibration_score_percentage") is not None:
        return "CALIBRATED"
    if pipeline_status != "SUCCESS":
        return f"PIPELINE_{pipeline_status}"
    return "BEHAVIOURAL_NOT_EVALUATED"


def _load_baseline_calibration_context(baseline_root:Path|None, algorithm_id:int)->dict[str,Any]:
    if baseline_root is None:
        return {"current":False,"reason":"No baseline root supplied.","validation":None,"calibration":None,"manifest":None}
    art=Path(baseline_root)/'pseudocode'/f'Algorithm - {algorithm_id}'/'pipeline_artifacts'
    manifest=_read_json(art/'manifest.json')
    validation=_read_json(art/'baseline_reference_validation.json')
    calibration=_read_json(art/'baseline_calibration.json') or _read_json(art/'baseline_python_comparison.json')
    current=bool(
        manifest
        and manifest.get('pipeline_version')==PIPELINE_VERSION
        and manifest.get('pseudocode_profile')==BASELINE_CALIBRATION_PROFILE.value
        and calibration
        and calibration.get('status')=='EVALUATED'
        and calibration.get('calibration_score_percentage') is not None
    )
    if current:
        reason=None
    elif manifest is None:
        reason='No baseline calibration manifest was found; run the baseline calibration first.'
    elif manifest.get('pipeline_version')!=PIPELINE_VERSION:
        reason=f"Baseline calibration was produced by pipeline {manifest.get('pipeline_version')}, not {PIPELINE_VERSION}."
    elif manifest.get('pseudocode_profile')!=BASELINE_CALIBRATION_PROFILE.value:
        reason=f"Baseline calibration used profile {manifest.get('pseudocode_profile')}, not {BASELINE_CALIBRATION_PROFILE.value}."
    else:
        reason=(
            f"Baseline processing status is {manifest.get('processing_status')}; "
            "no evaluated behavioural calibration score is available for this algorithm."
        )
    return {"current":current,"reason":reason,"validation":validation,"calibration":calibration,"manifest":manifest}

def _oracle_source(specs:list[dict[str,Any]], reference_python:Path|None)->str|None:
    if not specs:return None
    explicit=sum(_has_explicit_expectation(s) for s in specs)
    if explicit==len(specs):return "EXPLICIT_TEST_EXPECTATIONS"
    if reference_python is not None and explicit:return "MIXED_EXPLICIT_AND_BASELINE_REFERENCE"
    if reference_python is not None:return "BASELINE_REFERENCE_PYTHON"
    return "EXPLICIT_TEST_EXPECTATIONS" if explicit else None

def _write_batch_failure(artifact_directory:Path,algorithm_id:int,dataset:str,error:Exception)->Path:
    artifact_directory.mkdir(parents=True,exist_ok=True); p=artifact_directory/'batch_failure.json'; p.write_text(json.dumps({'algorithm_id':algorithm_id,'dataset':dataset,'status':'FAILURE','error':str(error),'recorded_at_utc':datetime.now(timezone.utc).isoformat()},indent=2),encoding='utf-8'); return p


TERMINAL_PROCESSING_STATUSES = {"SUCCESS", "FAILURE", "EXPECTED_FAILURE", "REVIEW_REQUIRED"}
ELIGIBLE_BASELINE_PROCESSING_STATUSES = {"SUCCESS", "EXPECTED_FAILURE", "REVIEW_REQUIRED"}
BASELINE_CALIBRATION_PROFILE = PseudocodeProfile.AJ_DIALECT_STRICT


def _mark_manifest_batch_failure(artifact_directory:Path,error:Exception)->None:
    path=Path(artifact_directory)/'manifest.json'; manifest=_read_json(path)
    if not manifest:return
    now=datetime.now(timezone.utc).isoformat(); manifest['processing_status']='BATCH_FAILURE'; manifest['completed_at_utc']=now; manifest['updated_at_utc']=now; manifest['batch_error']=str(error)
    path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')


def _artifact_set_complete(artifact_directory:Path)->bool:
    """Return True only for a fully finalised, internally consistent algorithm run."""
    artifact_directory=Path(artifact_directory); manifest=_read_json(artifact_directory/'manifest.json') or {}; pipeline=_read_json(artifact_directory/'pipeline_report.json') or {}
    processing_status=manifest.get('processing_status'); pipeline_status=pipeline.get('status')
    if processing_status not in TERMINAL_PROCESSING_STATUSES or pipeline_status != processing_status:
        return False
    required=(
        artifact_directory/'pipeline_report.json',
        artifact_directory/'flow_mediation_analysis.json',
        artifact_directory/'scoring'/'automated_score.json',
        artifact_directory/'scoring'/'scoring_evidence.json',
        artifact_directory/'scoring'/'final_score.json',
        artifact_directory/'scoring'/'human_review_questionnaire.json',
        artifact_directory/'scoring'/'human_review_questionnaire.html',
    )
    if manifest.get('is_baseline'):
        required += (artifact_directory/'baseline_reference_validation.json', artifact_directory/'baseline_python_comparison.json', artifact_directory/'baseline_calibration.json')
    if not manifest.get('is_baseline'):
        required += (artifact_directory/'baseline_relative_comparison.json',)
    if not all(path.is_file() for path in required):
        return False
    final=_read_json(artifact_directory/'scoring'/'final_score.json')
    return bool(final and final.get('score_status'))


def _archive_existing_artifacts(artifact_directory:Path)->Path|None:
    """Move the previous current-view artefacts aside before a new run starts."""
    artifact_directory=Path(artifact_directory)
    if not artifact_directory.exists():return None
    children=[child for child in artifact_directory.iterdir() if child.name != 'run_history']
    if not children:return None
    previous=_read_json(artifact_directory/'manifest.json') or {}
    label=str(previous.get('run_id') or f"legacy-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    history=artifact_directory/'run_history'; history.mkdir(parents=True,exist_ok=True); archive=history/label
    suffix=1
    while archive.exists():
        suffix+=1; archive=history/f"{label}-{suffix}"
    archive.mkdir(parents=True,exist_ok=False)
    moved=[]
    for child in children:
        shutil.move(str(child),str(archive/child.name)); moved.append(child.name)
    (archive/'archive_metadata.json').write_text(json.dumps({
        'archived_at_utc':datetime.now(timezone.utc).isoformat(),
        'previous_run_id':previous.get('run_id'),
        'previous_pipeline_version':previous.get('pipeline_version'),
        'previous_processing_status':previous.get('processing_status'),
        'files_and_directories':moved,
    },indent=2),encoding='utf-8')
    return archive.resolve()


ANALYSIS_SNAPSHOT_FILES = (
    'study_preflight.json', 'study_preflight.csv',
    'batch_report.json', 'batch_report.csv',
    'algorithm_scores.json', 'algorithm_scores.csv',
    'criterion_evidence.csv', 'review_queue.csv',
    'flowchart_impact.csv', 'human_review_status.csv',
    'baseline_comparison.csv', 'dashboard_generation.json',
)

def _archive_analysis_snapshot(analysis_directory:Path,batch_run_id:str,report:dict[str,Any])->Path:
    """Preserve one immutable copy of the latest batch-level analysis outputs.

    The top-level ``study_analysis`` files remain the convenient latest view.  Each
    invocation is additionally copied into ``run_history/<batch_run_id>`` so that
    a later run cannot silently destroy the previous batch evidence.
    """
    analysis_directory=Path(analysis_directory)
    archive=analysis_directory/'run_history'/batch_run_id
    archive.mkdir(parents=True,exist_ok=False)
    copied=[]
    for name in ANALYSIS_SNAPSHOT_FILES:
        src=analysis_directory/name
        if src.is_file():
            shutil.copy2(src,archive/name); copied.append(name)
    dashboards=analysis_directory/'dashboards'
    if dashboards.is_dir():
        shutil.copytree(dashboards,archive/'dashboards')
        copied.append('dashboards/')
    metadata={
        'batch_run_id':batch_run_id,
        'pipeline_version':PIPELINE_VERSION,
        'rubric_version':RUBRIC_VERSION,
        'dataset':report.get('dataset'),
        'batch_type':report.get('batch_type'),
        'generated_at_utc':report.get('generated_at_utc'),
        'snapshot_created_at_utc':datetime.now(timezone.utc).isoformat(),
        'files':copied,
    }
    (archive/'run_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    latest={**metadata,'archive_directory':str(archive.resolve())}
    (analysis_directory/'latest_run.json').write_text(json.dumps(latest,indent=2),encoding='utf-8')
    return archive.resolve()

class StudyBatchProcessor:
    def __init__(self, common_tests_root:Path|None=None)->None:
        self.pipeline=NLFlowDiagramEncoderPipeline(); self.scorer=StudyScoringEngine(); self.questionnaire=HumanReviewQuestionnaireGenerator(); self.semantic_harness=SemanticTestHarness()
        self.common_tests_root=Path(common_tests_root) if common_tests_root is not None else DEFAULT_COMMON_TESTS_ROOT

    def _tests_for_algorithm(self, algorithm_id:int, *fallback_folders:Path)->Path|None:
        """Resolve the active pipeline-owned Common Tests pack first, then legacy local tests."""
        return find_common_test_file(algorithm_id, self.common_tests_root) or _find_tests_file(*fallback_folders, algorithm_id=algorithm_id)

    def common_test_pack_status(self)->dict[str,Any]:
        return validate_common_test_pack(self.common_tests_root).to_dict()
    def _drawio_layout_is_current(self, artifact_directory:Path)->bool:
        artifact_directory=Path(artifact_directory)
        drawio_path=artifact_directory/'flow_diagram.drawio'
        if not drawio_path.is_file():
            return False
        try:
            root=ElementTree.parse(drawio_path).getroot()
        except Exception:
            return False
        return root.attrib.get('nl_fdep_layout_revision') == self.pipeline.drawio_exporter.LAYOUT_REVISION

    def _flow_diagram_has_comment_nodes(self, artifact_directory:Path)->bool:
        """Return True when a legacy flow artefact still models comments as nodes.

        v4.37 treats comments as source/AST metadata only.  A previously generated
        flow containing COMMENT nodes must therefore be regenerated and rescored
        rather than accepted as current, otherwise comment-only structure can
        produce false flow-count/topology errors.
        """
        document=_read_json(Path(artifact_directory)/'flow_diagram.json') or {}
        nodes=document.get('nodes')
        if not isinstance(nodes,dict):
            return False
        return any(
            isinstance(node,dict) and str(node.get('node_type') or '').upper()=='COMMENT'
            for node in nodes.values()
        )

    def _refresh_drawio_from_canonical_flow(self, artifact_directory:Path)->bool:
        """Refresh only a stale editable DrawIO view from frozen canonical flow JSON.

        Resume-safe visual refresh: semantic artefacts, generated Python, scores,
        manifests, and human-review state remain untouched.
        """
        artifact_directory=Path(artifact_directory)
        flow_path=artifact_directory/'flow_diagram.json'
        if not flow_path.is_file() or self._drawio_layout_is_current(artifact_directory):
            return False
        flow_diagram=FlowDiagram.from_json(flow_path.read_text(encoding='utf-8'))
        self.pipeline.drawio_exporter.export(flow_diagram,artifact_directory/'flow_diagram.drawio')
        return True

    def refresh_llm_drawio_views(self, results_directory:Path)->dict[str,Any]:
        """Refresh stale DrawIO views for an experimental LLM dataset only.

        This deliberately never touches baseline artefacts or semantic/scoring
        files. It exists so opening an existing Human Review study also picks up
        silent v4.37 visual-layout fixes even when the LLM batch itself is not
        reprocessed in the current runner session.
        """
        root=Path(results_directory)
        candidates=[root]
        if (root/'Results').is_dir():
            candidates.insert(0,root/'Results')
        results_root=None
        for candidate in candidates:
            try:
                if discover_algorithm_folders(candidate):
                    results_root=candidate
                    break
            except StudyFolderError:
                continue
        if results_root is None:
            return {'checked':0,'refreshed':0,'skipped_baseline':0,'errors':[]}

        checked=refreshed=skipped_baseline=0
        errors=[]
        for _,folder in discover_algorithm_folders(results_root):
            art=folder/'pipeline_artifacts'
            manifest=_read_json(art/'manifest.json') or {}
            if manifest.get('is_baseline') is True:
                skipped_baseline += 1
                continue
            if not (art/'flow_diagram.json').is_file():
                continue
            checked += 1
            try:
                if self._refresh_drawio_from_canonical_flow(art):
                    refreshed += 1
            except Exception as exc:
                errors.append(f"{folder.name}: {exc}")
        return {
            'checked':checked,
            'refreshed':refreshed,
            'skipped_baseline':skipped_baseline,
            'errors':errors,
            'layout_revision':self.pipeline.drawio_exporter.LAYOUT_REVISION,
        }
    def _resume_status(self,artifact_directory:Path,source_file:Path,reference_python:Path|None,tests_file:Path|None,resume:bool,force:bool,profile:PseudocodeProfile|None=None,compatible_pipeline_versions:frozenset[str]|None=None)->str|None:
        if force:
            _archive_review_if_forced(artifact_directory); return None
        review=(artifact_directory/'scoring'/'human_review.json').exists()
        versions=compatible_pipeline_versions or frozenset({PIPELINE_VERSION})
        current=any(
            manifest_is_current(artifact_directory/'manifest.json',source_file=source_file,pipeline_version=version,rubric_version=RUBRIC_VERSION,
                                rubric_sha256=(BASELINE_COMPATIBLE_RUBRIC_SHA256.get(version)
                                               if compatible_pipeline_versions is not None
                                               else sha256_json(rubric_document())),
                                reference_python=reference_python,tests_file=tests_file,
                                pseudocode_profile=profile.value if profile is not None else None)
            for version in versions
            if (compatible_pipeline_versions is None or version in BASELINE_COMPATIBLE_RUBRIC_SHA256)
        )
        # A legacy graph that contains COMMENT nodes is not semantically current
        # even when its manifest fingerprints match.  Only those affected
        # algorithms are regenerated; comment-free v4.36/v4.37 baselines retain
        # the fast resume path.
        if current and self._flow_diagram_has_comment_nodes(artifact_directory):
            current=False
        complete=_artifact_set_complete(artifact_directory)
        if review and current and complete: return 'SKIPPED_REVIEWED'
        if review and current and not complete: return 'REVIEW_PROTECTED_INCOMPLETE'
        if review and not current: return 'REVIEW_PROTECTED_INPUT_CHANGED'
        if resume and current and complete:return 'SKIPPED_CURRENT'
        return None
    def process_llm_results(self,results_directory:Path,profile:PseudocodeProfile=PseudocodeProfile.GENERIC_COMPATIBILITY,baseline_root:Path|None=None,
                            open_visualisations:bool=False,resume:bool=True,force:bool=False)->dict[str,Any]:
        """Process experimental result folders against the frozen semantic pack.

        ``baseline_root`` is accepted only for API compatibility and is deliberately
        ignored for experimental expected-value generation and scoring.  The LLM
        path uses packaged static expectations only.
        """
        results_directory=Path(results_directory)
        dataset=results_directory.parent.name if results_directory.name.casefold()=='results' else results_directory.name
        analysis_dir=results_directory/'study_analysis'
        batch_run_id=new_run_id()
        preflight=validate_llm_results(results_directory,None,common_tests_root=self.common_tests_root)
        preflight['experimental_expected_value_policy']='STATIC_PREEXPERIMENT_EXPECTATIONS'
        preflight['runtime_baseline_reference_used']=False
        preflight_paths=write_preflight(preflight,analysis_dir)
        records=[]
        for aid,folder in discover_algorithm_folders(results_directory):
            art=folder/'pipeline_artifacts'; source=None
            try:
                source=expected_pseudocode_file(folder,aid)
                tests=self._tests_for_algorithm(aid,folder)
                ref=None
                # Visual-layout revisions are independent of semantic resume state.
                # Refresh any stale experimental DrawIO view from the frozen
                # canonical flow before classifying the artefact as current,
                # reviewed, incomplete, or input-changed.  This keeps protected
                # studies immutable semantically while still applying v4.37
                # routing fixes (for example, exhausting decision vertices before
                # fractional edge anchors).
                self._refresh_drawio_from_canonical_flow(art)
                skip=self._resume_status(art,source,None,tests,resume,force,profile)
                if skip:
                    # A manually returned human_review.json must refresh final_score.json even when
                    # the immutable pipeline artefacts are current and therefore skipped.
                    adjudicate_files(art/'scoring')
                    status=(_read_json(art/'pipeline_report.json') or {}).get('status','REVIEW_REQUIRED' if skip=='REVIEW_PROTECTED_INCOMPLETE' else skip)
                    comparison=_read_json(art/'baseline_relative_comparison.json') or ((_read_json(art/'scoring'/'final_score.json') or {}).get('benchmark') if (art/'scoring'/'final_score.json').exists() else None) or {}
                    records.append(AlgorithmRunRecord(
                        aid,dataset,str(source.resolve()),str(art.resolve()),status,status=='SUCCESS',action=skip,
                        reference_python=None,tests_file=str(tests.resolve()) if tests else None,
                        score_file=str((art/'scoring'/'automated_score.json').resolve()) if (art/'scoring'/'automated_score.json').exists() else None,
                        questionnaire_file=str((art/'scoring'/'human_review_questionnaire.html').resolve()) if (art/'scoring'/'human_review_questionnaire.html').exists() else None,
                        reference_validation_status=None,
                        baseline_calibration_percentage=comparison.get('frozen_reference_score_percentage',comparison.get('baseline_calibration_score_percentage')),
                        experimental_behavioural_percentage=comparison.get('experimental_behavioural_score_percentage'),
                        delta_from_baseline_percentage_points=comparison.get('delta_from_frozen_reference_percentage_points',comparison.get('delta_from_baseline_percentage_points')),
                        comparison_to_baseline=comparison.get('comparison_to_frozen_reference',comparison.get('comparison_to_baseline')),
                        semantic_tests_evaluable=((comparison.get('semantic_test_report') or {}).get('evaluable_tests')),
                        semantic_tests_passed=((comparison.get('semantic_test_report') or {}).get('passed_tests')),
                        semantic_tests_not_evaluable=((comparison.get('semantic_test_report') or {}).get('not_evaluable_tests')),
                        semantic_boundary_probes_evaluable=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('evaluable_probes')),
                        semantic_boundary_probes_accepted=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('out_of_domain_accepted')),
                        semantic_boundary_probes_controlled_rejection=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('controlled_rejection')),
                        semantic_boundary_probes_incidental_failure=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('incidental_failure')),
                        semantic_boundary_probes_not_evaluable=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('not_evaluable')),
                        semantic_boundary_variance_percentage=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('variance_percentage')),
                    )); continue
                specs=load_test_spec(tests) if tests else []
                core_specs=[spec for spec in specs if str(spec.get('score_stream') or ((spec.get('semantic_test') or {}).get('score_stream')) or 'CORE_BEHAVIOURAL').upper() == 'CORE_BEHAVIOURAL']
                boundary_specs=[spec for spec in specs if str(spec.get('score_stream') or ((spec.get('semantic_test') or {}).get('score_stream')) or 'CORE_BEHAVIOURAL').upper() == 'SEMANTIC_BOUNDARY_PROBE']
                provisional_specs=[spec for spec in specs if str(spec.get('score_stream') or ((spec.get('semantic_test') or {}).get('score_stream')) or 'CORE_BEHAVIOURAL').upper() == 'PRE_FREEZE_VALIDATION']
                suite_metadata=load_test_suite_metadata(tests) if tests else {}
                semantic_contract=suite_metadata.get('semantic_contract') if isinstance(suite_metadata.get('semantic_contract'),dict) else None
                semantic_mode=bool(semantic_contract and str(semantic_contract.get('expectation_policy'))=='STATIC_PREEXPERIMENT_EXPECTED_VALUES')
                run_id=new_run_id()
                _archive_existing_artifacts(art)
                _write_test_suite_evidence(art,tests,specs)
                _write_manifest(art,algorithm_id=aid,dataset=dataset,source_type='LLM_PSEUDOCODE',source_file=source,profile=profile,is_baseline=False,reference_python=None,tests_file=tests,processing_status='RUNNING',run_id=run_id)
                # Structural pipeline processing deliberately receives no behavioural
                # test cases; semantic evaluation below owns the experimental metric.
                pr=self.pipeline.run(pseudocode=source.read_text(encoding='utf-8'),output_directory=art,test_cases=[],open_visualisations=open_visualisations,pseudocode_profile=profile)
                write_flow_mediation(art,[])
                semantic_report=None
                if semantic_mode:
                    generated_program=art/'generated_program.py'
                    if generated_program.is_file():
                        semantic_report=self.semantic_harness.run(generated_program,aid,suite_metadata,specs).to_dict()
                    else:
                        semantic_report={
                            'semantic_report_schema_version':'1.2','runtime_expected_value_generation':False,
                            'program_path':None,'algorithm_id':aid,
                            'contract_version':str((semantic_contract or {}).get('contract_version') or '1.4'),
                            'evaluable_tests':0,'passed_tests':0,'failed_tests':0,'not_evaluable_tests':len(core_specs),
                            'accuracy_percentage':None,'pre_freeze_validation':{'declared_cases':len(provisional_specs),'evaluable_cases':0,'passed_cases':0,'failed_cases':0,'not_evaluable':len(provisional_specs),'accuracy_percentage':None,'included_in_core_behavioural_score':False,'included_in_baseline_calibration':False},'semantic_boundary':{'measure':'SEMANTIC_BOUNDARY_VARIANCE','declared_probes':len(boundary_specs),'evaluable_probes':0,'out_of_domain_accepted':0,'controlled_rejection':0,'incidental_failure':0,'not_evaluable':len(boundary_specs),'variance_percentage':None},'status':'NOT_EVALUABLE',
                            'reason':pr.error or 'No generated Python program was available for frozen task-semantic invocation.','results':[],
                        }
                else:
                    semantic_report={
                        'semantic_report_schema_version':'1.2','runtime_expected_value_generation':False,
                        'program_path':str((art/'generated_program.py').resolve()) if (art/'generated_program.py').exists() else None,
                        'algorithm_id':aid,'contract_version':None,'evaluable_tests':0,'passed_tests':0,'failed_tests':0,
                        'not_evaluable_tests':len(core_specs),'accuracy_percentage':None,'pre_freeze_validation':{'declared_cases':len(provisional_specs),'evaluable_cases':0,'passed_cases':0,'failed_cases':0,'not_evaluable':len(provisional_specs),'accuracy_percentage':None,'included_in_core_behavioural_score':False,'included_in_baseline_calibration':False},'semantic_boundary':{'measure':'SEMANTIC_BOUNDARY_VARIANCE','declared_probes':len(boundary_specs),'evaluable_probes':0,'out_of_domain_accepted':0,'controlled_rejection':0,'incidental_failure':0,'not_evaluable':len(boundary_specs),'variance_percentage':None},'status':'NOT_EVALUABLE',
                        'reason':'The selected test suite does not declare frozen static semantic expectations.','results':[],
                    }
                (art/'semantic_test_report.json').write_text(json.dumps(semantic_report,indent=2),encoding='utf-8')
                comparison=build_frozen_semantic_comparison(semantic_report,tests)
                comparison['semantic_contract']=semantic_contract
                comparison['semantic_contract_version']=(semantic_contract or {}).get('contract_version')
                comparison['runtime_baseline_reference_used']=False
                comparison['baseline_root_supplied_but_not_used']=bool(baseline_root is not None)
                (art/'baseline_relative_comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
                metadata={
                    'algorithm_id':aid,'dataset':dataset,'source_type':'llm_pseudocode',
                    'source_file':source.name,'source_file_resolved':str(source.resolve()),'is_baseline':False,
                    'experimental_expected_value_policy':'STATIC_PREEXPERIMENT_EXPECTATIONS',
                    'runtime_baseline_reference_used':False,
                }
                sp=self.scorer.write_outputs(art,metadata,benchmark=comparison)
                qp=self.questionnaire.write(art/'scoring',_read_json(sp['automated_score']) or {})
                adjudicate_files(art/'scoring')
                _write_manifest(art,algorithm_id=aid,dataset=dataset,source_type='LLM_PSEUDOCODE',source_file=source,profile=profile,is_baseline=False,reference_python=None,tests_file=tests,processing_status=pr.status,run_id=run_id)
                records.append(AlgorithmRunRecord(
                    aid,dataset,str(source.resolve()),str(art.resolve()),pr.status,pr.success,error=pr.error,
                    reference_python=None,tests_file=str(tests.resolve()) if tests else None,
                    score_file=str(sp['automated_score'].resolve()),questionnaire_file=str(qp['questionnaire_html'].resolve()),
                    reference_validation_status=None,
                    baseline_calibration_percentage=comparison.get('frozen_reference_score_percentage'),
                    experimental_behavioural_percentage=comparison.get('experimental_behavioural_score_percentage'),
                    delta_from_baseline_percentage_points=comparison.get('delta_from_frozen_reference_percentage_points'),
                    comparison_to_baseline=comparison.get('comparison_to_frozen_reference'),
                    semantic_tests_evaluable=((comparison.get('semantic_test_report') or {}).get('evaluable_tests')),
                    semantic_tests_passed=((comparison.get('semantic_test_report') or {}).get('passed_tests')),
                    semantic_tests_not_evaluable=((comparison.get('semantic_test_report') or {}).get('not_evaluable_tests')),
                    semantic_boundary_probes_evaluable=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('evaluable_probes')),
                    semantic_boundary_probes_accepted=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('out_of_domain_accepted')),
                    semantic_boundary_probes_controlled_rejection=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('controlled_rejection')),
                    semantic_boundary_probes_incidental_failure=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('incidental_failure')),
                    semantic_boundary_probes_not_evaluable=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('not_evaluable')),
                    semantic_boundary_variance_percentage=(((comparison.get('semantic_test_report') or {}).get('semantic_boundary') or {}).get('variance_percentage')),
                ))
            except Exception as e:
                _write_batch_failure(art,aid,dataset,e); _mark_manifest_batch_failure(art,e)
                records.append(AlgorithmRunRecord(
                    aid,dataset,str(source.resolve()) if source else None,str(art.resolve()),'FAILURE',False,error=str(e),
                    comparison_to_baseline='NOT_EVALUABLE',
                ))
        records=sorted(records,key=lambda r:r.algorithm_id)
        batch=self._write_batch_reports(analysis_dir,dataset,records,'LLM_RESULTS',batch_run_id)
        batch['preflight']=preflight_paths
        batch['common_test_pack']=self.common_test_pack_status()
        batch['analysis_outputs']=aggregate_algorithm_folders(results_directory,analysis_dir)
        batch['dashboards']=generate_dashboards_for_completed_batch(results_directory,analysis_dir,'LLM_RESULTS')
        batch['history_directory']=str(_archive_analysis_snapshot(analysis_dir,batch_run_id,batch['report']))
        return batch

    def process_baseline(self,baseline_root:Path,profile:PseudocodeProfile=PseudocodeProfile.AJ_DIALECT_STRICT,open_visualisations:bool=False,resume:bool=True,force:bool=False)->dict[str,Any]:
        baseline_root=Path(baseline_root); pseudo=baseline_root/'pseudocode'; py=baseline_root/'python'
        if not pseudo.is_dir() or not py.is_dir(): raise StudyFolderError("Baseline root must contain 'pseudocode' and 'python' folders.")
        analysis_dir=baseline_root/'study_analysis'; batch_run_id=new_run_id(); preflight=validate_baseline(baseline_root,common_tests_root=self.common_tests_root); preflight_paths=write_preflight(preflight,analysis_dir); records=[]
        for aid,pfolder in discover_algorithm_folders(pseudo):
            art=pfolder/'pipeline_artifacts'; source=None
            try:
                source=expected_pseudocode_file(pfolder,aid); rfolder=py/f'Algorithm - {aid}'; ref=_find_reference_python(rfolder,aid) if rfolder.is_dir() else None; tests=self._tests_for_algorithm(aid,rfolder,pfolder)
                skip=self._resume_status(art,source,ref,tests,resume,force,profile,BASELINE_SEMANTICALLY_COMPATIBLE_PIPELINE_VERSIONS)
                if skip:
                    # Baseline readiness/calibration is read-only for an already-current
                    # baseline artefact set. Do not refresh DrawIO, re-adjudicate scoring,
                    # touch manifests, or otherwise rewrite anything under pipeline_artifacts.
                    # Experimental/LLM resume refresh remains intentionally separate.
                    status=(_read_json(art/'pipeline_report.json') or {}).get('status','REVIEW_REQUIRED' if skip=='REVIEW_PROTECTED_INCOMPLETE' else skip)
                    validation=_read_json(art/'baseline_reference_validation.json'); benchmark=_read_json(art/'baseline_calibration.json') or _read_json(art/'baseline_python_comparison.json'); calibration=_baseline_calibration_status(status,validation,benchmark)
                    records.append(AlgorithmRunRecord(aid,'Baseline',str(source.resolve()),str(art.resolve()),status,status=='SUCCESS',action=skip,reference_python=str(ref.resolve()) if ref else None,tests_file=str(tests.resolve()) if tests else None,score_file=str((art/'scoring'/'automated_score.json').resolve()) if (art/'scoring'/'automated_score.json').exists() else None,questionnaire_file=str((art/'scoring'/'human_review_questionnaire.html').resolve()) if (art/'scoring'/'human_review_questionnaire.html').exists() else None,calibration_status=calibration,reference_validation_status=(validation or {}).get('status'),behavioural_agreement_percentage=(benchmark or {}).get('behavioural_agreement_percentage'),baseline_calibration_percentage=(benchmark or {}).get('calibration_score_percentage'))); continue
                specs=load_test_spec(tests) if tests else []; suite_metadata=load_test_suite_metadata(tests) if tests else {}; reference_title=suite_metadata.get('algorithm_title'); run_id=new_run_id()
                core_specs=[spec for spec in specs if str(spec.get('score_stream') or ((spec.get('semantic_test') or {}).get('score_stream')) or 'CORE_BEHAVIOURAL').upper() == 'CORE_BEHAVIOURAL']
                _archive_existing_artifacts(art)
                _write_test_suite_evidence(art,tests,specs)
                _write_manifest(art,algorithm_id=aid,dataset='Baseline',source_type='BASELINE_PSEUDOCODE',source_file=source,profile=profile,is_baseline=True,reference_python=ref,tests_file=tests,processing_status='RUNNING',run_id=run_id)
                reference_validation=write_reference_validation(art/'baseline_reference_validation.json',ref,core_specs,reference_title)
                oracle_ref=ref if _reference_oracle_eligible(reference_validation) else None
                usable_specs=core_specs if oracle_ref is not None else [spec for spec in core_specs if _has_explicit_expectation(spec)]
                cases,oracle=test_cases_from_spec(usable_specs,reference_python=oracle_ref,reference_title=reference_title)
                pr=self.pipeline.run(pseudocode=source.read_text(encoding='utf-8'),output_directory=art,test_cases=cases,open_visualisations=open_visualisations,pseudocode_profile=profile)
                write_flow_mediation(art,cases)
                generated=_read_json(art/'test_report.json') if (art/'test_report.json').exists() else None
                baseline_semantic_report=None
                if (art/'generated_program.py').is_file() and suite_metadata.get('semantic_contract'):
                    baseline_semantic_report=self.semantic_harness.run(art/'generated_program.py',aid,suite_metadata,specs).to_dict()
                    (art/'semantic_test_report.json').write_text(json.dumps(baseline_semantic_report,indent=2),encoding='utf-8')
                benchmark=build_baseline_comparison(generated,ref,tests,oracle,generated_python=art/'generated_program.py',reference_title=reference_title); benchmark['reference_validation']=reference_validation
                if baseline_semantic_report is not None:
                    benchmark['semantic_boundary']=baseline_semantic_report.get('semantic_boundary')
                    benchmark['pre_freeze_validation']=baseline_semantic_report.get('pre_freeze_validation')
                    benchmark['core_semantic_validation']={k:baseline_semantic_report.get(k) for k in ('evaluable_tests','passed_tests','failed_tests','not_evaluable_tests','accuracy_percentage')}
                benchmark['oracle_source']=_oracle_source(usable_specs,oracle_ref); benchmark['reference_oracle_eligible']=oracle_ref is not None
                if oracle_ref is None and ref is not None:
                    benchmark['oracle_block_reason']=f"Reference Python was not used to derive omitted expectations because reference assurance status is {reference_validation.get('status')}."
                if reference_validation.get('status') in {'FAILED','NOT_EVALUATED'}:
                    benchmark['status']='REFERENCE_NOT_ACCEPTED'; benchmark['reason']='The baseline reference was not accepted as the trusted behavioural oracle.'; benchmark['behavioural_agreement_percentage']=None; benchmark['calibration_score_percentage']=None
                (art/'baseline_python_comparison.json').write_text(json.dumps(benchmark,indent=2),encoding='utf-8')
                (art/'baseline_calibration.json').write_text(json.dumps(benchmark,indent=2),encoding='utf-8')
                metadata={'algorithm_id':aid,'dataset':'Baseline','source_type':'baseline_pseudocode','source_file':source.name,'source_file_resolved':str(source.resolve()),'is_baseline':True}
                sp=self.scorer.write_outputs(art,metadata,benchmark=benchmark); qp=self.questionnaire.write(art/'scoring',_read_json(sp['automated_score']) or {}); adjudicate_files(art/'scoring')
                _write_manifest(art,algorithm_id=aid,dataset='Baseline',source_type='BASELINE_PSEUDOCODE',source_file=source,profile=profile,is_baseline=True,reference_python=ref,tests_file=tests,processing_status=pr.status,run_id=run_id)
                calibration=_baseline_calibration_status(pr.status,reference_validation,benchmark)
                records.append(AlgorithmRunRecord(aid,'Baseline',str(source.resolve()),str(art.resolve()),pr.status,pr.success,error=pr.error,reference_python=str(ref.resolve()) if ref else None,tests_file=str(tests.resolve()) if tests else None,score_file=str(sp['automated_score'].resolve()),questionnaire_file=str(qp['questionnaire_html'].resolve()),calibration_status=calibration,reference_validation_status=reference_validation.get('status'),behavioural_agreement_percentage=benchmark.get('behavioural_agreement_percentage'),baseline_calibration_percentage=benchmark.get('calibration_score_percentage')))
            except Exception as e:
                _write_batch_failure(art,aid,'Baseline',e); _mark_manifest_batch_failure(art,e); records.append(AlgorithmRunRecord(aid,'Baseline',str(source.resolve()) if source else None,str(art.resolve()),'FAILURE',False,error=str(e),calibration_status='PIPELINE_FAILURE'))
        records=sorted(records,key=lambda r:r.algorithm_id)
        batch=self._write_batch_reports(analysis_dir,'Baseline',records,'BASELINE',batch_run_id); batch['preflight']=preflight_paths; batch['common_test_pack']=self.common_test_pack_status(); batch['analysis_outputs']=aggregate_algorithm_folders(pseudo,analysis_dir); batch['dashboards']=generate_dashboards_for_completed_batch(pseudo,analysis_dir,'BASELINE'); batch['history_directory']=str(_archive_analysis_snapshot(analysis_dir,batch_run_id,batch['report'])); return batch

    @staticmethod
    def _write_batch_reports(analysis_directory:Path,dataset:str,records:list[AlgorithmRunRecord],batch_type:str,batch_run_id:str)->dict[str,Any]:
        analysis_directory.mkdir(parents=True,exist_ok=True)
        baseline_scores=[r.baseline_calibration_percentage for r in records if r.baseline_calibration_percentage is not None]
        experimental_scores=[r.experimental_behavioural_percentage for r in records if r.experimental_behavioural_percentage is not None]
        deltas=[r.delta_from_baseline_percentage_points for r in records if r.delta_from_baseline_percentage_points is not None]
        semantic_evaluable=sum(int(r.semantic_tests_evaluable or 0) for r in records)
        semantic_passed=sum(int(r.semantic_tests_passed or 0) for r in records)
        semantic_not_evaluable=sum(int(r.semantic_tests_not_evaluable or 0) for r in records)
        boundary_evaluable=sum(int(r.semantic_boundary_probes_evaluable or 0) for r in records)
        boundary_accepted=sum(int(r.semantic_boundary_probes_accepted or 0) for r in records)
        boundary_controlled=sum(int(r.semantic_boundary_probes_controlled_rejection or 0) for r in records)
        boundary_incidental=sum(int(r.semantic_boundary_probes_incidental_failure or 0) for r in records)
        boundary_not_evaluable=sum(int(r.semantic_boundary_probes_not_evaluable or 0) for r in records)
        algorithm_boundary_variances=[float(r.semantic_boundary_variance_percentage) for r in records if r.semantic_boundary_variance_percentage is not None]
        report={
            'batch_schema_version':'1.5',
            'batch_run_id':batch_run_id,
            'pipeline_version':PIPELINE_VERSION,
            'rubric_version':RUBRIC_VERSION,
            'batch_type':batch_type,
            'dataset':dataset,
            'generated_at_utc':datetime.now(timezone.utc).isoformat(),
            'algorithm_count':len(records),
            'baseline_algorithm_count':len(records) if batch_type=='BASELINE' else None,
            'baseline_expected_algorithm_ids':[r.algorithm_id for r in records] if batch_type=='BASELINE' else None,
            'status_counts':dict(sorted(Counter(r.status for r in records).items())),
            'pipeline_status_counts':dict(sorted(Counter(r.status for r in records).items())),
            'calibration_status_counts':dict(sorted(Counter(r.calibration_status for r in records if r.calibration_status).items())),
            'comparison_to_baseline_counts':dict(sorted(Counter(r.comparison_to_baseline for r in records if r.comparison_to_baseline).items())),
            'action_counts':dict(sorted(Counter(r.action for r in records).items())),
            'evaluated_baseline_calibration_count':len(baseline_scores),
            'baseline_calibration_unavailable_count':(len(records)-len(baseline_scores)) if batch_type=='BASELINE' else None,
            'mean_baseline_calibration_percentage':round(sum(baseline_scores)/len(baseline_scores),2) if baseline_scores else None,
            'mean_experimental_behavioural_percentage':round(sum(experimental_scores)/len(experimental_scores),2) if experimental_scores else None,
            'mean_delta_from_baseline_percentage_points':round(sum(deltas)/len(deltas),2) if deltas else None,
            'semantic_tests_evaluable':semantic_evaluable if batch_type=='LLM_RESULTS' else None,
            'semantic_tests_passed':semantic_passed if batch_type=='LLM_RESULTS' else None,
            'semantic_tests_not_evaluable':semantic_not_evaluable if batch_type=='LLM_RESULTS' else None,
            'semantic_test_accuracy_percentage':round((semantic_passed/semantic_evaluable)*100,2) if batch_type=='LLM_RESULTS' and semantic_evaluable else None,
            'semantic_boundary_probes_evaluable':boundary_evaluable if batch_type=='LLM_RESULTS' else None,
            'semantic_boundary_probes_accepted':boundary_accepted if batch_type=='LLM_RESULTS' else None,
            'semantic_boundary_probes_controlled_rejection':boundary_controlled if batch_type=='LLM_RESULTS' else None,
            'semantic_boundary_probes_incidental_failure':boundary_incidental if batch_type=='LLM_RESULTS' else None,
            'semantic_boundary_probes_not_evaluable':boundary_not_evaluable if batch_type=='LLM_RESULTS' else None,
            'semantic_boundary_variance_percentage':round((boundary_accepted/boundary_evaluable)*100,2) if batch_type=='LLM_RESULTS' and boundary_evaluable else None,
            'mean_algorithm_semantic_boundary_variance_percentage':round(sum(algorithm_boundary_variances)/len(algorithm_boundary_variances),2) if batch_type=='LLM_RESULTS' and algorithm_boundary_variances else None,
            'algorithms':[asdict(r) for r in records],
        }
        jp=analysis_directory/'batch_report.json'; cp=analysis_directory/'batch_report.csv'; jp.write_text(json.dumps(report,indent=2),encoding='utf-8')
        fields=list(asdict(records[0]).keys()) if records else list(AlgorithmRunRecord.__dataclass_fields__)
        with cp.open('w',encoding='utf-8',newline='') as h:
            w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); [w.writerow(asdict(r)) for r in records]
        return {'report':report,'json_path':str(jp.resolve()),'csv_path':str(cp.resolve())}

