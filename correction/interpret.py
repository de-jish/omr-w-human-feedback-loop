"""
correction/interpret.py - The LLM boundary (layer 2). STUB this session.

`interpret(utterance, measure) -> EditOp` is the half of this module that turns
a free-text human correction ("make the third note a half note", "delete that
rest") into a structured EditOp the deterministic core can apply. That mapping
needs a language model and lives entirely behind this function, on purpose, so
the core in correction/edit.py stays pure and fully testable.

Not implemented yet. It is stubbed so the two-layer contract is visible in code
from day one; wiring the actual LLM call is a later session. See
.claude/rules/correction.md for the split and why.
"""

from __future__ import annotations

from model.score import Measure

from correction.ops import EditOp


def interpret(utterance: str, measure: Measure) -> EditOp:
    """Turn a human utterance about `measure` into a structured EditOp.

    Stub: the LLM call is not built yet. Implementing this must NOT pull an LLM
    dependency into the deterministic core - it stays isolated here.
    """
    raise NotImplementedError(
        "correction.interpret (utterance -> EditOp) is the LLM boundary and is "
        "not implemented yet; build the LLM call here without touching the "
        "deterministic core in correction.edit"
    )
