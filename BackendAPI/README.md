# BackendAPI - Ticket Booking

FastAPI backend for the ticket booking application. Exposes REST endpoints for users, bookings, payments, notifications, and admin operations. Uses PostgreSQL (async SQLAlchemy) and generates OpenAPI spec consumed by other containers.

## Run (dev)

1. Create a `.env` with:
```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME
REACT_APP_FRONTEND_URL=http://localhost:3000
REACT_APP_BACKEND_URL=http://localhost:3001
```

2. Install dependencies:
- Recommended bootstrap (ensures pip install -r requirements.txt):
```
./install.sh
```
- Or directly:
```
pip install -r requirements.txt
```

3. Start server (port 3001):
- Recommended (entry script ensures correct import path):
```
python run.py
```

- Or direct uvicorn with top-level shim (works from BackendAPI root):
```
uvicorn main:app --host 0.0.0.0 --port 3001 --reload
```

- Or direct uvicorn with full module path:
```
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
```

4. Generate OpenAPI:
```
python -m src.api.generate_openapi
```

5. Quick verification
- Import check:
```
python -c "import sqlalchemy, fastapi, pydantic; print('OK')"
```
- Uvicorn import/start check (will run until Ctrl+C):
```
uvicorn main:app --host 127.0.0.1 --port 3001
```

Notes:
- If `DATABASE_URL` is not set, the app falls back to an in-memory SQLite database for scaffolding.
- Replace mock login with real authentication before production.
- If you see "Error loading ASGI app. Could not import module 'main'", ensure you are in the `BackendAPI` directory (contains `main.py`) and run `uvicorn main:app ...`, or use `python run.py`. Ensure `src/api/__init__.py` exists (it does).
