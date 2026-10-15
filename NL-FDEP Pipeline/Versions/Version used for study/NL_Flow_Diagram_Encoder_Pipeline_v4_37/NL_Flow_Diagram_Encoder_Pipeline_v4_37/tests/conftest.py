"""Test bootstrap for the grouped v4.30 project layout."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPONENT_DIRECTORIES = [
    PROJECT_ROOT / "parser components",
    PROJECT_ROOT / "compiler components",
    PROJECT_ROOT / "flow diagram components",
    PROJECT_ROOT / "pipeline components",
    PROJECT_ROOT / "study components",
    PROJECT_ROOT / "cli components",
]

for component_directory in reversed(COMPONENT_DIRECTORIES):
    component_path = str(component_directory)
    if component_path not in sys.path:
        sys.path.insert(0, component_path)
