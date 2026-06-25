"""
model/score.py - Canonical internal representation for the OMR pipeline.

This module is the single source of truth for how music is represented inside
the app. Every other module (segmentation, recognition, validation, correction,
export) speaks in these objects. It is intentionally pydantic-pure: it does NOT
import music21 or any rendering library, so the core stays light, fast, and
trivially testable. music21 only ever appears in export/.

Scope: clean, printed, single-staff, MONOPHONIC music (one sounding note at a
time). No chords, no multiple voices, no tuplets, no ornaments, no slurs. Clef
changes ARE supported, because cello repertoire moves between bass, tenor, and
treble clefs.

Key design decisions (read these before changing anything):

1. Durations are exact rationals, never floats. A duration is stored as a written
   type ("quarter") plus a dot count, and its value in quarter-note units is
   DERIVED as a fractions.Fraction. This is the whole reason rhythm validation can
   be trusted: 1/2 + 1/2 + 1/4 + 1/4 sums to exactly 3/2, where floats drift.

2. Pitch is stored as WRITTEN, not as sounding pitch. We keep the diatonic step
   (the staff position read through the clef), the octave, and the accidental
   GLYPH actually drawn beside the note (or None if none was drawn). The sounding
   pitch is a downstream concern: it depends on the key signature and any earlier
   accidentals in the same measure. Storing what is on the page is exactly what a
   recognizer can observe.  <-- This is the decision most worth a second look.
   See NOTE_ON_PITCH at the bottom of this file.

3. Measures store only the attributes DECLARED at them. A clef, key, or time
   signature appears on a measure only when it is newly stated, exactly like
   MusicXML. The attributes in force at any measure are computed by walking
   forward from the start: see Score.effective_context().

4. Confidence and source travel with each event, so the validator and the
   correction UI can flag shaky recognition and track who touched what. Both are
   optional, so hand-built test fixtures can leave them out entirely.

Cosmetic things we deliberately do NOT model, because they are derivable from the
above and only affect rendering: stems, flags, beams, note spacing. music21 and
Verovio regenerate these on export.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Annotated, Literal, Union

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_serializer,
    field_validator,
    model_validator,
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


# --------------------------------------------------------------------------- #
# Pitch
# --------------------------------------------------------------------------- #

Step = Literal["A", "B", "C", "D", "E", "F", "G"]
AccidentalGlyph = Literal["natural", "sharp", "flat", "double-sharp", "double-flat"]


class Pitch(BaseModel):
    """A written pitch: a staff position plus an optional drawn accidental.

    octave uses scientific pitch notation (middle C is C4). Cello open strings,
    for reference, are C2, G2, D3, A3.
    """

    step: Step
    octave: int
    # The accidental GLYPH actually drawn next to the note. None means no glyph
    # was drawn (the note may still sound altered via the key signature).
    accidental: AccidentalGlyph | None = None


# --------------------------------------------------------------------------- #
# Duration
# --------------------------------------------------------------------------- #

DurationType = Literal[
    "breve", "whole", "half", "quarter", "eighth", "16th", "32nd", "64th"
]

# Base length of each written type in quarter-note units, exact.
_BASE_QL: dict[str, Fraction] = {
    "breve": Fraction(8),
    "whole": Fraction(4),
    "half": Fraction(2),
    "quarter": Fraction(1),
    "eighth": Fraction(1, 2),
    "16th": Fraction(1, 4),
    "32nd": Fraction(1, 8),
    "64th": Fraction(1, 16),
}


class Duration(BaseModel):
    """A written duration: a base type plus 0-2 augmentation dots.

    The value in quarter-note units is derived, never stored, so there is one
    source of truth and no chance of the stored number drifting from the type.
    """

    type: DurationType
    dots: int = Field(0, ge=0, le=2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def quarter_length(self) -> Fraction:
        # n dots multiply the base by (2 - 1/2**n):
        #   0 dots -> x1, 1 dot -> x3/2, 2 dots -> x7/4.
        return _BASE_QL[self.type] * (Fraction(2) - Fraction(1, 2**self.dots))

    @field_serializer("quarter_length")
    def _ser_ql(self, value: Fraction) -> str:
        # Emit fractions as exact strings ("1/2", "3"), never floats, so eval
        # JSON stays exact and human-readable.
        return str(value)


# --------------------------------------------------------------------------- #
# Events: Note and Rest
# --------------------------------------------------------------------------- #

TieType = Literal["start", "stop", "continue"]
Source = Literal["recognized", "corrected", "validated", "manual"]


class Note(BaseModel):
    """A single sounding note. Monophonic only: never a chord."""

    kind: Literal["note"] = "note"
    pitch: Pitch
    duration: Duration
    # Ties connect this note to an adjacent note of the same pitch (often across a
    # barline). Not needed for rhythm validation, but kept for export fidelity.
    tie: TieType | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    source: Source | None = None


class Rest(BaseModel):
    """A rest. Has a duration but no pitch."""

    kind: Literal["rest"] = "rest"
    duration: Duration
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    source: Source | None = None


# Discriminated on `kind`, so (de)serialization and editing pick the right type.
Event = Annotated[Union[Note, Rest], Field(discriminator="kind")]


# --------------------------------------------------------------------------- #
# Measure attributes
# --------------------------------------------------------------------------- #

ClefSign = Literal["G", "F", "C"]


class Clef(BaseModel):
    """A clef as sign + staff line (counting 1-5 from the bottom line).

    Common cello clefs:
      bass   -> sign F, line 4
      tenor  -> sign C, line 4
      treble -> sign G, line 2
    """

    sign: ClefSign
    line: int = Field(..., ge=1, le=5)


class KeySignature(BaseModel):
    """Key signature as a count of sharps (+) or flats (-), MusicXML convention."""

    fifths: int = Field(..., ge=-7, le=7)


class TimeSignature(BaseModel):
    """A simple time signature. Denominator must be a power of two."""

    numerator: int = Field(..., gt=0)
    denominator: int = Field(..., gt=0)

    @field_validator("denominator")
    @classmethod
    def _power_of_two(cls, v: int) -> int:
        if v & (v - 1) != 0:
            raise ValueError(f"denominator must be a power of two, got {v}")
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def quarter_length(self) -> Fraction:
        """Total quarter-note length of one full measure in this meter."""
        return Fraction(self.numerator * 4, self.denominator)

    @field_serializer("quarter_length")
    def _ser_ql(self, value: Fraction) -> str:
        return str(value)


# --------------------------------------------------------------------------- #
# Measure
# --------------------------------------------------------------------------- #


class Measure(BaseModel):
    """One measure of a single monophonic staff.

    clef / key / time are present only when newly declared at this measure
    (None means "unchanged from earlier"). Use Score.effective_context() to get
    the attributes actually in force here.
    """

    number: int
    events: list[Event] = Field(default_factory=list)
    clef: Clef | None = None
    key: KeySignature | None = None
    time: TimeSignature | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_quarter_length(self) -> Fraction:
        """Sum of event durations, exact. The validator compares this against the
        time signature's quarter_length."""
        total = Fraction(0)
        for e in self.events:
            total += e.duration.quarter_length
        return total

    @field_serializer("total_quarter_length")
    def _ser_ql(self, value: Fraction) -> str:
        return str(value)


