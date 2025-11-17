#!/usr/bin/env python3
"""
PUBLIC_INTERFACE
Entrypoint script to run the FastAPI application via uvicorn.

This ensures the correct module path is used regardless of current working directory.
- Binds to host 0.0.0.0 on port 3001 by default.
- Targets the FastAPI app located at src.api.main:app.

Environment:
- Optionally set UVICORN_HOST and UVICORN_PORT to override defaults.
"""

import os
import sys
from pathlib import Path


def _ensure_project_root_on_path():
    """
    Ensure the project root (BackendAPI folder) is in sys.path so that
    package imports like 'src.api.main' resolve reliably no matter where
    the process is started from.
    """
    # Resolve this script file, then its parent directory (BackendAPI)
    backend_dir = Path(__file__).resolve().parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


def main():
    """Launch uvicorn pointing to src.api.main:app using configured host/port."""
    _ensure_project_root_on_path()

    try:
        import uvicorn  # type: ignore
    except Exception as exc:
        # Provide a clear message if uvicorn is not installed.
        msg = (
            "uvicorn is not installed. Install dependencies with:\n"
            "  pip install -r requirements.txt\n"
            f"Original import error: {exc}"
        )
        print(msg, file=sys.stderr)
        sys.exit(1)

    host = os.getenv("UVICORN_HOST", "0.0.0.0")
    port = int(os.getenv("UVICORN_PORT", "3001"))

    # Start the ASGI app defined in src/api/main.py as 'app'
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=os.getenv("UVICORN_RELOAD", "false").lower() == "true",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
