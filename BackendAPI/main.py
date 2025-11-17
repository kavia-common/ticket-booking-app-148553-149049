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
"""
from src.api.main import app  # re-export for uvicorn discovery

# Explicitly declare public interface to satisfy linters (F401) for re-exported symbol.
__all__ = ["app"]
