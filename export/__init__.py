"""
export/ - Render the canonical model out to MusicXML.

Public contract (see CLAUDE.md Architecture table):

    score_to_stream(score: Score)   -> music21.stream.Score
    score_to_musicxml(score: Score) -> str   # a MusicXML document

This is the ONLY module allowed to import music21 (CLAUDE.md iron rule). The
model stays music21-free; all the translation from our pydantic types into
music21 objects lives here.

We emit written pitch exactly as stored (step + octave + drawn accidental
glyph) and attach clef/key/time to a measure only when that measure declares
them, mirroring both the model and MusicXML's own "state only on change"
convention.
"""

from export.musicxml import score_to_musicxml, score_to_stream

__all__ = ["score_to_stream", "score_to_musicxml"]
