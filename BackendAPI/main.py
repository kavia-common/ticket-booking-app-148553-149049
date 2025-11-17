"""
PUBLIC_INTERFACE
ASGI shim for uvicorn to run the FastAPI app using `uvicorn main:app`.

This file exists so that preview environments or commands that assume a top-level
`main:app` can import the FastAPI application without needing to know the
internal module path (`src.api.main:app`).

Usage:
    uvicorn main:app --host 0.0.0.0 --port 3001

Notes:
- The canonical app location remains src.api.main:app.
- Prefer using `python run.py` for local development which sets up sys.path and env flags.
- This module intentionally re-exports `app` as a public interface for uvicorn and tooling.
- If the working directory is not the BackendAPI root, this module will attempt
  to add the BackendAPI directory to sys.path for reliable imports.
"""
from pathlib import Path
import sys

# Best-effort: ensure BackendAPI directory is on sys.path for import to succeed
_this_file = Path(__file__).resolve()
_backend_dir = _this_file.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

try:
    from src.api.main import app  # re-export for uvicorn discovery
except Exception as exc:
    # Provide clearer feedback if imports fail
    raise RuntimeError(
        "Failed to import FastAPI app from src.api.main. Ensure you are running "
        "`uvicorn main:app` from the BackendAPI directory or use `python run.py`. "
        f"Original error: {exc}"
    ) from exc

# Explicitly declare public interface to satisfy linters (F401) for re-exported symbol.
__all__ = ["app"]