# --------------------------------------------------------------------------- #
# Score
# --------------------------------------------------------------------------- #


class MeasureContext(BaseModel):
    """The clef, key, and time signature in force at a given measure, resolved."""

    clef: Clef
    key: KeySignature
    time: TimeSignature


class ScoreMetadata(BaseModel):
    title: str | None = None
    composer: str | None = None
    source_file: str | None = None


class Score(BaseModel):
    """A whole single-staff piece: metadata plus an ordered list of measures."""

    metadata: ScoreMetadata = Field(default_factory=ScoreMetadata)
    measures: list[Measure] = Field(default_factory=list)

    @model_validator(mode="after")
    def _first_measure_declares_context(self) -> "Score":
        # Nothing inherits into measure 1, so it must declare clef, key, and time.
        if self.measures:
            m0 = self.measures[0]
            missing = [
                name
                for name, value in (("clef", m0.clef), ("key", m0.key), ("time", m0.time))
                if value is None
            ]
            if missing:
                raise ValueError(
                    f"first measure must declare {', '.join(missing)}"
                )
        return self

    def effective_context(self, index: int) -> MeasureContext:
        """Clef, key, and time signature in force at measures[index], found by
        walking forward and carrying the last declared value of each."""
        clef: Clef | None = None
        key: KeySignature | None = None
        time: TimeSignature | None = None
        for m in self.measures[: index + 1]:
            if m.clef is not None:
                clef = m.clef
            if m.key is not None:
                key = m.key
            if m.time is not None:
                time = m.time
        if clef is None or key is None or time is None:
            raise ValueError(
                "context not fully established; the first measure must declare "
                "clef, key, and time"
            )
        return MeasureContext(clef=clef, key=key, time=time)


# --------------------------------------------------------------------------- #
# NOTE_ON_PITCH
# --------------------------------------------------------------------------- #
# We store the WRITTEN pitch (step + octave + drawn accidental glyph), not the
# sounding pitch. Two consequences worth understanding:
#
#   * To know what a note actually sounds like, you must apply the key signature
#     and any earlier accidentals in the same measure. That logic lives wherever
#     we need sounding pitch (export, playback), NOT in this model.
#   * The recognizer's job stays concrete: read staff position -> step+octave,
#     and "is there an accidental glyph?" -> accidental. It never has to reason
#     about key context to fill this model in.
#
# The alternative is storing sounding pitch directly (an explicit semitone alter
# per note). That is simpler for playback but throws away what was on the page
# and makes the recognizer responsible for key-context reasoning. If we ever flip
# this decision, it changes Pitch and every module that reads it, so flag it loud.


if __name__ == "__main__":
    # Smoke test / worked example: one 4/4 measure in bass clef, C major,
    # a little C-D-E-F figure that should sum to exactly 4 quarter notes.
    m = Measure(
        number=1,
        clef=Clef(sign="F", line=4),
        key=KeySignature(fifths=0),
        time=TimeSignature(numerator=4, denominator=4),
        events=[
            Note(pitch=Pitch(step="C", octave=3), duration=Duration(type="quarter")),
            Note(pitch=Pitch(step="D", octave=3), duration=Duration(type="eighth")),
            Note(pitch=Pitch(step="E", octave=3), duration=Duration(type="eighth")),
            Note(pitch=Pitch(step="F", octave=3), duration=Duration(type="half")),
        ],
    )
    score = Score(
        metadata=ScoreMetadata(title="smoke test", source_file="none"),
        measures=[m],
    )

    ctx = score.effective_context(0)
    print("measure total:", m.total_quarter_length)
    print("meter expects:", ctx.time.quarter_length)
    print("valid measure:", m.total_quarter_length == ctx.time.quarter_length)
    print("dotted-quarter ql:", Duration(type="quarter", dots=1).quarter_length)
    print("double-dotted-half ql:", Duration(type="half", dots=2).quarter_length)
