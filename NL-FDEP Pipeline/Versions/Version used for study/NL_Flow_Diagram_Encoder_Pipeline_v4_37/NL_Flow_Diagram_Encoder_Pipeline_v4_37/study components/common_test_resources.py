"""Packaged Common Test Design v1.4.2 resource discovery and validation.

v4.29 treats common behavioural tests as pipeline-owned study resources rather
than files that must be physically merged into every selected baseline folder.
The selected baseline remains an external, read-only runtime input.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
import json

TEST_DESIGN_VERSION = "1.4.2"
TEST_SPEC_SCHEMA_VERSION = "1.6"
EXPECTED_ALGORITHM_COUNT = 50
EXPECTED_TEST_COUNT = 156

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMMON_TESTS_ROOT = PROJECT_ROOT / "study data" / "common tests v1.4.2"


@dataclass(frozen=True)
class CommonTestPackStatus:
    root: str
    complete: bool
    suite_count: int
    test_count: int
    missing_algorithm_ids: list[int]
    invalid_algorithm_ids: list[int]
    issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _candidate_paths(root: Path, algorithm_id: int) -> tuple[Path, ...]:
    name = f"Algorithm {algorithm_id} Tests.json"
    return (
        root / name,
        root / f"Algorithm - {algorithm_id}" / name,
        root / "python" / f"Algorithm - {algorithm_id}" / name,
    )


def find_common_test_file(algorithm_id: int, root: Path | None = None) -> Path | None:
    """Return the packaged common test file for an algorithm, if present."""
    resolved_root = Path(root) if root is not None else DEFAULT_COMMON_TESTS_ROOT
    for candidate in _candidate_paths(resolved_root, algorithm_id):
        if candidate.is_file():
            return candidate
    return None


def validate_common_test_pack(
    root: Path | None = None,
    expected_ids: Iterable[int] = range(1, EXPECTED_ALGORITHM_COUNT + 1),
) -> CommonTestPackStatus:
    """Validate identity/schema/count invariants without executing the tests."""
    resolved_root = Path(root) if root is not None else DEFAULT_COMMON_TESTS_ROOT
    missing: list[int] = []
    invalid: list[int] = []
    issues: list[str] = []
    suite_count = 0
    test_count = 0

    for algorithm_id in expected_ids:
        path = find_common_test_file(algorithm_id, resolved_root)
        if path is None:
            missing.append(algorithm_id)
            continue
        suite_count += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:  # invalid resource must fail closed
            invalid.append(algorithm_id)
            issues.append(f"Algorithm {algorithm_id}: invalid JSON ({error}).")
            continue
        if not isinstance(data, dict):
            invalid.append(algorithm_id)
            issues.append(f"Algorithm {algorithm_id}: suite must be a JSON object.")
            continue
        if data.get("algorithm_id") not in {None, algorithm_id}:
            invalid.append(algorithm_id)
            issues.append(
                f"Algorithm {algorithm_id}: declared algorithm_id={data.get('algorithm_id')!r}."
            )
        design = data.get("test_design_version")
        if design not in {None, "1.1", "1.2", "1.3", "1.4", "1.4.1", TEST_DESIGN_VERSION}:
            invalid.append(algorithm_id)
            issues.append(
                f"Algorithm {algorithm_id}: unsupported test design {design!r}; packaged design is {TEST_DESIGN_VERSION}."
            )
        schema = data.get("test_spec_schema_version")
        if schema not in {None, "1.2", "1.3", "1.4", "1.5", TEST_SPEC_SCHEMA_VERSION}:
            invalid.append(algorithm_id)
            issues.append(
                f"Algorithm {algorithm_id}: unsupported test-spec schema {schema!r}; packaged schema is {TEST_SPEC_SCHEMA_VERSION}."
            )
        tests = data.get("tests")
        if not isinstance(tests, list):
            invalid.append(algorithm_id)
            issues.append(f"Algorithm {algorithm_id}: 'tests' must be a list.")
            continue
        test_count += len(tests)

    missing = sorted(set(missing))
    invalid = sorted(set(invalid))
    if suite_count != EXPECTED_ALGORITHM_COUNT:
        issues.append(
            f"Common test pack contains {suite_count} discoverable suites; expected {EXPECTED_ALGORITHM_COUNT}."
        )
    if test_count != EXPECTED_TEST_COUNT:
        issues.append(
            f"Common test pack contains {test_count} tests; expected {EXPECTED_TEST_COUNT}."
        )

    complete = not missing and not invalid and suite_count == EXPECTED_ALGORITHM_COUNT and test_count == EXPECTED_TEST_COUNT
    return CommonTestPackStatus(
        root=str(resolved_root.resolve()),
        complete=complete,
        suite_count=suite_count,
        test_count=test_count,
        missing_algorithm_ids=missing,
        invalid_algorithm_ids=invalid,
        issues=issues,
    )
