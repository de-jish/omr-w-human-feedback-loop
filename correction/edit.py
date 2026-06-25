"""
correction/edit.py - The deterministic edit core (layer 1).

`apply_edit(measure, op) -> Measure` applies one structured EditOp to a Measure
and returns a NEW Measure; the input is never mutated, so the correction UI can
preview an edit and discard it. No LLM, no music21, pydantic-pure - the whole
point of this layer is that it is a pure, predictable function fully covered by
deterministic evals.

The core does exactly the edit it is given and nothing more. In particular it
does NOT re-check the bar's rhythm: an edit may legitimately leave the measure
overflowing or underflowing, and judging that is validation/'s job, called
afterward. It also never invents provenance - it does not stamp `source`; an op
that inserts an event carries whatever `source` the caller put on that event,
and set_duration/set_pitch preserve the edited event's existing `source`.

When an op cannot be applied (index out of range, set_pitch on a rest) the core
fails loud with EditError rather than guessing - same rule as the rest of the
project: never silently do something other than what was asked.
"""

from __future__ import annotations

from model.score import Measure, Note

from correction.ops import (
    DeleteEvent,
    EditOp,
    InsertEvent,
    SetDuration,
    SetPitch,
)


class EditError(Exception):
    """An EditOp could not be applied to the given Measure (bad index, or a
    pitch edit aimed at a rest). Raised instead of guessing."""


def _check_index(measure: Measure, index: int, *, op: str) -> None:
    """Index must address an existing event: 0 <= index < len(events)."""
    n = len(measure.events)
    if not 0 <= index < n:
        raise EditError(
            f"{op}: index {index} out of range for measure {measure.number} "
            f"with {n} event(s)"
        )


def apply_edit(measure: Measure, op: EditOp) -> Measure:
    """Apply one structured edit and return a new Measure (input untouched)."""
    # Work on a deep copy so the caller's Measure is never mutated.
    edited = measure.model_copy(deep=True)
    events = list(edited.events)

    if isinstance(op, SetDuration):
        _check_index(edited, op.index, op="set_duration")
        events[op.index] = events[op.index].model_copy(update={"duration": op.duration})

    elif isinstance(op, SetPitch):
        _check_index(edited, op.index, op="set_pitch")
        target = events[op.index]
        if not isinstance(target, Note):
            raise EditError(
                f"set_pitch: event {op.index} in measure {edited.number} is a "
                f"rest, which has no pitch"
            )
        events[op.index] = target.model_copy(update={"pitch": op.pitch})

    elif isinstance(op, DeleteEvent):
        _check_index(edited, op.index, op="delete_event")
        del events[op.index]

    elif isinstance(op, InsertEvent):
        # Insert is the one op allowed to address one past the end (append).
        if not 0 <= op.index <= len(events):
            raise EditError(
                f"insert_event: index {op.index} out of range for measure "
                f"{edited.number} with {len(events)} event(s) (0..{len(events)} "
                f"allowed)"
            )
        events.insert(op.index, op.event.model_copy(deep=True))

    else:  # pragma: no cover - exhaustive over the EditOp union.
        raise EditError(f"unknown edit op: {op!r}")

    edited.events = events
    return edited
