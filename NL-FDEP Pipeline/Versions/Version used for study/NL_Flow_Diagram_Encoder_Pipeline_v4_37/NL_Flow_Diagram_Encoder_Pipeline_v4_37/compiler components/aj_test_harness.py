"""Subprocess-based behavioural test harness for generated Python programs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json
import os
import subprocess
import sys
import time


@dataclass
class TestCase:
    """Defines one behavioural test for a generated Python program."""

    name: str
    standard_input: list[str] = field(default_factory=list)
    expected_output: list[str] | None = None
    timeout_seconds: float = 3.0
    category: str = "NORMAL"
    semantic_feature: str | None = None
    expected_return_code: int | None = None
    expected_error_type: str | None = None
    criteria_links: list[str] = field(default_factory=list)
    random_seed: int | None = None
    environment: dict[str, str] = field(default_factory=dict)
    requires_modules: list[str] = field(default_factory=list)


@dataclass
class TestCaseResult:
    """Records the outcome of one executed test case."""

    name: str
    status: str
    expected_output: list[str] | None
    actual_output: list[str]
    standard_error: str
    return_code: int | None
    duration_ms: float
    category: str = "NORMAL"
    semantic_feature: str | None = None
    expected_return_code: int | None = None
    expected_error_type: str | None = None
    actual_error_type: str | None = None
    criteria_links: list[str] = field(default_factory=list)
    random_seed: int | None = None
    environment: dict[str, str] = field(default_factory=dict)
    requires_modules: list[str] = field(default_factory=list)


@dataclass
class TestHarnessReport:
    """Aggregates all behavioural test results."""

    program_path: str
    results: list[TestCaseResult]

    @property
    def passed_tests(self) -> int:
        return sum(result.status == "PASSED" for result in self.results)

    @property
    def failed_tests(self) -> int:
        return len(self.results) - self.passed_tests

    @property
    def success(self) -> bool:
        return bool(self.results) and self.failed_tests == 0

    def to_dict(self) -> dict[str, Any]:
        category_summary: dict[str, dict[str, int]] = {}
        for result in self.results:
            category = str(result.category or "NORMAL").upper()
            row = category_summary.setdefault(category, {"total": 0, "passed": 0, "failed": 0})
            row["total"] += 1
            if result.status == "PASSED":
                row["passed"] += 1
            else:
                row["failed"] += 1
        return {
            "program_path": self.program_path,
            "success": self.success,
            "total_tests": len(self.results),
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "category_summary": category_summary,
            "results": [asdict(result) for result in self.results],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class AJTestHarness:
    """Runs generated Python in isolated subprocesses with time limits."""

    def run(
        self,
        program_path: Path,
        test_cases: list[TestCase],
        working_directory: Path | None = None,
    ) -> TestHarnessReport:
        results: list[TestCaseResult] = []

        for test_case in test_cases:
            results.append(self._run_test_case(program_path, test_case, working_directory))

        return TestHarnessReport(
            program_path=str(program_path.resolve()),
            results=results,
        )

    @staticmethod
    def _error_type(stderr: str) -> str | None:
        """Extract the final Python exception type from stderr, if present."""
        for line in reversed(stderr.splitlines()):
            stripped = line.strip()
            if not stripped:
                continue
            head = stripped.split(":", 1)[0]
            if head.endswith("Error") or head.endswith("Exception"):
                return head
            break
        return None

    @staticmethod
    def _execution_command(program_path: Path, test_case: TestCase) -> list[str]:
        """Build a deterministic command for ordinary or seeded execution.

        The historic harness used ``python -S program.py`` to avoid ambient site
        packages.  That remains the default.  Seeded execution uses a tiny wrapper
        so Python's ``random`` module is initialised before the program starts.  If
        a test explicitly declares external module requirements, normal site-package
        discovery is enabled and NumPy is seeded when available.
        """
        program_path = program_path.resolve()
        if test_case.random_seed is None and not test_case.requires_modules:
            return [sys.executable, "-S", str(program_path)]

        seed = "None" if test_case.random_seed is None else repr(int(test_case.random_seed))
        wrapper = (
            "import random,runpy; "
            f"_seed={seed}; "
            "random.seed(_seed) if _seed is not None else None; "
            "\ntry:\n import numpy as _np\n _np.random.seed(_seed) if _seed is not None else None\nexcept Exception:\n pass\n"
            f"runpy.run_path({str(program_path)!r}, run_name='__main__')"
        )
        command = [sys.executable]
        if not test_case.requires_modules:
            command.append("-S")
        command.extend(["-c", wrapper])
        return command

    @staticmethod
    def _execution_environment(test_case: TestCase) -> dict[str, str]:
        env = dict(os.environ)
        for key, value in (test_case.environment or {}).items():
            env[str(key)] = str(value)
        if test_case.random_seed is not None:
            env.setdefault("PYTHONHASHSEED", str(int(test_case.random_seed)))
        return env

    def _run_test_case(
        self,
        program_path: Path,
        test_case: TestCase,
        working_directory: Path | None = None,
    ) -> TestCaseResult:
        program_path = program_path.resolve()
        input_text = "\n".join(test_case.standard_input)

        if input_text:
            input_text += "\n"

        start_time = time.perf_counter()

        try:
            completed_process = subprocess.run(
                self._execution_command(program_path, test_case),
                input=input_text,
                capture_output=True,
                text=True,
                timeout=test_case.timeout_seconds,
                cwd=(Path(working_directory).resolve() if working_directory is not None else program_path.parent),
                env=self._execution_environment(test_case),
                check=False,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000
            actual_output = completed_process.stdout.splitlines()
            status = "PASSED"

            actual_error_type = self._error_type(completed_process.stderr)

            if (
                test_case.expected_return_code is not None
                and completed_process.returncode != test_case.expected_return_code
            ):
                status = "FAILED"

            if (
                test_case.expected_output is not None
                and actual_output != test_case.expected_output
            ):
                status = "FAILED"

            if (
                test_case.expected_error_type is not None
                and actual_error_type != test_case.expected_error_type
            ):
                status = "FAILED"

            return TestCaseResult(
                name=test_case.name,
                status=status,
                expected_output=test_case.expected_output,
                actual_output=actual_output,
                standard_error=completed_process.stderr,
                return_code=completed_process.returncode,
                duration_ms=round(duration_ms, 3),
                category=test_case.category,
                semantic_feature=test_case.semantic_feature,
                expected_return_code=test_case.expected_return_code,
                expected_error_type=test_case.expected_error_type,
                actual_error_type=actual_error_type,
                criteria_links=list(test_case.criteria_links or []),
                random_seed=test_case.random_seed,
                environment=dict(test_case.environment or {}),
                requires_modules=list(test_case.requires_modules or []),
            )

        except subprocess.TimeoutExpired as error:
            duration_ms = (time.perf_counter() - start_time) * 1000
            standard_output = error.stdout or ""

            if isinstance(standard_output, bytes):
                standard_output = standard_output.decode(errors="replace")

            return TestCaseResult(
                name=test_case.name,
                status="TIMEOUT",
                expected_output=test_case.expected_output,
                actual_output=standard_output.splitlines(),
                standard_error="Execution exceeded the configured timeout.",
                return_code=None,
                duration_ms=round(duration_ms, 3),
                category=test_case.category,
                semantic_feature=test_case.semantic_feature,
                expected_return_code=test_case.expected_return_code,
                expected_error_type=test_case.expected_error_type,
                actual_error_type=None,
                criteria_links=list(test_case.criteria_links or []),
                random_seed=test_case.random_seed,
                environment=dict(test_case.environment or {}),
                requires_modules=list(test_case.requires_modules or []),
            )
