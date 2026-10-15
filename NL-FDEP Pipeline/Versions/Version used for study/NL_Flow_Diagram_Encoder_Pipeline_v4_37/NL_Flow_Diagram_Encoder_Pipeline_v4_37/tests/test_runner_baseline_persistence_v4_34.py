import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pycharm_runner import (
    RUNNER_STATE_PURPOSE,
    RUNNER_STATE_SCHEMA_VERSION,
    _clear_baseline_preference,
    _runner_state_path,
    _save_baseline_preference,
    _saved_baseline_root,
)


class RunnerBaselineStateCompatibilityTests(unittest.TestCase):
    """Retain low-level v4.34 state I/O coverage after RC5 changes its semantics."""

    def test_state_file_round_trips_baseline_path_as_recovery_hint(self):
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / "user-state" / "runner_state.json"
            baseline = Path(temp) / "Baselines"
            baseline.mkdir()
            with patch.dict(os.environ, {"NL_FDEP_RUNNER_STATE_FILE": str(state_path)}, clear=False):
                _save_baseline_preference(baseline)
                self.assertEqual(state_path, _runner_state_path())
                self.assertEqual(baseline.resolve(), _saved_baseline_root().resolve())
                payload = json.loads(state_path.read_text(encoding="utf-8"))
                self.assertEqual(RUNNER_STATE_SCHEMA_VERSION, payload["schema_version"])
                self.assertEqual(RUNNER_STATE_PURPOSE, payload["state_purpose"])
                self.assertEqual(str(baseline.resolve()), payload["last_baseline_root"])
                self.assertEqual("4.37", payload["last_selected_pipeline_version"])
                _clear_baseline_preference()
                self.assertFalse(state_path.exists())

    def test_legacy_state_without_rc5_purpose_remains_a_detection_hint(self):
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / "runner_state.json"
            baseline = Path(temp) / "Baselines"
            baseline.mkdir()
            state_path.write_text(
                json.dumps({
                    "schema_version": "1.0",
                    "last_baseline_root": str(baseline),
                    "last_selected_pipeline_version": "4.37",
                }),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"NL_FDEP_RUNNER_STATE_FILE": str(state_path)}, clear=False):
                self.assertEqual(baseline.resolve(), _saved_baseline_root().resolve())


if __name__ == "__main__":
    unittest.main()
