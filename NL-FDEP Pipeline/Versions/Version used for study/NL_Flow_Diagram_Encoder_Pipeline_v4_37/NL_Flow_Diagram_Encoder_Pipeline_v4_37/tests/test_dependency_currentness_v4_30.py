import json
from pathlib import Path

import study_provenance as provenance
from study_provenance import declared_dependency_environment, manifest_is_current, sha256_file, sha256_json


def _base_manifest(source: Path, ref: Path, tests: Path, dependency_hash: str) -> dict:
    return {
        "pipeline_version": "4.30",
        "rubric_version": "1.1",
        "rubric_sha256": "rubric",
        "pseudocode_profile": "AJ_DIALECT_STRICT",
        "source_pseudocode_sha256": sha256_file(source),
        "reference_python_sha256": sha256_file(ref),
        "tests_sha256": sha256_file(tests),
        "dependency_environment_sha256": dependency_hash,
    }


def test_declared_dependency_availability_change_invalidates_current_manifest(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    ref = tmp_path / "ref.py"
    tests = tmp_path / "tests.json"
    manifest = tmp_path / "manifest.json"
    source.write_text('OUTPUT STRING("ok")\n', encoding="utf-8")
    ref.write_text('print("ok")\n', encoding="utf-8")
    tests.write_text(json.dumps({"tests": [{"requires_modules": ["demo_optional_module"]}]}), encoding="utf-8")

    monkeypatch.setattr(provenance.importlib.util, "find_spec", lambda name: None)
    unavailable = declared_dependency_environment(tests)
    assert unavailable["modules"]["demo_optional_module"]["available"] is False
    manifest.write_text(json.dumps(_base_manifest(source, ref, tests, sha256_json(unavailable))), encoding="utf-8")

    assert manifest_is_current(
        manifest,
        source_file=source,
        pipeline_version="4.30",
        rubric_version="1.1",
        rubric_sha256="rubric",
        reference_python=ref,
        tests_file=tests,
        pseudocode_profile="AJ_DIALECT_STRICT",
    )

    monkeypatch.setattr(provenance.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(provenance.importlib.metadata, "version", lambda name: "1.0.0")
    available = declared_dependency_environment(tests)
    assert available["modules"]["demo_optional_module"] == {
        "available": True,
        "distribution_version": "1.0.0",
    }

    assert not manifest_is_current(
        manifest,
        source_file=source,
        pipeline_version="4.30",
        rubric_version="1.1",
        rubric_sha256="rubric",
        reference_python=ref,
        tests_file=tests,
        pseudocode_profile="AJ_DIALECT_STRICT",
    )


def test_declared_dependency_version_change_invalidates_current_manifest(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    ref = tmp_path / "ref.py"
    tests = tmp_path / "tests.json"
    manifest = tmp_path / "manifest.json"
    source.write_text('OUTPUT STRING("ok")\n', encoding="utf-8")
    ref.write_text('print("ok")\n', encoding="utf-8")
    tests.write_text(json.dumps({"tests": [{"requires_modules": ["demo_optional_module"]}]}), encoding="utf-8")

    monkeypatch.setattr(provenance.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(provenance.importlib.metadata, "version", lambda name: "1.0.0")
    environment = declared_dependency_environment(tests)
    manifest.write_text(json.dumps(_base_manifest(source, ref, tests, sha256_json(environment))), encoding="utf-8")

    monkeypatch.setattr(provenance.importlib.metadata, "version", lambda name: "2.0.0")
    assert not manifest_is_current(
        manifest,
        source_file=source,
        pipeline_version="4.30",
        rubric_version="1.1",
        rubric_sha256="rubric",
        reference_python=ref,
        tests_file=tests,
        pseudocode_profile="AJ_DIALECT_STRICT",
    )


def test_legacy_manifest_without_dependency_hash_remains_current_when_suite_declares_none(tmp_path):
    source = tmp_path / "source.txt"
    ref = tmp_path / "ref.py"
    tests = tmp_path / "tests.json"
    manifest = tmp_path / "manifest.json"
    source.write_text('OUTPUT STRING("ok")\n', encoding="utf-8")
    ref.write_text('print("ok")\n', encoding="utf-8")
    tests.write_text(json.dumps({"tests": [{}]}), encoding="utf-8")
    payload = _base_manifest(source, ref, tests, "unused")
    payload.pop("dependency_environment_sha256")
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    assert manifest_is_current(
        manifest,
        source_file=source,
        pipeline_version="4.30",
        rubric_version="1.1",
        rubric_sha256="rubric",
        reference_python=ref,
        tests_file=tests,
        pseudocode_profile="AJ_DIALECT_STRICT",
    )
