"""Filesystem paths that adapt to read-only/serverless hosts.

On a normal machine (local dev, Render) we write run artifacts into the
repo's ``runs/latest`` directory. On serverless hosts such as Vercel the
project directory is read-only, so writes must go to ``/tmp`` instead.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo root: coralcon/paths.py -> coralcon/ -> <root>
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _serverless() -> bool:
    """True when running on a host with a read-only project filesystem."""
    return bool(os.getenv("VERCEL") or os.getenv("CORALCON_READONLY_FS"))


def runs_dir() -> Path:
    """Return a writable ``runs/latest`` directory for run artifacts."""
    override = os.getenv("CORALCON_RUNS_DIR")
    if override:
        base = Path(override)
    elif _serverless():
        base = Path("/tmp/coralcon-runs")
    else:
        base = PROJECT_ROOT / "runs"
    return base / "latest"
