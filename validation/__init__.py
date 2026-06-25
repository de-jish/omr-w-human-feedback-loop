"""
validation/ - Rhythm validation for a single monophonic measure.

Public contract (see CLAUDE.md Architecture table):

    validate_measure(measure: Measure, context: MeasureContext) -> MeasureReport

Given a Measure and the MeasureContext in force at it, decide whether the
measure's event durations sum to exactly one full bar of the meter, and if not,
report by how much and (for overflow) at which event the bar first spills over.

Everything here stays in exact rationals (fractions.Fraction). No floats: the
whole point of the validator is that the arithmetic does not lie.
"""

from validation.report import MeasureReport, ValidationStatus
from validation.validator import validate_measure

__all__ = ["validate_measure", "MeasureReport", "ValidationStatus"]
