"""
evals/correction/test_correction.py - Run the correction/ JSON eval cases.

For each case under ./cases, build the typed inputs (a Measure plus an EditOp
parsed from its discriminated-union dict), call the named public function, and
assert the JSON-serialized result Measure matches `expected` exactly.
Deterministic eval: exact match, no tolerance, no LLM judge.

The deterministic core's happy-path transformations live as JSON cases. Its
fail-loud paths (bad index, set_pitch on a rest) and its no-mutation guarantee
don't fit the "expected output" JSON shape, so they're covered by the plain
pytest tests at the bottom of this file - same pattern as validation's extra
guard test.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Callable

import pytest
from pydantic import TypeAdapter

from model.score import Measure, Note, Pitch, Rest
from model.score import Duration
from correction import EditError, EditOp, SetPitch, apply_edit
from evals.harness import load_cases

CASES_DIR = Path(__file__).parent / "cases"

# Maps the case file's "function" field to the actual callable. Add to this as
# correction/ grows more public functions.
FUNCTIONS: dict[str, Callable[..., Any]] = {
    "apply_edit": apply_edit,
}

# Parses a case's raw `op` dict into the correct EditOp via the `op` discriminator.
_EDIT_OP = TypeAdapter(EditOp)


def _inputs_for_apply_edit(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "measure": Measure(**raw["measure"]),
        "op": _EDIT_OP.validate_python(raw["op"]),
    }


# Each function builds its typed inputs from its own `input` schema.
INPUT_BUILDERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "apply_edit": _inputs_for_apply_edit,
}


def _build_inputs(function: str, case_input: dict[str, Any]) -> dict[str, Any]:
    """Turn a case's raw `input` dict into typed model objects for `function`."""
    return INPUT_BUILDERS[function](case_input)


_CASES = load_cases(CASES_DIR)


@pytest.mark.parametrize("case", _CASES, ids=[c["_file"] for c in _CASES])
def test_correction_case(case: dict[str, Any]) -> None:
    fn = FUNCTIONS[case["function"]]
    kwargs = _build_inputs(case["function"], case["input"])

    result = fn(**kwargs)
    actual = result.model_dump(mode="json")

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


# --------------------------------------------------------------------------- #
# Fail-loud and no-mutation guarantees (don't fit the JSON-output case shape).
# --------------------------------------------------------------------------- #


def _one_note_measure() -> Measure:
    return Measure(
        number=1,
        events=[Note(pitch=Pitch(step="C", octave=3), duration=Duration(type="quarter"))],
    )


def test_apply_edit_does_not_mutate_input() -> None:
    measure = _one_note_measure()
    before = measure.model_dump(mode="json")

    apply_edit(measure, SetPitch(index=0, pitch=Pitch(step="G", octave=2)))

    assert measure.model_dump(mode="json") == before, "input Measure was mutated"


def test_set_pitch_on_rest_fails_loud() -> None:
    measure = Measure(number=1, events=[Rest(duration=Duration(type="quarter"))])
    with pytest.raises(EditError, match="rest"):
        apply_edit(measure, SetPitch(index=0, pitch=Pitch(step="C", octave=3)))


@pytest.mark.parametrize("index", [-1, 1, 99])
def test_out_of_range_index_fails_loud(index: int) -> None:
    measure = _one_note_measure()
    with pytest.raises(EditError, match="out of range"):
        apply_edit(measure, SetPitch(index=index, pitch=Pitch(step="C", octave=3)))
