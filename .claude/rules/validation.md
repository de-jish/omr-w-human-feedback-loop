# validation/ — rhythm validator

Path-specific guidance for the `validation/` module. Read this plus `model/`
before touching the validator. Keep it short; record new decisions here the
moment they're made.

## What it does

Checks that a measure's events sum to exactly one full bar of the meter in
force, and explains any mismatch.

- `validate_measure(measure, context) -> MeasureReport`
- `validate_score(score) -> ScoreReport` — runs the per-measure check across a
  whole score, resolving each measure's effective context via
  `Score.effective_context(i)`, and rolls the results up.

## Decisions (the why, so they don't rot)

- **Exact rationals, zero tolerance.** Comparison is `Fraction == Fraction`.
  A printed bar either adds up or it doesn't; there is no epsilon. Floats are
  banned here for the same reason as in `model/` — they make the validator lie.
- **Three outcomes, named.** `status` is `valid | overflow | underflow`
  (`actual` vs `expected` quarter-length). `valid` is the one-bit field callers
  branch on; the rest explains it.
- **`overflow_event_index`.** On overflow we report the index of the first
  event whose running total crosses the bar — the actionable bit for the
  correction UI ("look at this note"), not just "too long". `None` for
  valid/underflow. There is no analogous index for underflow: a short bar has
  no single offending event.
- **Report carries `expected`, `actual`, signed `difference`.** Positive
  difference = overflow, negative = underflow, zero = valid. All serialized as
  exact strings ("4", "7/2", "-1/2"), never floats.
- **`validate_score` honors mid-piece meter changes.** It validates each
  measure under its *effective* context, so a measure that inherits a 3/4
  declared two bars earlier is checked against 3/4. `ScoreReport.valid` is true
  only when every measure is valid; `invalid_measure_numbers` is the worklist.
- **Pydantic-pure.** No music21, no rendering, no I/O. Same rule as `model/`.

## Out of scope (do NOT add without an explicit decision)

- Pitch / key-signature / accidental correctness. This module validates
  *rhythm* only. Pitch validation, if it ever exists, is a separate concern.
- Tuplets, chords, multiple voices — out of scope for the whole project; the
  model can't even represent them. Don't add validator branches for them.
- Tie/duration interaction beyond summing quarter-lengths. Ties don't change a
  bar's total length, so the validator ignores them by design.

## Evals

- Cases live in `evals/validation/cases/*.json`; run with `pytest evals/`.
- Each case: `{name, description, function, input, expected}` where `expected`
  is the function output as `model_dump(mode="json")`.
- Iron rule enforced in-test: **>= 3 cases per public function.** When you add a
  public function, add its input-builder to `INPUT_BUILDERS` and >= 3 cases.
- Deterministic eval — exact match, no LLM judge, no output/reference swap.
