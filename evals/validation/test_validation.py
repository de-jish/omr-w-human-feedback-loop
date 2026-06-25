"""
evals/validation/test_validation.py - Run the validation/ JSON eval cases.

For each case under ./cases, build the typed inputs from the model, call the
named public function, and assert its JSON-serialized output matches `expected`
exactly. Deterministic eval, so no tolerance and no LLM judge.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

from model.score import Measure, MeasureContext
from validation import validate_measure
from evals.harness import load_cases

CASES_DIR = Path(__file__).parent / "cases"

# Maps the case file's "function" field to the actual callable. Add to this as
# validation/ grows more public functions.
FUNCTIONS: dict[str, Callable[..., Any]] = {
    "validate_measure": validate_measure,
}


def _build_inputs(case_input: dict[str, Any]) -> dict[str, Any]:
    """Turn a case's raw `input` dict into typed model objects."""
    return {
        "measure": Measure(**case_input["measure"]),
        "context": MeasureContext(**case_input["context"]),
    }


_CASES = load_cases(CASES_DIR)


@pytest.mark.parametrize("case", _CASES, ids=[c["_file"] for c in _CASES])
def test_validation_case(case: dict[str, Any]) -> None:
    fn = FUNCTIONS[case["function"]]
    kwargs = _build_inputs(case["input"])

    report = fn(**kwargs)
    actual = report.model_dump(mode="json")

    assert actual == case["expected"], (
        f"{case['_file']} ({case['name']}): output did not match expected.\n"
        f"  actual:   {actual}\n"
        f"  expected: {case['expected']}"
    )


def test_at_least_three_cases() -> None:
    """CLAUDE.md iron rule: every public function ships >= 3 JSON eval cases."""
    assert len(_CASES) >= 3, f"expected >= 3 validation cases, found {len(_CASES)}"
