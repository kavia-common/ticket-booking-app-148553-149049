# BackendAPI - Ticket Booking

FastAPI backend for the ticket booking application. Exposes REST endpoints for users, bookings, payments, notifications, and admin operations. Uses PostgreSQL (async SQLAlchemy) and generates OpenAPI spec consumed by other containers.

## Run (dev)

1. Create a `.env` with:
```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME
REACT_APP_FRONTEND_URL=http://localhost:3000
REACT_APP_BACKEND_URL=http://localhost:3001
```

2. Install deps:
```
pip install -r requirements.txt
```

3. Start server (port 3001):
- Recommended (entry script ensures correct import path):
```
python run.py
```

- Or direct uvicorn (ensure working directory is BackendAPI so module path resolves):
```
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
```

4. Generate OpenAPI:
```
python -m src.api.generate_openapi
```

Notes:
- If `DATABASE_URL` is not set, the app falls back to an in-memory SQLite database for scaffolding.
- Replace mock login with real authentication before production.
- If you see "Error loading ASGI app. Could not import module 'main'", use `python run.py` or specify the full import path `src.api.main:app`. Ensure `src/api/__init__.py` exists (it does).
