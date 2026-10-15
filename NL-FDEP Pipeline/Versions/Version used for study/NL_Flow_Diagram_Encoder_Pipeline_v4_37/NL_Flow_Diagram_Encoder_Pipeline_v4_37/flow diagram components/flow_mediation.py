"""Paired direct-AST versus flow-mediated Python study analysis.

This tests the machine-readable structured flow mediation used by NL-FDEP. It does
not claim to measure how a human/LLM responds to a rendered flowchart image.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from aj_test_harness import AJTestHarness, TestCase
from flow_diagram import ASTStructureSerializer


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _minimal_flow_document(program: dict[str,Any]) -> dict[str,Any]:
    return {
        'format':'NL-FDEP Flow Diagram','version':'1.0','entry_node':'direct_start','exit_node':'direct_end',
        'nodes':{
            'direct_start':{'node_id':'direct_start','node_type':'START','label':'Start','line':1,'data':{}},
            'direct_end':{'node_id':'direct_end','node_type':'END','label':'End','line':1,'data':{}},
        },
        'edges':[{'source':'direct_start','target':'direct_end','label':'NEXT'}],
        'structured_program':program,
    }


def analyse_flow_mediation(artifact_directory: Path, test_cases: list[TestCase]) -> dict[str,Any]:
    d=Path(artifact_directory); processed=d/'processed_pseudocode.aj'; flow_path=d/'flow_diagram.json'; flow_python=d/'generated_program.py'
    result={'analysis_schema_version':'1.0','status':'NOT_EVALUATED','interpretation':(
        'Paired control comparing direct AST-structured compilation with the pipeline flow-structured compilation. '
        'This measures machine-readable flow mediation, not accuracy from submitting a rendered flowchart to an LLM.'
    )}
    if not processed.is_file() or not flow_path.is_file():
        result['reason']='Processed AJ and flow_diagram.json are required.'; return result
    parsed=AJParserFacade().parse(processed.read_text(encoding='utf-8'))
    if not parsed.success or parsed.ast is None:
        result['reason']='Processed AJ could not be reparsed for the direct control path.'; return result
    direct_program=ASTStructureSerializer().serialize(parsed.ast)
    flow_doc=json.loads(flow_path.read_text(encoding='utf-8')); flow_program=flow_doc.get('structured_program')
    result['structured_program_match']=direct_program==flow_program
    compiler=AJPythonCompiler(); direct_comp=compiler.compile(_minimal_flow_document(direct_program))
    result['direct_compilation']={'success':direct_comp.success,'message':direct_comp.message,'execution_model':direct_comp.execution_model}
    direct_path=d/'direct_ast_program.py'; direct_report_path=d/'direct_ast_compilation_report.json'
    if direct_comp.success:
        direct_path.write_text(direct_comp.source_code,encoding='utf-8')
        result['direct_python']=str(direct_path.resolve()); result['direct_python_sha256']=_sha_text(direct_comp.source_code)
    direct_report_path.write_text(json.dumps(result['direct_compilation'],indent=2),encoding='utf-8')
    if flow_python.is_file():
        fs=flow_python.read_text(encoding='utf-8'); result['flow_python_sha256']=_sha_text(fs)
        result['direct_vs_flow_python_source_match']=bool(direct_comp.success and direct_comp.source_code==fs)
    if direct_comp.success and test_cases:
        tr=AJTestHarness().run(direct_path,test_cases); tp=d/'direct_ast_test_report.json'; tp.write_text(tr.to_json(),encoding='utf-8')
        total=len(tr.results); result['direct_test_accuracy_percentage']=round(tr.passed_tests/total*100,2) if total else None
    else: result['direct_test_accuracy_percentage']=None
    flow_test=None
    p=d/'test_report.json'
    if p.is_file():
        flow_test=json.loads(p.read_text(encoding='utf-8')); total=int(flow_test.get('total_tests',0) or 0); passed=int(flow_test.get('passed_tests',0) or 0)
        result['flow_mediated_test_accuracy_percentage']=round(passed/total*100,2) if total else None
    else: result['flow_mediated_test_accuracy_percentage']=None
    da=result.get('direct_test_accuracy_percentage'); fa=result.get('flow_mediated_test_accuracy_percentage')
    if da is not None and fa is not None:
        delta=round(fa-da,2); result['flow_mediation_delta']=delta
        result['flow_mediation_effect']='IMPROVEMENT' if delta>0 else ('DEGRADATION' if delta<0 else 'NO_CHANGE')
        result['status']='EVALUATED'
    elif direct_comp.success:
        result['status']='STRUCTURAL_ONLY'; result['flow_mediation_delta']=None; result['flow_mediation_effect']='NOT_EVALUABLE'
        result['reason']='No common behavioural tests were available for the paired paths.'
    else:
        result['status']='NOT_EVALUATED'; result['reason']=direct_comp.message
    return result


def write_flow_mediation(artifact_directory: Path, test_cases: list[TestCase]) -> Path:
    p=Path(artifact_directory)/'flow_mediation_analysis.json'; doc=analyse_flow_mediation(artifact_directory,test_cases)
    p.write_text(json.dumps(doc,indent=2),encoding='utf-8'); return p
