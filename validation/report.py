"""
validation/report.py - The validity report returned by the rhythm validator.

Kept pydantic-pure and float-free, exactly like model/score.py. Every
quarter-length quantity is an exact fractions.Fraction and is serialized as a
string ("4", "3/4", "1/2"), never as a float, so eval JSON stays exact.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Literal

from pydantic import BaseModel, field_serializer

# A measure either sums exactly (valid), spills past the bar (overflow), or
# falls short of a full bar (underflow).
ValidationStatus = Literal["valid", "overflow", "underflow"]


class MeasureReport(BaseModel):
    """The verdict on one measure's rhythm.

    `valid` is the one-bit answer the correction UI keys off. The remaining
    fields explain it: how long the bar should be, how long it actually is, the
    signed gap, and - for an overflow only - the index of the first event whose
    running total pushes the bar past full.
    """

    measure_number: int
    status: ValidationStatus
    valid: bool

    # One full bar of the meter vs. the sum of the events actually present.
    expected_quarter_length: Fraction
    actual_quarter_length: Fraction
    # actual - expected. Positive => overflow, negative => underflow, 0 => valid.
    difference: Fraction

    # Index into measure.events of the first event whose cumulative duration
    # exceeds the bar. Only set when status == "overflow"; None otherwise.
    overflow_event_index: int | None = None

    # Human-readable one-liner for logs and the correction UI.
    message: str

    @field_serializer(
        "expected_quarter_length", "actual_quarter_length", "difference"
    )
    def _ser_fraction(self, value: Fraction) -> str:
        return str(value)
