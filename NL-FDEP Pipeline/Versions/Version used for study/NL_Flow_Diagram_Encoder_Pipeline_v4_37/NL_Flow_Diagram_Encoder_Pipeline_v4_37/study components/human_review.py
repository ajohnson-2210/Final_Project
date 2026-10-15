"""Generate portable human-review questionnaire artefacts from automated scores."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
import json


def _review_template(score_document: dict[str, Any]) -> dict[str, Any]:
    criteria = []
    for stage_key, stage in score_document.get("stages", {}).items():
        for criterion in stage.get("criteria", []):
            auto = criterion.get("automated_assessment", {})
            criteria.append({
                "stage_key": stage_key,
                "stage_name": stage.get("stage_name"),
                "criterion_id": criterion.get("criterion_id"),
                "question": criterion.get("question"),
                "automated_score": auto.get("score"),
                "automated_status": auto.get("status"),
                "automated_confidence": auto.get("confidence"),
                "automated_justification": auto.get("justification"),
                "evidence": deepcopy(criterion.get("evidence", [])),
                "human_assessment": {
                    "score": None,
                    "agreement_with_automated_score": None,
                    "semantic_issue": None,
                    "reviewer_justification": "",
                },
            })

    gate = score_document.get("source_sufficiency", {})
    evidence_gate = score_document.get("behavioural_evidence_adequacy", {})
    return {
        "questionnaire_schema_version": "1.3",
        "rubric_version": score_document.get("rubric_version"),
        "pipeline_version": score_document.get("pipeline_version"),
        "algorithm": deepcopy(score_document.get("algorithm", {})),
        "instructions": (
            "Review the source and generated artefacts, then independently assess every criterion using the same "
            "0-2/NA scale. The automated assessment is shown as evidence but must not replace reviewer judgement. "
            "Automated and human rubric scores are retained side by side; after all sixteen human criteria are completed, "
            "the combined rubric score is the equal-weight mean of the automated and human overall rubric percentages."
        ),
        "reviewer": {
            "reviewer_id": "",
            "reviewer_name": "",
            "reviewed_at_utc": None,
            "overall_reviewer_confidence": None,
        },
        "source_sufficiency": {
            "criterion_id": gate.get("criterion_id"),
            "question": gate.get("question"),
            "automated_result": gate.get("result"),
            "automated_justification": gate.get("justification"),
            "human_result": None,
            "agreement_with_automated_result": None,
            "reviewer_justification": "",
        },
        "behavioural_evidence_adequacy": {
            "criterion_id": evidence_gate.get("criterion_id"),
            "question": evidence_gate.get("question"),
            "automated_result": evidence_gate.get("result"),
            "summary": evidence_gate.get("summary"),
            "test_counts": deepcopy(evidence_gate.get("test_counts", {})),
            "coverage_dimensions": deepcopy(evidence_gate.get("coverage_dimensions", {})),
            "strengths": deepcopy(evidence_gate.get("strengths", [])),
            "limitations": deepcopy(evidence_gate.get("limitations", [])),
            "coverage_basis": evidence_gate.get("coverage_basis"),
            "interpretation": evidence_gate.get("interpretation"),
            "human_result": None,
            "agreement_with_automated_result": None,
            "reviewer_justification": "",
        },
        "task_semantic_evaluation": ({
            "contract": deepcopy(score_document.get("semantic_contract")),
            "automated_evidence": deepcopy(score_document.get("semantic_behavioural_evidence")),
            "instruction": (
                "Judge the original model pseudocode against the task-semantic contract. "
                "Use the same questions whether automated semantic execution succeeded, failed, or was NOT_EVALUABLE; "
                "the automated evidence is supporting evidence and must not replace independent human judgement."
            ),
            "human_assessment": {
                "required_inputs_represented": None,
                "core_algorithm_logic": None,
                "required_output_semantics_represented": None,
                "edge_and_domain_handling": None,
                "overall_semantic_assessment": None,
                "reviewer_justification": "",
            },
        } if score_document.get("semantic_contract") else None),
        "benchmark_validation": ({
            "question": "Is the supplied baseline Python an appropriate reference implementation for this algorithm?",
            "automated_reference_validation": deepcopy((score_document.get("benchmark") or {}).get("reference_validation")),
            "human_reference_appropriate": None,
            "reviewer_justification": "",
        } if (score_document.get("benchmark") or {}).get("is_baseline") else None),
        "criteria": criteria,
        "overall_review": {
            "material_semantic_error_not_captured": None,
            "first_semantic_loss_stage": None,
            "final_python_behaviourally_faithful": None,
            "additional_observations": "",
        },
    }



JUSTIFICATION_PRESETS = [
    "Evidence supports the selected score.",
    "Evidence mostly supports the selected score, with minor limitations.",
    "Evidence shows partial fulfilment of the criterion.",
    "Evidence does not support the criterion.",
    "Insufficient evidence to make a confident judgement.",
    "Not applicable to this algorithm.",
]

REVIEW_COMMENT_PRESETS = [
    "Evidence supports the selected assessment.",
    "Evidence mostly supports the selected assessment, with minor limitations.",
    "Evidence shows partial support for the selected assessment.",
    "Evidence does not support the selected assessment.",
    "Insufficient evidence to make a confident judgement.",
    "Not applicable to this algorithm.",
]

def _review_comment_select(field_id: str, label: str, rows: int = 3) -> str:
    options = "\n".join(
        f'<option value="{escape(option, quote=True)}">{escape(option)}</option>'
        for option in REVIEW_COMMENT_PRESETS
    )
    return (
        f'<label>{escape(label)}\n'
        f'  <select id="{field_id}_choice" onchange="toggleReviewComment(\'{field_id}\')">\n'
        f'    {options}\n'
        f'    <option value="__OTHER__">Other — add specific comment</option>\n'
        f'  </select>\n'
        f'</label>\n'
        f'<div id="{field_id}_other_wrap" class="custom-justification">\n'
        f'  <label>Specific Comment\n'
        f'    <textarea id="{field_id}_other" rows="{rows}"></textarea>\n'
        f'  </label>\n'
        f'</div>'
    )

def _criterion_card(index: int, item: dict[str, Any]) -> str:
    cid = escape(str(item["criterion_id"]))
    question = escape(str(item["question"]))
    stage = escape(str(item["stage_name"]))
    score = item.get("automated_score")
    score_text = "N/A" if score is None else f"{score}/2"
    auto_status = escape(str(item.get("automated_status")))
    confidence = escape(str(item.get("automated_confidence")))
    justification = escape(str(item.get("automated_justification")))
    evidence = escape(json.dumps(item.get("evidence", []), indent=2))
    name = f"criterion_{index}"
    preset_options = "\n".join(
        f'<option value="{escape(option, quote=True)}">{escape(option)}</option>'
        for option in JUSTIFICATION_PRESETS
    )
    return f'''\n    <section class="criterion" data-index="{index}" data-criterion-id="{cid}">\n      <h3>{cid} · {stage}</h3>\n      <p class="question">{question}</p>\n      <div class="auto"><strong>Automated assessment:</strong> {score_text} · {auto_status} · confidence {confidence}</div>\n      <p><strong>Automated justification:</strong> {justification}</p>\n      <details><summary>Evidence</summary><pre>{evidence}</pre></details>\n      <fieldset>\n        <legend>Human score</legend>\n        <label><input type="radio" name="{name}_score" value="2"> 2 — fully satisfied</label>\n        <label><input type="radio" name="{name}_score" value="1"> 1 — partially satisfied / uncertain</label>\n        <label><input type="radio" name="{name}_score" value="0"> 0 — material semantic discrepancy</label>\n        <label><input type="radio" name="{name}_score" value="NA"> N/A — not legitimately assessable</label>\n      </fieldset>\n      <label>Agreement with automated score\n        <select id="{name}_agreement" name="{name}_agreement">\n          <option value="">Select…</option>\n          <option>AGREE</option><option>PARTIALLY_AGREE</option><option>DISAGREE</option>\n        </select>\n      </label>\n      <label>Semantic issue identified?\n        <select id="{name}_semantic" name="{name}_semantic">\n          <option value="">Select…</option><option value="false">No</option><option value="true">Yes</option>\n        </select>\n      </label>\n      <label>Reviewer justification\n        <select id="{name}_justification_choice" name="{name}_justification_choice" onchange="toggleCriterionJustification({index})">\n          {preset_options}\n          <option value="__OTHER__">Other — add specific comment</option>\n        </select>\n      </label>\n      <div id="{name}_justification_other_wrap" class="custom-justification">\n        <label>Specific comment\n          <textarea id="{name}_justification_other" name="{name}_justification_other" rows="3"></textarea>\n        </label>\n      </div>\n    </section>\n    '''


def _html_document(
    template: dict[str, Any],
    *,
    reviewer_identity: dict[str, str] | None = None,
    save_endpoint: str | None = None,
    read_only: bool = False,
    ownership_notice: str = "",
) -> str:
    '''Render the verbose questionnaire in portable or local-service mode.'''
    template = deepcopy(template)
    reviewer = template.setdefault("reviewer", {})
    reviewer.setdefault("reviewer_id", "")
    reviewer.setdefault("reviewer_name", "")
    if reviewer_identity:
        reviewer["reviewer_id"] = reviewer_identity.get("reviewer_id", "")
        reviewer["reviewer_name"] = reviewer_identity.get("reviewer_name", "")

    algorithm = template.get("algorithm", {})
    title = f"Algorithm {algorithm.get('algorithm_id', '?')} human review"
    cards = "\n".join(_criterion_card(i, c) for i, c in enumerate(template.get("criteria", [])))
    benchmark = template.get("benchmark_validation")
    benchmark_html = ""
    if benchmark:
        automated = escape(json.dumps(benchmark.get("automated_reference_validation"), indent=2))
        benchmark_html = f'''<h2>Baseline Reference Validation</h2><section class="criterion"><p class="question">{escape(str(benchmark.get('question')))}</p><details><summary>Automated reference validation</summary><pre>{automated}</pre></details><label>Human assessment <select id="baseline_reference_appropriate"><option value="">Select…</option><option>YES</option><option>PARTIALLY</option><option>NO</option><option>UNABLE_TO_DETERMINE</option></select></label><label>Reviewer justification <textarea id="baseline_reference_justification" rows="3"></textarea></label></section>'''
    semantic = template.get("task_semantic_evaluation")
    semantic_html = ""
    if semantic:
        contract = escape(json.dumps(semantic.get("contract"), indent=2, ensure_ascii=False))
        automated_semantic = escape(json.dumps(semantic.get("automated_evidence"), indent=2, ensure_ascii=False))
        semantic_comment = _review_comment_select("sem_justification", "Reviewer Semantic Justification", rows=4)
        semantic_html = f'''<h2>Task-Semantic Evaluation</h2><section class="criterion"><p>{escape(str(semantic.get('instruction')))}</p><details open><summary>Canonical Task-Semantic Contract</summary><pre>{contract}</pre></details><details><summary>Automated Semantic Evidence</summary><pre>{automated_semantic}</pre></details><label>Are the required task inputs represented? <select id="sem_inputs"><option value="">Select…</option><option>YES</option><option>PARTIAL</option><option>NO</option><option>UNABLE_TO_DETERMINE</option></select></label><label>Core Algorithm Logic <select id="sem_logic"><option value="">Select…</option><option>CORRECT</option><option>MOSTLY_CORRECT</option><option>PARTIAL</option><option>INCORRECT</option><option>NOT_DETERMINABLE</option></select></label><label>Are the required output semantics represented? <select id="sem_output"><option value="">Select…</option><option>YES</option><option>PARTIAL</option><option>NO</option><option>UNABLE_TO_DETERMINE</option></select></label><label>Edge/Domain Handling <select id="sem_edge"><option value="">Select…</option><option>YES</option><option>PARTIAL</option><option>NO</option><option>NOT_APPLICABLE</option><option>UNABLE_TO_DETERMINE</option></select></label><label>Overall Semantic Assessment <select id="sem_overall"><option value="">Select…</option><option>CORRECT</option><option>MOSTLY_CORRECT</option><option>PARTIAL</option><option>INCORRECT</option><option>NOT_DETERMINABLE</option></select></label>{semantic_comment}</section>'''
    template_json = json.dumps(template).replace("</", "<\\/")
    endpoint_json = json.dumps(save_endpoint)
    read_only_json = "true" if read_only else "false"
    fetch_fallback_message_json = json.dumps(
        "Direct save service is unavailable. A backup human_review.json has been downloaded so your completed review is not lost. "
        "Keep or reopen the NL-FDEP Human Review window, then save again, or place the backup in this algorithm's "
        "pipeline_artifacts/scoring folder.",
        ensure_ascii=False,
    )
    ownership_html = f'<div class="warning">{escape(ownership_notice)}</div>' if ownership_notice else ""
    primary_button = "Save review" if save_endpoint else "Download completed human_review.json"
    portable_notice = (
        "Save writes directly to this algorithm's scoring folder and immediately refreshes adjudication. The NL-FDEP Human Review launcher supplies the local save service; closing its window with X minimises it so saving remains available. Use End Review Session only after your questionnaire tabs are saved."
        if save_endpoint else
        "The downloaded JSON preserves the automated evidence and your independent human assessment. "
        "Place it in this algorithm's pipeline_artifacts/scoring/ folder."
    )
    g1_comment_html = _review_comment_select("g1_justification", "Reviewer Justification", rows=3)
    g2_comment_html = _review_comment_select("g2_justification", "Reviewer Evidence Comment", rows=3)
    return f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<style>
body{{font-family:Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 18px;line-height:1.45;color:#243240;background:#f7f9fc}}
h1{{line-height:1.2;color:#173b5e;border-bottom:3px solid #3f7cac;padding-bottom:10px}}
h2{{line-height:1.2;color:#fff;background:#2f6690;padding:10px 14px;border-radius:7px;margin-top:28px;box-shadow:0 1px 2px rgba(0,0,0,.08)}}
h3{{line-height:1.2;color:#24506f}}
.meta,.auto{{background:#eaf2f8;padding:10px 12px;border-radius:6px;border-left:4px solid #3f7cac}}
.criterion{{background:#fff;border:1px solid #ccd7e2;border-left:5px solid #6c9bc3;border-radius:8px;padding:16px;margin:16px 0;box-shadow:0 1px 3px rgba(20,45,70,.06)}}
.question{{font-size:1.05rem;font-weight:600;color:#173b5e}} fieldset{{border:0;padding:8px 0;display:grid;gap:6px}}
label{{display:block;margin:10px 0;font-weight:600}} select,textarea,input[type=text]{{font:inherit;max-width:100%;box-sizing:border-box;border:1px solid #b8c7d6;border-radius:5px;background:#fff}}
textarea{{width:100%;padding:8px;font-weight:400}} select,input[type=text]{{padding:7px;font-weight:400}}
select:focus,textarea:focus,input[type=text]:focus{{outline:2px solid #8ab6d6;outline-offset:1px;border-color:#3f7cac}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f8fafc;padding:10px;border:1px solid #dce5ed;border-radius:5px}}
details summary{{cursor:pointer;color:#24506f;font-weight:600}}
button{{font:inherit;font-weight:600;padding:10px 16px;margin:8px 8px 8px 0;cursor:pointer;border-radius:6px;border:1px solid #2f6690;background:#2f6690;color:#fff}}
button#print{{background:#fff;color:#2f6690}} button:hover{{filter:brightness(.96)}} .notice{{color:#5f6f7f}}
.warning{{background:#fff3cd;border:1px solid #e0b84f;border-radius:6px;padding:12px;margin:14px 0}}
.status{{display:none;border-radius:6px;padding:10px 12px;margin:12px 0}} .status.ok{{display:block;background:#e8f5e9;border-left:4px solid #4f8a5b}} .status.err{{display:block;background:#ffebee;border-left:4px solid #b94a48}} .custom-justification{{display:none}}
.identity{{display:grid;grid-template-columns:minmax(160px,1fr) minmax(220px,2fr);gap:12px;max-width:720px}}
@media(max-width:650px){{.identity{{grid-template-columns:1fr}}}}
@media print{{body{{background:#fff}}h2{{color:#173b5e;background:#fff;border-bottom:2px solid #3f7cac;padding-left:0}}.criterion{{box-shadow:none}}button{{display:none}}}}
</style>
</head>
<body>
<h1>{escape(title)}</h1>
<div class="meta">
<strong>Dataset:</strong> {escape(str(algorithm.get('dataset', '')))} ·
<strong>Source:</strong> {escape(str(algorithm.get('source_file', '')))} ·
<strong>Pipeline:</strong> {escape(str(template.get('pipeline_version')))} ·
<strong>Rubric:</strong> {escape(str(template.get('rubric_version')))}
</div>
{ownership_html}
<div id="save_status" class="status"></div>
<p>{escape(str(template.get('instructions') or ''))}</p>
<h2>Reviewer</h2>
<div class="identity">
<label>Reviewer ID <input id="reviewer_id" type="text"></label>
<label>Reviewer Name <input id="reviewer_name" type="text"></label>
</div>
<label>Overall Reviewer Confidence
<select id="reviewer_confidence"><option value="">Select…</option><option>HIGH</option><option>MODERATE</option><option>LOW</option></select></label>
<h2>Source Sufficiency</h2>
<section class="criterion">
<p class="question">{escape(str((template.get('source_sufficiency') or {}).get('question')))}</p>
<p><strong>Automated result:</strong> {escape(str((template.get('source_sufficiency') or {}).get('automated_result')))}</p>
<p><strong>Automated justification:</strong> {escape(str((template.get('source_sufficiency') or {}).get('automated_justification')))}</p>
<label>Human Result <select id="g1_result"><option value="">Select…</option><option>EVALUABLE</option><option>EXPECTED_FAILURE</option><option>REVIEW_REQUIRED</option></select></label>
<label>Agreement <select id="g1_agreement"><option value="">Select…</option><option>AGREE</option><option>PARTIALLY_AGREE</option><option>DISAGREE</option></select></label>
{g1_comment_html}
</section>
<h2>Behavioural Evidence Adequacy</h2>
<section class="criterion">
<p class="question">{escape(str((template.get('behavioural_evidence_adequacy') or {}).get('question')))}</p>
<p><strong>Headline classification:</strong> {escape(str((template.get('behavioural_evidence_adequacy') or {}).get('automated_result')))}</p>
<p><strong>Evidence summary:</strong> {escape(str((template.get('behavioural_evidence_adequacy') or {}).get('summary')))}</p>
<details open><summary>Coverage profile</summary><pre>{escape(json.dumps((template.get('behavioural_evidence_adequacy') or {}).get('coverage_dimensions') or {}, indent=2))}</pre></details>
<details><summary>Strengths</summary><pre>{escape(json.dumps((template.get('behavioural_evidence_adequacy') or {}).get('strengths') or [], indent=2))}</pre></details>
<details><summary>Limitations</summary><pre>{escape(json.dumps((template.get('behavioural_evidence_adequacy') or {}).get('limitations') or [], indent=2))}</pre></details>
<p><strong>Coverage basis:</strong> {escape(str((template.get('behavioural_evidence_adequacy') or {}).get('coverage_basis')))}</p>
<p><strong>Interpretation:</strong> {escape(str((template.get('behavioural_evidence_adequacy') or {}).get('interpretation')))}</p>
<label>Human G2 Assessment <select id="g2_result"><option value="">Select…</option><option>ADEQUATE</option><option>PARTIAL</option><option>LIMITED</option><option>NOT_EVALUABLE</option><option>NOT_DECLARED</option></select></label>
<label>Agreement <select id="g2_agreement"><option value="">Select…</option><option>AGREE</option><option>PARTIALLY_AGREE</option><option>DISAGREE</option></select></label>
{g2_comment_html}
</section>
{semantic_html}
{benchmark_html}
<h2>Stage Criteria</h2>
{cards}
<h2>Overall Review</h2>
<label>Material Semantic Error Not Captured by the Automated Criteria?
<select id="uncaptured"><option value="">Select…</option><option value="false">No</option><option value="true">Yes</option></select></label>
<label>First Semantic Loss Stage
<select id="first_loss"><option value="">Select…</option><option>SOURCE</option><option>CANONICALISATION</option><option>AST</option><option>FLOW_DIAGRAM</option><option>PYTHON</option><option>BEHAVIOURAL_TESTING</option><option>NONE</option><option>UNABLE_TO_DETERMINE</option></select></label>
<label>Is the Final Generated Python Behaviourally Faithful to the Algorithm Supplied by the Model?
<select id="faithful"><option value="">Select…</option><option>YES</option><option>PARTIALLY</option><option>NO</option><option>NA</option></select></label>
<label>Additional Observations <textarea id="observations" rows="5"></textarea></label>
<button id="primary" type="button">{primary_button}</button>
<button id="print" type="button">Print / save as PDF</button>
<p class="notice">{escape(portable_notice)}</p>
<script id="template" type="application/json">{template_json}</script>
<script>
const template=JSON.parse(document.getElementById('template').textContent);
const saveEndpoint={endpoint_json};
const readOnly={read_only_json};
const justificationPresets={json.dumps(JUSTIFICATION_PRESETS, ensure_ascii=False)};
const reviewCommentPresets={json.dumps(REVIEW_COMMENT_PRESETS, ensure_ascii=False)};
const val=id=>{{const el=document.getElementById(id);return el?(el.value||null):null;}};
const boolVal=id=>{{const v=val(id);return v===null?null:v==='true';}};
const radio=name=>{{const el=document.querySelector(`input[name="${{name}}"]:checked`);return el?el.value:null;}};
const setVal=(id,value)=>{{const el=document.getElementById(id);if(el)el.value=value??'';}};
const setText=(id,value)=>{{const el=document.getElementById(id);if(el)el.value=value??'';}};
const toggleCriterionJustification=i=>{{const choice=document.getElementById(`criterion_${{i}}_justification_choice`);const wrap=document.getElementById(`criterion_${{i}}_justification_other_wrap`);if(wrap)wrap.style.display=(choice&&choice.value==='__OTHER__')?'block':'none';}};
const setCriterionJustification=(i,value)=>{{const choice=document.getElementById(`criterion_${{i}}_justification_choice`);const other=document.getElementById(`criterion_${{i}}_justification_other`);const text=value||'';if(!choice)return;if(text&&justificationPresets.includes(text)){{choice.value=text;if(other)other.value='';}}else if(text){{choice.value='__OTHER__';if(other)other.value=text;}}else{{choice.value=justificationPresets[0];if(other)other.value='';}}toggleCriterionJustification(i);}};
const criterionJustification=i=>{{const choice=document.getElementById(`criterion_${{i}}_justification_choice`);if(!choice)return'';if(choice.value==='__OTHER__'){{const other=document.getElementById(`criterion_${{i}}_justification_other`);return other?other.value.trim():'';}}return choice.value||justificationPresets[0];}};
const toggleReviewComment=base=>{{const choice=document.getElementById(`${{base}}_choice`);const wrap=document.getElementById(`${{base}}_other_wrap`);if(wrap)wrap.style.display=(choice&&choice.value==='__OTHER__')?'block':'none';}};
const setReviewComment=(base,value)=>{{const choice=document.getElementById(`${{base}}_choice`);const other=document.getElementById(`${{base}}_other`);const text=value||'';if(!choice)return;if(text&&reviewCommentPresets.includes(text)){{choice.value=text;if(other)other.value='';}}else if(text){{choice.value='__OTHER__';if(other)other.value=text;}}else{{choice.value=reviewCommentPresets[0];if(other)other.value='';}}toggleReviewComment(base);}};
const reviewCommentValue=base=>{{const choice=document.getElementById(`${{base}}_choice`);if(!choice)return'';if(choice.value==='__OTHER__'){{const other=document.getElementById(`${{base}}_other`);return other?other.value.trim():'';}}return choice.value||reviewCommentPresets[0];}};
function populate(){{
 const r=template.reviewer||{{}}; setVal('reviewer_id',r.reviewer_id);setVal('reviewer_name',r.reviewer_name);setVal('reviewer_confidence',r.overall_reviewer_confidence);
 const g1=template.source_sufficiency||{{}};setVal('g1_result',g1.human_result);setVal('g1_agreement',g1.agreement_with_automated_result);setReviewComment('g1_justification',g1.reviewer_justification);
 const g2=template.behavioural_evidence_adequacy||{{}};setVal('g2_result',g2.human_result);setVal('g2_agreement',g2.agreement_with_automated_result);setReviewComment('g2_justification',g2.reviewer_justification);
 if(template.task_semantic_evaluation){{const h=template.task_semantic_evaluation.human_assessment||{{}};setVal('sem_inputs',h.required_inputs_represented);setVal('sem_logic',h.core_algorithm_logic);setVal('sem_output',h.required_output_semantics_represented);setVal('sem_edge',h.edge_and_domain_handling);setVal('sem_overall',h.overall_semantic_assessment);setReviewComment('sem_justification',h.reviewer_justification);}}
 if(template.benchmark_validation){{setVal('baseline_reference_appropriate',template.benchmark_validation.human_reference_appropriate);setText('baseline_reference_justification',template.benchmark_validation.reviewer_justification);}}
 (template.criteria||[]).forEach((item,i)=>{{const h=item.human_assessment||{{}};let label=h.score_label;if(!label&&h.score!==null&&h.score!==undefined)label=String(h.score);if(label){{const el=document.querySelector(`input[name="criterion_${{i}}_score"][value="${{label}}"]`);if(el)el.checked=true;}}setVal(`criterion_${{i}}_agreement`,h.agreement_with_automated_score);setVal(`criterion_${{i}}_semantic`,h.semantic_issue===true?'true':(h.semantic_issue===false?'false':''));setCriterionJustification(i,h.reviewer_justification);}});
 const o=template.overall_review||{{}};setVal('uncaptured',o.material_semantic_error_not_captured===true?'true':(o.material_semantic_error_not_captured===false?'false':''));setVal('first_loss',o.first_semantic_loss_stage);setVal('faithful',o.final_python_behaviourally_faithful);setText('observations',o.additional_observations);
 if(saveEndpoint){{document.getElementById('reviewer_id').readOnly=true;document.getElementById('reviewer_name').readOnly=true;}}
 if(readOnly){{document.querySelectorAll('input,select,textarea').forEach(el=>el.disabled=true);document.getElementById('primary').disabled=true;}}
}}
function buildReview(){{
 const out=JSON.parse(JSON.stringify(template));out.reviewer=out.reviewer||{{}};
 out.reviewer.reviewer_id=val('reviewer_id')||'';out.reviewer.reviewer_name=val('reviewer_name')||'';out.reviewer.reviewed_at_utc=new Date().toISOString();out.reviewer.overall_reviewer_confidence=val('reviewer_confidence');
 out.source_sufficiency.human_result=val('g1_result');out.source_sufficiency.agreement_with_automated_result=val('g1_agreement');out.source_sufficiency.reviewer_justification=reviewCommentValue('g1_justification');
 out.behavioural_evidence_adequacy.human_result=val('g2_result');out.behavioural_evidence_adequacy.agreement_with_automated_result=val('g2_agreement');out.behavioural_evidence_adequacy.reviewer_justification=reviewCommentValue('g2_justification');
 if(out.benchmark_validation){{out.benchmark_validation.human_reference_appropriate=val('baseline_reference_appropriate');out.benchmark_validation.reviewer_justification=document.getElementById('baseline_reference_justification').value;}}
 if(out.task_semantic_evaluation){{const h=out.task_semantic_evaluation.human_assessment;h.required_inputs_represented=val('sem_inputs');h.core_algorithm_logic=val('sem_logic');h.required_output_semantics_represented=val('sem_output');h.edge_and_domain_handling=val('sem_edge');h.overall_semantic_assessment=val('sem_overall');h.reviewer_justification=reviewCommentValue('sem_justification');}}
 out.criteria.forEach((item,i)=>{{const raw=radio(`criterion_${{i}}_score`);item.human_assessment.score=raw===null?null:(raw==='NA'?null:Number(raw));item.human_assessment.score_label=raw;item.human_assessment.completed=['0','1','2','NA'].includes(raw);item.human_assessment.agreement_with_automated_score=val(`criterion_${{i}}_agreement`);item.human_assessment.semantic_issue=boolVal(`criterion_${{i}}_semantic`);item.human_assessment.reviewer_justification=criterionJustification(i);}});
 out.overall_review.material_semantic_error_not_captured=boolVal('uncaptured');out.overall_review.first_semantic_loss_stage=val('first_loss');out.overall_review.final_python_behaviourally_faithful=val('faithful');out.overall_review.additional_observations=document.getElementById('observations').value;return out;
}}
function showStatus(ok,message){{const box=document.getElementById('save_status');box.className='status '+(ok?'ok':'err');box.textContent=message;box.scrollIntoView({{behavior:'smooth',block:'center'}});}}
function downloadReviewBackup(review){{const blob=new Blob([JSON.stringify(review,null,2)],{{type:'application/json'}});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='human_review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),500);}}
document.getElementById('primary').addEventListener('click',async()=>{{
 if(readOnly)return;const review=buildReview();if(!review.reviewer.reviewer_id||!review.reviewer.reviewer_name){{showStatus(false,'Reviewer ID and Reviewer Name are required.');return;}}
 if(saveEndpoint){{try{{const response=await fetch(saveEndpoint,{{method:'POST',headers:{{'Content-Type':'application/json'}},cache:'no-store',body:JSON.stringify(review)}});let result={{}};try{{result=await response.json();}}catch(_err){{result={{}};}}if(!response.ok){{showStatus(false,result.error||('Review could not be saved (HTTP '+response.status+').'));return;}}showStatus(true,result.message||'Review saved.');}}catch(_err){{downloadReviewBackup(review);showStatus(false,{fetch_fallback_message_json});}}return;}}
 downloadReviewBackup(review);
}});
document.getElementById('print').addEventListener('click',()=>window.print());
populate();
</script>
</body>
</html>'''


class HumanReviewQuestionnaireGenerator:
    def write(self, scoring_directory: Path, score_document: dict[str, Any]) -> dict[str, Path]:
        scoring_directory = Path(scoring_directory)
        scoring_directory.mkdir(parents=True, exist_ok=True)
        template = _review_template(score_document)
        json_path = scoring_directory / "human_review_questionnaire.json"
        html_path = scoring_directory / "human_review_questionnaire.html"
        json_path.write_text(json.dumps(template, indent=2), encoding="utf-8")
        html_path.write_text(_html_document(template), encoding="utf-8")
        return {"questionnaire_json": json_path, "questionnaire_html": html_path}
