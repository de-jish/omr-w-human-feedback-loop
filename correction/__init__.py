"""
correction/ - Human-in-the-loop correction of a recognized Measure.

Two layers, deliberately kept apart:

  1. A deterministic core (correction.edit): apply a structured EditOp to a
     Measure and return a new Measure. No LLM, no music21, pydantic-pure, and
     fully covered by deterministic evals. This is the part that actually
     changes the music.

  2. An LLM boundary (correction.interpret): turn a free-text human utterance
     into an EditOp. STUBBED this session - the language-model call is a later
     concern and stays isolated here so the core never depends on it.

The structured edit vocabulary shared by both layers lives in correction.ops:
SetDuration, SetPitch, DeleteEvent, InsertEvent (the EditOp union). See
.claude/rules/correction.md for the decisions behind the split and the scope.
"""

from correction.edit import EditError, apply_edit
from correction.interpret import interpret
from correction.ops import (
    DeleteEvent,
    EditOp,
    InsertEvent,
    SetDuration,
    SetPitch,
)

__all__ = [
    "apply_edit",
    "EditError",
    "interpret",
    "EditOp",
    "SetDuration",
    "SetPitch",
    "DeleteEvent",
    "InsertEvent",
]
