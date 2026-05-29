"""Vercel serverless entrypoint for the CoralCon FastAPI app.

Vercel's Python runtime discovers the ASGI application exported as ``app``.
We add the project root to ``sys.path`` so the ``web`` and ``coralcon``
packages import cleanly from inside the function bundle.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.app import app  # noqa: E402

__all__ = ["app"]
