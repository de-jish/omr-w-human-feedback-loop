"""
model/ - The canonical internal representation for the OMR pipeline.

Re-exports the public types from model.score so callers can write
`from model import Score, Measure, MeasureContext, ...` against the module
named in CLAUDE.md's architecture table.
"""

from model.score import (
    AccidentalGlyph,
    Clef,
    ClefSign,
    Duration,
    DurationType,
    Event,
    KeySignature,
    Measure,
    MeasureContext,
    Note,
    Pitch,
    Rest,
    Score,
    ScoreMetadata,
    Source,
    Step,
    TieType,
    TimeSignature,
)

__all__ = [
    "Step",
    "AccidentalGlyph",
    "Pitch",
    "DurationType",
    "Duration",
    "TieType",
    "Source",
    "Note",
    "Rest",
    "Event",
    "ClefSign",
    "Clef",
    "KeySignature",
    "TimeSignature",
    "Measure",
    "MeasureContext",
    "ScoreMetadata",
    "Score",
]
