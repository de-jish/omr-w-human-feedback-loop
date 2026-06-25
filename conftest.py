"""Make the repo root importable so evals can `from score import ...` and
`from validation import ...` no matter where pytest is invoked from."""

import sys
from pathlib import Path

_ROOT = str(Path(__file__).parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
