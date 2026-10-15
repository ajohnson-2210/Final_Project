import json
import tempfile
import unittest
from pathlib import Path

from baseline_benchmark import validate_reference_python
from pseudocode_profiles import PseudocodeProfile
from study_batch import StudyBatchProcessor
from study_provenance import validate_baseline, validate_llm_results
from study_review import ReviewSession

SAMPLE = '''total <- INTEGER(0)\nFOR i <- IN RANGE INTEGER(1) TO INTEGER(4) DO\ntotal <- total + i\nENDFOR\nOUTPUT total\n'''

class StudyInfrastructureV408Tests(unittest.TestCase):
    def test_preflight_reports_hashes_and_missing_expected_algorithms(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'source_a'/'results'; folder=root/'Algorithm - 1'; folder.mkdir(parents=True)
            source=folder/'Algorithm 1 Pseudocode.txt'; source.write_text(SAMPLE,encoding='utf-8')
            report=validate_llm_results(root)
            row=next(r for r in report['algorithms'] if r['algorithm_id']==1)
            self.assertEqual('READY',row['status']); self.assertEqual(64,len(row['source_sha256']))
            self.assertEqual(49,report['issue_count'])

    def test_reference_validation_uses_only_explicit_researcher_expectations(self):
        with tempfile.TemporaryDirectory() as directory:
            ref=Path(directory)/'Algorithm 1 Python.py'; ref.write_text("print('6')\n",encoding='utf-8')
            specs=[{'name':'explicit','standard_input':[],'expected_output':['6']},{'name':'derived','standard_input':[]}]
            result=validate_reference_python(ref,specs)
            self.assertEqual('VALIDATED',result['status']); self.assertEqual(1,result['explicit_tests_total']); self.assertEqual(100.0,result['validation_percentage'])

    def test_baseline_run_writes_reference_validation_flow_mediation_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline=Path(directory)/'Baseline'; pseudo=baseline/'pseudocode'/'Algorithm - 1'; py=baseline/'python'/'Algorithm - 1'; pseudo.mkdir(parents=True); py.mkdir(parents=True)
            (pseudo/'Algorithm 1 Pseudocode.txt').write_text(SAMPLE,encoding='utf-8')
            (py/'Algorithm 1 Python.py').write_text("total=0\nfor i in range(1,4): total += i\nprint(total)\n",encoding='utf-8')
            (py/'Algorithm 1 Tests.json').write_text(json.dumps({'tests':[{'name':'verified','standard_input':[],'expected_output':['6']}]}),encoding='utf-8')
            result=StudyBatchProcessor(common_tests_root=Path(directory)/"no_common_tests").process_baseline(baseline,profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            art=pseudo/'pipeline_artifacts'
            self.assertEqual('VALIDATED',json.loads((art/'baseline_reference_validation.json').read_text())['status'])
            fm=json.loads((art/'flow_mediation_analysis.json').read_text())
            self.assertTrue(fm['structured_program_match']); self.assertEqual(0.0,fm['flow_mediation_delta'])
            manifest=json.loads((art/'manifest.json').read_text()); self.assertEqual('4.37',manifest['pipeline_version']); self.assertEqual(64,len(manifest['source_pseudocode_sha256'])); self.assertTrue(manifest['run_id'].startswith('run-'))
            score=json.loads((art/'scoring'/'automated_score.json').read_text())
            self.assertEqual(0.0,score['derived_metrics']['flow_mediation_delta'])
            self.assertEqual('VALIDATED',score['benchmark']['reference_validation']['status'])
            self.assertIn('benchmark_validation',json.loads((art/'scoring'/'human_review_questionnaire.json').read_text()))

    def test_resume_skips_current_and_review_protects_changed_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'source_a'/'results'; folder=root/'Algorithm - 1'; folder.mkdir(parents=True); source=folder/'Algorithm 1 Pseudocode.txt'; source.write_text(SAMPLE,encoding='utf-8')
            p=StudyBatchProcessor(); p.process_llm_results(root,profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            drawio=folder/'pipeline_artifacts'/'flow_diagram.drawio'
            drawio.write_text('STALE DRAWIO',encoding='utf-8')
            second=p.process_llm_results(root,profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            self.assertEqual('SKIPPED_CURRENT',second['report']['algorithms'][0]['action'])
            self.assertNotEqual('STALE DRAWIO',drawio.read_text(encoding='utf-8'))
            self.assertIn('<mxfile',drawio.read_text(encoding='utf-8'))
            scoring=folder/'pipeline_artifacts'/'scoring'; q=json.loads((scoring/'human_review_questionnaire.json').read_text()); q['reviewer']['reviewer_id']='R1'; (scoring/'human_review.json').write_text(json.dumps(q),encoding='utf-8')
            source.write_text(SAMPLE+'COMMENT changed\n',encoding='utf-8')
            third=p.process_llm_results(root,profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            self.assertEqual('REVIEW_PROTECTED_INPUT_CHANGED',third['report']['algorithms'][0]['action'])


    def test_baseline_resume_is_read_only_for_current_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline=Path(directory)/'Baseline'; pseudo=baseline/'pseudocode'/'Algorithm - 1'; py=baseline/'python'/'Algorithm - 1'; pseudo.mkdir(parents=True); py.mkdir(parents=True)
            (pseudo/'Algorithm 1 Pseudocode.txt').write_text(SAMPLE,encoding='utf-8')
            (py/'Algorithm 1 Python.py').write_text("total=0\nfor i in range(1,4): total += i\nprint(total)\n",encoding='utf-8')
            (py/'Algorithm 1 Tests.json').write_text(json.dumps({'tests':[{'name':'verified','standard_input':[],'expected_output':['6']}]}),encoding='utf-8')
            processor=StudyBatchProcessor(common_tests_root=Path(directory)/'no_common_tests')
            processor.process_baseline(baseline,profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            art=pseudo/'pipeline_artifacts'
            drawio=art/'flow_diagram.drawio'
            drawio.write_text('BASELINE DRAWIO MUST REMAIN UNTOUCHED',encoding='utf-8')
            before={str(path.relative_to(art)): path.read_bytes() for path in art.rglob('*') if path.is_file()}
            second=processor.process_baseline(baseline,profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            after={str(path.relative_to(art)): path.read_bytes() for path in art.rglob('*') if path.is_file()}
            self.assertEqual('SKIPPED_CURRENT',second['report']['algorithms'][0]['action'])
            self.assertEqual(before,after)
            self.assertEqual('BASELINE DRAWIO MUST REMAIN UNTOUCHED',drawio.read_text(encoding='utf-8'))

    def test_review_session_writes_directly_and_adjudicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'source_a'/'results'; folder=root/'Algorithm - 1'; folder.mkdir(parents=True); (folder/'Algorithm 1 Pseudocode.txt').write_text(SAMPLE,encoding='utf-8')
            StudyBatchProcessor().process_llm_results(root,profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            scoring=folder/'pipeline_artifacts'/'scoring'; session=ReviewSession(scoring); first=session.document['criteria'][0]['criterion_id']
            session.save(reviewer_id='R1',confidence='HIGH',gate_result='EVALUABLE',gate_agreement='AGREE',gate_justification='',criteria={first:{'score':2,'score_label':'2','agreement_with_automated_score':'AGREE','semantic_issue':False,'reviewer_justification':'Confirmed.'}},overall={'material_semantic_error_not_captured':False,'first_semantic_loss_stage':'NONE','final_python_behaviourally_faithful':'YES','additional_observations':''})
            self.assertTrue((scoring/'human_review.json').exists()); final=json.loads((scoring/'final_score.json').read_text()); self.assertEqual('HUMAN_REVIEW_PARTIAL',final['score_status']); self.assertFalse(final['rubric_scores']['combined']['available'])

    def test_v437_baseline_resume_accepts_semantically_unchanged_v436_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline=Path(directory)/'Baseline'; pseudo=baseline/'pseudocode'/'Algorithm - 1'; py=baseline/'python'/'Algorithm - 1'; pseudo.mkdir(parents=True); py.mkdir(parents=True)
            source=pseudo/'Algorithm 1 Pseudocode.txt'; source.write_text(SAMPLE,encoding='utf-8')
            (py/'Algorithm 1 Python.py').write_text("total=0\nfor i in range(1,4): total += i\nprint(total)\n",encoding='utf-8')
            (py/'Algorithm 1 Tests.json').write_text(json.dumps({'tests':[{'name':'verified','standard_input':[],'expected_output':['6']}]}),encoding='utf-8')
            processor=StudyBatchProcessor(common_tests_root=Path(directory)/'no_common_tests')
            processor.process_baseline(baseline,profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            art=pseudo/'pipeline_artifacts'; manifest_path=art/'manifest.json'
            manifest=json.loads(manifest_path.read_text(encoding='utf-8')); manifest['pipeline_version']='4.36'; manifest['rubric_sha256']='72c285d390630dc4e1d341537de06f025b4a49b4eb023f94215f70ee0d6dfb72'; manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
            before={str(path.relative_to(art)): path.read_bytes() for path in art.rglob('*') if path.is_file()}
            second=processor.process_baseline(baseline,profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            after={str(path.relative_to(art)): path.read_bytes() for path in art.rglob('*') if path.is_file()}
            self.assertEqual('SKIPPED_CURRENT',second['report']['algorithms'][0]['action'])
            self.assertEqual(before,after)

    def test_v437_does_not_accept_changed_v436_baseline_as_current(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline=Path(directory)/'Baseline'; pseudo=baseline/'pseudocode'/'Algorithm - 1'; py=baseline/'python'/'Algorithm - 1'; pseudo.mkdir(parents=True); py.mkdir(parents=True)
            source=pseudo/'Algorithm 1 Pseudocode.txt'; source.write_text(SAMPLE,encoding='utf-8')
            (py/'Algorithm 1 Python.py').write_text("total=0\nfor i in range(1,4): total += i\nprint(total)\n",encoding='utf-8')
            (py/'Algorithm 1 Tests.json').write_text(json.dumps({'tests':[{'name':'verified','standard_input':[],'expected_output':['6']}]}),encoding='utf-8')
            processor=StudyBatchProcessor(common_tests_root=Path(directory)/'no_common_tests')
            processor.process_baseline(baseline,profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            art=pseudo/'pipeline_artifacts'; manifest_path=art/'manifest.json'
            manifest=json.loads(manifest_path.read_text(encoding='utf-8')); manifest['pipeline_version']='4.36'; manifest['rubric_sha256']='72c285d390630dc4e1d341537de06f025b4a49b4eb023f94215f70ee0d6dfb72'; manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
            source.write_text(SAMPLE+'COMMENT changed\n',encoding='utf-8')
            status=processor._resume_status(art,source,py/'Algorithm 1 Python.py',py/'Algorithm 1 Tests.json',True,False,PseudocodeProfile.AJ_DIALECT_STRICT,frozenset({'4.36','4.37'}))
            self.assertIsNone(status)

if __name__=='__main__': unittest.main()
