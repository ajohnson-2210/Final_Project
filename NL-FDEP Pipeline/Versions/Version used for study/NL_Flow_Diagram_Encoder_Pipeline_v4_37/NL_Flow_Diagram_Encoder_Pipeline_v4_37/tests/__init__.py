"""Unittest bootstrap for the grouped v4.30 project layout."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for component_name in (
    "parser components",
    "compiler components",
    "flow diagram components",
    "pipeline components",
    "study components",
    "cli components",
):
    component_path = str(PROJECT_ROOT / component_name)
    if component_path not in sys.path:
        sys.path.insert(0, component_path)
