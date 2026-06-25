"""
evals/export/test_export.py - Run the export/ JSON eval cases.

MusicXML is a large, version-sensitive document, so the cases do NOT pin a raw
XML string. Instead each case asserts on a normalized, stable view of the
music21 stream the converter builds (clef, key, time, and per-event facts),
which is exactly the mapping export/ is responsible for. A separate smoke test
confirms the full serialization to a MusicXML document still works.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from music21 import clef, key, meter

from model.score import Score
from export import score_to_musicxml, score_to_stream
from evals.harness import load_cases

CASES_DIR = Path(__file__).parent / "cases"


def stream_facts(m21score) -> dict[str, Any]:
    """Normalize a music21 Score into the stable, comparable facts the export
    mapping is responsible for producing."""
    part = m21score.parts[0]
    measures: list[dict[str, Any]] = []
    for m in part.getElementsByClass("Measure"):
        ce = m.getElementsByClass(clef.Clef)
        ke = m.getElementsByClass(key.KeySignature)
        te = m.getElementsByClass(meter.TimeSignature)
        events: list[dict[str, Any]] = []
        for el in m.notesAndRests:
            if el.isRest:
                events.append(
                    {"kind": "rest", "type": el.duration.type, "dots": el.duration.dots}
                )
            else:
                acc = el.pitch.accidental.name if el.pitch.accidental else None
                events.append(
                    {
                        "kind": "note",
                        "step": el.pitch.step,
                        "octave": el.pitch.octave,
                        "accidental": acc,
                        "type": el.duration.type,
                        "dots": el.duration.dots,
                        "tie": el.tie.type if el.tie else None,
                    }
                )
        measures.append(
            {
                "number": m.number,
                "clef": {"sign": ce[0].sign, "line": ce[0].line} if ce else None,
                "key_fifths": ke[0].sharps if ke else None,
                "time": (
                    {"numerator": te[0].numerator, "denominator": te[0].denominator}
                    if te
                    else None
                ),
                "events": events,
            }
        )
    return {"measures": measures}


_CASES = load_cases(CASES_DIR)


@pytest.mark.parametrize("case", _CASES, ids=[c["_file"] for c in _CASES])
def test_export_case(case: dict[str, Any]) -> None:
    assert case["function"] == "score_to_stream"
    score = Score(**case["input"]["score"])

    actual = stream_facts(score_to_stream(score))

    assert actual == case["expected"], (
        f"{case['_file']} ({case['name']}): stream facts did not match expected.\n"
        f"  actual:   {actual}\n"
        f"  expected: {case['expected']}"
    )


def test_at_least_three_cases() -> None:
    """CLAUDE.md iron rule: every public function ships >= 3 JSON eval cases."""
    assert len(_CASES) >= 3, f"expected >= 3 export cases, found {len(_CASES)}"


def test_musicxml_serializes_to_a_document() -> None:
    """score_to_musicxml produces a well-formed MusicXML document, not just a
    music21 object graph."""
    score = Score(**_CASES[0]["input"]["score"])
    xml = score_to_musicxml(score)
    assert xml.lstrip().startswith("<?xml")
    assert "<score-partwise" in xml
