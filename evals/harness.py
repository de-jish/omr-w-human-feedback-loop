"""
evals/harness.py - Tiny shared helpers for JSON-case evals.

A case file is a JSON object:

    {
      "name": str,
      "description": str,
      "function": str,          # which public function to call
      "input": {...},           # function-specific, parsed by the module test
      "expected": {...}         # the function's output, model_dump(mode="json")
    }

The harness only loads cases and reports their names; each module's test knows
how to turn its own `input` into typed model objects and how to call the named
function. That keeps the harness generic without pretending one schema fits all
modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_cases(cases_dir: str | Path) -> list[dict[str, Any]]:
    """Load every *.json case in `cases_dir`, sorted by filename for stable test
    ordering. Each case carries its own filename under `_file` for clearer test
    ids and failure messages."""
    cases_dir = Path(cases_dir)
    cases: list[dict[str, Any]] = []
    for path in sorted(cases_dir.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            case = json.load(fh)
        case["_file"] = path.name
        cases.append(case)
    return cases
