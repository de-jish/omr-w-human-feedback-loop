# correction/ — human-in-the-loop measure editing

Path-specific guidance for the `correction/` module. Read this plus `model/`
before touching it. Keep it short; record new decisions here the moment they're
made.

## What it does

Applies a human's correction to a recognized `Measure`. Split into two layers
that are kept deliberately apart:

1. **Deterministic core** (`correction/edit.py`):
   `apply_edit(measure, op: EditOp) -> Measure`. Applies one structured edit and
   returns a NEW measure. No LLM, no music21, pydantic-pure, fully covered by
   deterministic evals. This is the part that actually changes the music.
2. **LLM boundary** (`correction/interpret.py`):
   `interpret(utterance, measure) -> EditOp`. Turns free text into a structured
   op. **STUBBED** (`NotImplementedError`) until a later session — it needs a
   language model and that dependency must never leak into the core.

The shared vocabulary is `correction/ops.py`: `SetDuration`, `SetPitch`,
`DeleteEvent`, `InsertEvent`, unified as the `EditOp` discriminated union.

## Why the two-layer split

The thing that mutates music must be pure and exhaustively testable, so it's a
plain function over typed inputs with zero model calls. The fuzzy part
(natural language -> intent) is quarantined behind one function. You can build,
test, and trust the core today and swap in the LLM later without touching it.

## Decisions (the why, so they don't rot)

- **`EditOp` is discriminated on `op`**, mirroring the model's `Event`/`kind`
  pattern, so ops round-trip through JSON unambiguously (eval cases, and the
  boundary's future output schema).
- **Events are addressed by integer index** into `measure.events` — the same
  coordinate the validator returns as `overflow_event_index`. The correction UI
  passes straight through the index it was just shown.
- **The core is immutable**: `apply_edit` deep-copies and returns a new measure;
  the input is never mutated, so the UI can preview an edit and discard it.
- **The core only does the edit — it does NOT re-validate rhythm.** An edit may
  legitimately leave the bar overflowing/underflowing; judging that is
  `validation/`'s job, called afterward. Keep these concerns separate.
- **Fail loud, never guess** (project scope rule). `EditError` is raised on:
  out-of-range index; `set_pitch` aimed at a `Rest` (a rest has no pitch).
  `insert_event` is the one op allowed `index == len(events)` (append); range is
  `[0, len]`.
- **Field preservation**: `set_duration`/`set_pitch` use `model_copy(update=…)`,
  preserving the event's `kind`, `tie`, `confidence`, and `source`. Measure-level
  `number`/`clef`/`key`/`time` are never touched by an edit.
- **The core never invents provenance.** It does NOT stamp `source` on edited or
  inserted events: an inserted event keeps whatever `source` the caller set, and
  set_duration/set_pitch preserve the existing `source`. *Open decision:* whether
  edits should mark events `source="corrected"` is deferred; if we want it, do it
  explicitly (an op field or the caller), not as a hidden side effect. Revisit
  when the corrected-vs-recognized distinction is actually consumed.

## Out of scope (do NOT add without an explicit decision)

- **The LLM call.** `interpret` stays a stub this session.
- **Anything the model can't represent** (chords, multiple voices, tuplets,
  ornaments, slurs). No ops for them.
- **Cross-measure edits.** Ops act on a single `Measure`'s event list. Moving
  events across barlines, re-barring, or score-level edits are a separate, unbuilt
  concern.
- **Rhythm/pitch validation** — that's `validation/`. The editor doesn't check
  whether the result is musically valid.

## Evals

- Cases live in `evals/correction/cases/*.json`; run with `pytest evals/`.
- Each case: `{name, description, function, input, expected}` where `input` is
  `{measure, op}` and `expected` is the result `Measure.model_dump(mode="json")`.
  Op dicts are parsed via `TypeAdapter(EditOp)` (the `op` discriminator).
- Iron rule enforced in-test: **>= 3 cases per public function.** Happy-path
  transformations are JSON cases (one per op type + append). The fail-loud paths
  (bad index, set_pitch on a rest) and the no-mutation guarantee are plain pytest
  tests in `test_correction.py`, since they don't fit the "expected output" shape.
- Deterministic eval — exact match, no LLM judge, no output/reference swap.
