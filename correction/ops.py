"""
correction/ops.py - The structured edit vocabulary.

An EditOp is the typed, deterministic description of a single change to a
Measure's event list: set an event's duration, set a note's pitch, delete an
event, or insert an event. It is the contract between the two layers of this
module (see correction/__init__.py): the LLM boundary's only job is to turn a
human utterance into one of these, and the deterministic core's only job is to
apply one of these to a Measure.

Discriminated on `op`, exactly like model/score.py's Event is discriminated on
`kind`, so an op round-trips through JSON unambiguously. Pydantic-pure: no
music21, no I/O.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from model.score import Duration, Event, Pitch

# Events are addressed by their integer index into `measure.events` - the same
# coordinate the rhythm validator hands back as `overflow_event_index`, so the
# correction UI can pass straight through the index it was just shown.


class SetDuration(BaseModel):
    """Replace the duration of the event at `index` (Note or Rest both have one)."""

    op: Literal["set_duration"] = "set_duration"
    index: int
    duration: Duration


class SetPitch(BaseModel):
    """Replace the pitch of the *note* at `index`. Fails loud on a rest."""

    op: Literal["set_pitch"] = "set_pitch"
    index: int
    pitch: Pitch


class DeleteEvent(BaseModel):
    """Remove the event at `index`."""

    op: Literal["delete_event"] = "delete_event"
    index: int


class InsertEvent(BaseModel):
    """Insert `event` *before* `index`. `index == len(events)` appends."""

    op: Literal["insert_event"] = "insert_event"
    index: int
    event: Event


# The union the boundary produces and the core consumes. Discriminated on `op`.
EditOp = Annotated[
    Union[SetDuration, SetPitch, DeleteEvent, InsertEvent],
    Field(discriminator="op"),
]
