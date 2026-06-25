# CLAUDE.md

Project memory for the OMR widget. Keep this file **small and stable**. It is an
index, not a wiki. Deep or path-specific guidance goes in `.claude/rules/`;
repeatable workflows go in `.claude/skills/`. Every line here should change how
you act. If a line doesn't, delete it.

## What this is

An Optical Music Recognition tool that turns clean printed sheet music into
editable MusicXML, with a human-in-the-loop correction step. It is one widget in
a larger music web app. Its output (MusicXML) feeds a separate cello fingering
generator, so **MusicXML is the interchange format across the whole app** and the
internal model below is the working representation in between.

**Current phase:** core pipeline taking shape. Done: `model/` (the contract),
`validation/` (rhythm validator), `export/` (MusicXML), and `correction/`'s
deterministic edit core (the utterance->EditOp LLM boundary is stubbed). Next:
recognition, or the `correction/` LLM boundary. There is no CV model yet, and
that is fine.

## Scope (hold this line)

- **In scope:** clean, printed, single-staff, **monophonic** music (one note at a
  time). Solo cello, violin, flute, and similar parts.
- **Out of scope for now** (do NOT add without an explicit decision): piano /
  grand staff, multiple voices, chords, handwriting, tuplets, ornaments, slurs,
  dense orchestral scores.
- **Clef changes ARE in scope.** Cello moves between bass, tenor, and treble.
- When input needs an out-of-scope feature, fail loudly with a clear message.
  Never silently guess.

## Stack

- Python 3.11+
- **pydantic v2** for every typed data contract
- **music21** for MusicXML import/export ONLY. The internal model does not import
  music21; only `export/` does.
- **Verovio** for rendering notation to SVG in the correction UI (later)
- **pytest** for the eval harness
- A CRNN trained on **PrIMuS** for recognition (later)

## Architecture

A pipeline of modules with typed contracts. Inputs and outputs are pydantic models
from `model/`. Work on **one module per session**; you only need that module's
contract plus `model/`, never the whole repo.

| module          | takes                          | returns                                  |
|-----------------|--------------------------------|------------------------------------------|
| `model/`        | -                              | canonical types (Score, Measure, Note…)  |
| `segmentation/` | page image                     | list of single-staff strip images        |
| `recognition/`  | staff strip image              | `Measure` objects (CV lives here, later)  |
| `validation/`   | `Measure` + `MeasureContext`   | validity report (sums? where it overflows)|
| `correction/`   | `EditOp` + `Measure` (core); utterance + `Measure` (boundary, stub) | new `Measure` (core); `EditOp` (boundary) |
| `export/`       | `Score`                        | MusicXML (via music21)                    |
| `evals/`        | -                              | eval harness + JSON cases, per module     |

**Data bus:** everything speaks `model/` objects internally and MusicXML at the
app boundary.

## Iron rules

- **Durations are exact rationals** (`fractions.Fraction`, in quarter-note units).
  NEVER use float for durations. Float rounding is the bug that makes rhythm
  validation lie. The model already enforces this; keep it that way.
- **EDD:** write the eval before the implementation.
- **Every public function ships with at least 3 JSON eval cases** (input, tools to
  call, expected output) under `evals/`. No eval, no merge.
- **Commit on every green eval run**, not just big milestones. Small commits are
  rollback points.
- **The internal model is pydantic-pure.** Only `export/` may import music21.
- For LLM-judged evals only (e.g. correction-intent), swap reference and actual
  outputs across runs to cancel ordering bias. Deterministic evals don't need it.

## How to work

- Run all evals: `pytest evals/`.
- Start each session by reading the target module's contract and its rule file in
  `.claude/rules/` if one exists.
- When a design decision is made, **record it in the relevant file immediately.**
  A decision that lives only in chat is already rotting.

## Reference

- Internal model and its design notes: `model/score.py` (read the module docstring
  and `NOTE_ON_PITCH` before touching pitch).
- Rules and skills will be added as each module comes online.
