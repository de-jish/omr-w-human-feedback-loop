# export/ — MusicXML export

Path-specific guidance for the `export/` module. Read this plus `model/` before
touching the exporter. Keep it short; record new decisions here as they're made.

## What it does

Translates the canonical model into music21 objects and MusicXML.

- `score_to_stream(score) -> music21.stream.Score` — one Part, one Measure per
  model measure.
- `score_to_musicxml(score) -> str` — serializes that stream to a MusicXML
  document.

## Decisions (the why, so they don't rot)

- **Only `export/` imports music21.** Iron rule. The model and every other
  module stay music21-free; all translation lives here.
- **The mapping is literal because the model mirrors MusicXML.** Our
  `DurationType` strings ("whole", "quarter", "16th", "breve", …) ARE music21's
  type names, and our accidental glyph names ("sharp", "double-flat",
  "natural", …) ARE music21 `Accidental` names. So most conversion is a direct
  hand-off, not a lookup table. If you add a new type/glyph to the model, check
  the name still matches music21 before assuming it round-trips.
- **Written pitch is exported as-is.** step + octave + the drawn accidental
  glyph. We do NOT compute sounding pitch; the key signature is emitted
  separately and the consumer applies it — same as on the page. Accidentals we
  do draw get `displayStatus = True` so the glyph isn't suppressed.
- **Attributes restated only on change.** clef/key/time are attached to a
  measure only when that measure declares them (`m.clef is not None`, …),
  mirroring the model and MusicXML's own convention. Do not "helpfully" repeat
  inherited attributes on every measure.
- **Metadata is opt-in.** A music21 `Metadata` block is attached only when the
  score has a title; composer rides along when present.

## Out of scope (do NOT add without an explicit decision)

- **MusicXML import / round-trip.** This module is export only. Reading MusicXML
  back into the model is a separate, unbuilt concern.
- Anything the model can't represent (chords, multiple voices, tuplets,
  ornaments, slurs). The model makes these unrepresentable; don't add exporter
  branches for them.
- Cosmetic layout (stems, beams, flags, spacing). music21/Verovio regenerate
  these; we don't emit them.

## Evals

- Cases live in `evals/export/cases/*.json`; run with `pytest evals/`.
- MusicXML is large and version-sensitive, so cases do NOT pin a raw XML string.
  Each case asserts on `stream_facts()` — a normalized, stable view of the
  music21 stream (metadata, and per-measure clef/key/time + per-event facts) —
  which is exactly the mapping this module owns. A separate smoke test confirms
  `score_to_musicxml` still emits a well-formed `<score-partwise>` document.
- Coverage today: basic notes, rests, accidental + tie across a barline, dots,
  mid-piece clef change, all accidental glyphs with a flat key signature, breve,
  and metadata. Iron rule: keep >= 3 cases; add one whenever you extend the map.
