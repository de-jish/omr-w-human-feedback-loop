"""
export/musicxml.py - Translate a Score into music21 objects and MusicXML.

The mapping is deliberately literal: our types were designed to mirror MusicXML,
so most of this is one-to-one. The two things worth attention:

  * Pitch is WRITTEN. We copy step/octave straight across and attach the drawn
    accidental glyph as a music21 Accidental when one was drawn. We do NOT
    compute sounding pitch here; the key signature is emitted separately and the
    consumer applies it, exactly as on the page.
  * Attributes (clef/key/time) are attached to a measure only when that measure
    declares them, so MusicXML re-states them only on change - the same rule the
    model follows.

This module is the single place music21 is imported.
"""

from __future__ import annotations

from music21 import clef, duration, key, meter, note, pitch, stream, tie
from music21.musicxml import m21ToXml

from model.score import Clef, Duration, Measure, Note, Rest, Score, TimeSignature


def _build_duration(d: Duration) -> duration.Duration:
    # Our DurationType strings ("whole", "quarter", "16th", ...) are exactly
    # music21's type names, so this is a direct hand-off; dots carry over too.
    out = duration.Duration(type=d.type)
    out.dots = d.dots
    return out


def _build_clef(c: Clef) -> clef.Clef:
    out = clef.Clef()
    out.sign = c.sign
    out.line = c.line
    return out


def _build_time(t: TimeSignature) -> meter.TimeSignature:
    return meter.TimeSignature(f"{t.numerator}/{t.denominator}")


def _build_note(n: Note) -> note.Note:
    p = pitch.Pitch()
    p.step = n.pitch.step
    p.octave = n.pitch.octave
    if n.pitch.accidental is not None:
        # Our glyph names ("sharp", "double-flat", ...) match music21's
        # Accidental names exactly. displayStatus=True keeps the glyph drawn
        # even where the key signature would otherwise imply it.
        p.accidental = pitch.Accidental(n.pitch.accidental)
        p.accidental.displayStatus = True
    m21note = note.Note(p)
    m21note.duration = _build_duration(n.duration)
    if n.tie is not None:
        m21note.tie = tie.Tie(n.tie)
    return m21note


def _build_rest(r: Rest) -> note.Rest:
    m21rest = note.Rest()
    m21rest.duration = _build_duration(r.duration)
    return m21rest


def _build_measure(m: Measure) -> stream.Measure:
    out = stream.Measure(number=m.number)
    # Attributes go at offset 0, only when this measure declares them.
    if m.clef is not None:
        out.insert(0, _build_clef(m.clef))
    if m.key is not None:
        out.insert(0, key.KeySignature(m.key.fifths))
    if m.time is not None:
        out.insert(0, _build_time(m.time))
    for event in m.events:
        if isinstance(event, Rest):
            out.append(_build_rest(event))
        else:
            out.append(_build_note(event))
    return out


def score_to_stream(score: Score) -> stream.Score:
    """Convert a Score into a single-part music21 Score.

    One Part, one Measure per model measure, attributes restated only where the
    model declares them. This is the in-memory object the MusicXML serializer
    (and any music21-based playback/rendering) consumes.
    """
    part = stream.Part()
    for m in score.measures:
        part.append(_build_measure(m))

    out = stream.Score()
    if score.metadata.title is not None:
        out.metadata = _build_metadata(score)
    out.append(part)
    return out


def _build_metadata(score: Score):
    from music21 import metadata as m21metadata

    md = m21metadata.Metadata()
    if score.metadata.title is not None:
        md.title = score.metadata.title
    if score.metadata.composer is not None:
        md.composer = score.metadata.composer
    return md


def score_to_musicxml(score: Score) -> str:
    """Serialize a Score to a MusicXML document string."""
    m21score = score_to_stream(score)
    return m21ToXml.GeneralObjectExporter(m21score).parse().decode("utf-8")
