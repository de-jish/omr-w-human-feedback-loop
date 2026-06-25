"""
validation/validator.py - The rhythm validator itself.

`validate_measure` compares the sum of a measure's event durations against one
full bar of the meter in force (from MeasureContext). All arithmetic is exact
(fractions.Fraction); there is deliberately no tolerance, because a printed bar
either adds up or it does not.
"""

from __future__ import annotations

from fractions import Fraction

from model.score import Measure, MeasureContext
from validation.report import MeasureReport


def validate_measure(measure: Measure, context: MeasureContext) -> MeasureReport:
    """Validate one measure's rhythm against the meter in force.

    Returns a MeasureReport describing whether the events sum to exactly one bar
    and, when they overflow, the index of the first event that spills over.
    """
    expected = context.time.quarter_length
    actual = measure.total_quarter_length
    difference = actual - expected

    overflow_event_index: int | None = None
    if difference > 0:
        # Walk the running total to find where the bar first overflows. This is
        # the actionable bit for the correction UI: not just "too long", but the
        # exact event the human should look at.
        running = Fraction(0)
        for index, event in enumerate(measure.events):
            running += event.duration.quarter_length
            if running > expected:
                overflow_event_index = index
                break

    if difference == 0:
        status = "valid"
        message = (
            f"measure {measure.number}: {actual} == {expected} quarter-notes, "
            f"complete"
        )
    elif difference > 0:
        status = "overflow"
        message = (
            f"measure {measure.number}: {actual} > {expected} quarter-notes, "
            f"overflows by {difference} at event {overflow_event_index}"
        )
    else:
        status = "underflow"
        message = (
            f"measure {measure.number}: {actual} < {expected} quarter-notes, "
            f"short by {-difference}"
        )

    return MeasureReport(
        measure_number=measure.number,
        status=status,
        valid=(status == "valid"),
        expected_quarter_length=expected,
        actual_quarter_length=actual,
        difference=difference,
        overflow_event_index=overflow_event_index,
        message=message,
    )
