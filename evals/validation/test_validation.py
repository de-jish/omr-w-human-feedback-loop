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

from collections import Counter

from model.score import Measure, MeasureContext, Score
from validation import validate_measure, validate_score
from evals.harness import load_cases

CASES_DIR = Path(__file__).parent / "cases"

# Maps the case file's "function" field to the actual callable. Add to this as
# validation/ grows more public functions.
FUNCTIONS: dict[str, Callable[..., Any]] = {
    "validate_measure": validate_measure,
    "validate_score": validate_score,
}


def _inputs_for_validate_measure(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "measure": Measure(**raw["measure"]),
        "context": MeasureContext(**raw["context"]),
    }


def _inputs_for_validate_score(raw: dict[str, Any]) -> dict[str, Any]:
    return {"score": Score(**raw["score"])}


# Each function builds its typed inputs from its own `input` schema.
INPUT_BUILDERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "validate_measure": _inputs_for_validate_measure,
    "validate_score": _inputs_for_validate_score,
}


def _build_inputs(function: str, case_input: dict[str, Any]) -> dict[str, Any]:
    """Turn a case's raw `input` dict into typed model objects for `function`."""
    return INPUT_BUILDERS[function](case_input)


_CASES = load_cases(CASES_DIR)


@pytest.mark.parametrize("case", _CASES, ids=[c["_file"] for c in _CASES])
def test_validation_case(case: dict[str, Any]) -> None:
    fn = FUNCTIONS[case["function"]]
    kwargs = _build_inputs(case["function"], case["input"])

    report = fn(**kwargs)
    actual = report.model_dump(mode="json")

    assert actual == case["expected"], (
        f"{case['_file']} ({case['name']}): output did not match expected.\n"
        f"  actual:   {actual}\n"
        f"  expected: {case['expected']}"
    )


def test_at_least_three_cases_per_function() -> None:
    """CLAUDE.md iron rule: every public function ships >= 3 JSON eval cases."""
    counts = Counter(c["function"] for c in _CASES)
    for function in FUNCTIONS:
        assert counts[function] >= 3, (
            f"{function} has {counts[function]} eval cases, need >= 3"
        )
