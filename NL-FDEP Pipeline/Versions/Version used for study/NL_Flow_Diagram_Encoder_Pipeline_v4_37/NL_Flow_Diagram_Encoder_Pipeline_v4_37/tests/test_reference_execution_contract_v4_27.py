import tempfile
from pathlib import Path

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from aj_test_harness import AJTestHarness, TestCase as HarnessCase
from baseline_benchmark import _run_reference, test_cases_from_spec as build_test_cases, validate_reference_python
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def test_trusted_txt_reference_can_comment_exact_packaged_algorithm_title_without_mutating_source():
    with tempfile.TemporaryDirectory() as td:
        ref = Path(td) / "Algorithm 1 Baseline Python code.txt"
        original = "Determine if 2 strings are anagrams of each other\n\nprint('expected')\nquit()\n"
        ref.write_text(original, encoding="utf-8")
        title = "Determine if 2 strings are anagrams of each other"
        validation = validate_reference_python(ref, [{"name": "normal", "category": "NORMAL"}], title)
        assert validation["status"] == "TRUSTED_REFERENCE"
        prep = validation["reference_source_preparation"]
        assert prep["raw_syntax_valid"] is False
        assert prep["execution_syntax_valid"] is True
        assert prep["normalisation_applied"] is True
        assert prep["normalisation_rule"] == "COMMENT_MATCHED_TEST_SUITE_ALGORITHM_TITLE"
        assert ref.read_text(encoding="utf-8") == original

        run = _run_reference(ref, {"name": "normal", "category": "NORMAL"}, title)
        assert run["status"] == "COMPLETED"
        assert run["return_code"] == 0
        assert run["error_type"] is None
        assert run["stdout"] == ["expected"]


def test_unmatched_invalid_reference_heading_is_not_silently_normalised():
    with tempfile.TemporaryDirectory() as td:
        ref = Path(td) / "ref.txt"
        ref.write_text("Different prose heading\n\nprint('x')\n", encoding="utf-8")
        validation = validate_reference_python(ref, [], "Expected algorithm title")
        assert validation["status"] == "NOT_EVALUATED"
        assert validation["reference_source_preparation"]["execution_syntax_valid"] is False


def test_non_error_reference_runtime_fault_is_not_adopted_as_expected_behaviour():
    with tempfile.TemporaryDirectory() as td:
        ref = Path(td) / "ref.py"
        ref.write_text("raise NameError('broken reference')\n", encoding="utf-8")
        specs = [{"name": "normal", "category": "NORMAL"}]
        cases, oracle = build_test_cases(specs, reference_python=ref)
        assert cases == []
        assert oracle[0]["test_case_status"] == "NOT_EVALUABLE"
        assert "not adopted as expected behaviour" in oracle[0]["reason"]


def test_error_behaviour_reference_exception_can_define_error_oracle():
    with tempfile.TemporaryDirectory() as td:
        ref = Path(td) / "ref.py"
        ref.write_text("raise ValueError('expected invalid input')\n", encoding="utf-8")
        specs = [{"name": "error", "category": "ERROR_BEHAVIOUR"}]
        cases, oracle = build_test_cases(specs, reference_python=ref)
        assert len(cases) == 1
        assert cases[0].expected_return_code == 1
        assert cases[0].expected_error_type == "ValueError"
        assert oracle[0]["test_case_status"] == "EVALUABLE"


def test_strict_uppercase_intrinsics_and_quit_compile_to_isolated_python():
    source = '''string <- STRING("1a23")
string1 <- EMPTY STRING
FOR EACH char IN string DO
    string1 <- string1 + CALL LOWERCASE(char)
ENDFOR
list1 <- CALL CHARACTERS_OF(string1)
OUTPUT list1
QUIT
'''
    processed = PseudocodeProfileProcessor().process(source, PseudocodeProfile.AJ_DIALECT_STRICT)
    parsed = AJParserFacade().parse(processed.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    assert "LOWERCASE(" not in compiled.source_code
    assert "CHARACTERS_OF(" not in compiled.source_code
    assert ".lower()" in compiled.source_code
    assert "list(string1)" in compiled.source_code
    assert "raise SystemExit" in compiled.source_code

    with tempfile.TemporaryDirectory() as td:
        program = Path(td) / "generated.py"
        program.write_text(compiled.source_code, encoding="utf-8")
        report = AJTestHarness().run(
            program,
            [HarnessCase(name="isolated", expected_output=["['1', 'a', '2', '3']"], expected_return_code=0)],
        )
        assert report.success


def test_truncated_packaged_title_prefix_can_identify_long_reference_heading_conservatively():
    with tempfile.TemporaryDirectory() as td:
        ref = Path(td) / "ref.txt"
        title = (
            "Create a deliberately long packaged algorithm title that was truncated "
            "during the historical common-test metadata export"
        )
        heading = title + " but the frozen reference retained the full descriptive heading"
        original = heading + "\n\nprint('expected')\n"
        ref.write_text(original, encoding="utf-8")
        validation = validate_reference_python(ref, [{"name": "normal", "category": "NORMAL"}], title)
        assert validation["status"] == "TRUSTED_REFERENCE"
        prep = validation["reference_source_preparation"]
        assert prep["normalisation_applied"] is True
        assert prep["normalisation_rule"] == "COMMENT_PREFIX_MATCHED_TRUNCATED_TEST_SUITE_ALGORITHM_TITLE"
        assert prep["declared_algorithm_title"] == title
        assert prep["reference_heading"] == heading
        assert ref.read_text(encoding="utf-8") == original


def test_short_title_prefix_does_not_authorise_reference_heading_normalisation():
    with tempfile.TemporaryDirectory() as td:
        ref = Path(td) / "ref.txt"
        ref.write_text("Sort data but with unrelated extra prose\n\nprint('x')\n", encoding="utf-8")
        validation = validate_reference_python(
            ref,
            [{"name": "normal", "category": "NORMAL"}],
            "Sort data",
        )
        assert validation["status"] == "NOT_EVALUATED"
        prep = validation["reference_source_preparation"]
        assert prep["normalisation_applied"] is False
        assert prep["execution_syntax_valid"] is False


def test_raise_systemexit_compiles_as_control_flow_not_wrapped_exception():
    source = "RAISE SystemExit\n"
    processed = PseudocodeProfileProcessor().process(source, PseudocodeProfile.AJ_DIALECT_STRICT)
    parsed = AJParserFacade().parse(processed.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    assert "raise SystemExit" in compiled.source_code
    assert "raise Exception(SystemExit)" not in compiled.source_code

    with tempfile.TemporaryDirectory() as td:
        program = Path(td) / "generated.py"
        program.write_text(compiled.source_code, encoding="utf-8")
        report = AJTestHarness().run(
            program,
            [HarnessCase(name="system-exit", expected_output=[], expected_return_code=0)],
        )
        assert report.success
