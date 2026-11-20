import uvicorn
from app.main import app as fastapi_app
from app.core.config import settings
import os
import sys

# Ensure we are in the correct directory for relative paths
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

# Production Frontend Hosting
# If installed via .deb, the frontend is in /usr/share/hearth/frontend
FRONTEND_PATH = "/usr/share/hearth/frontend"
if os.path.exists(FRONTEND_PATH):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    fastapi_app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="static")
    
    from fastapi.responses import JSONResponse

    @fastapi_app.exception_handler(404)
    async def spa_fallback(request, exc):
        # Unknown API paths get a real 404; handing them the SPA's HTML makes
        # the frontend fail with a confusing JSON parse error instead.
        if request.url.path.startswith(settings.API_V1_STR):
            return JSONResponse({"detail": getattr(exc, "detail", "Not Found")}, status_code=404)
        return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))

# Database Initialization
def init_db():
    from app.db.database import engine
    from app.db.migrations import upgrade_database
    import sqlalchemy

    print(f"Checking database connection: {settings.DATABASE_URL.split('@')[-1]}...", flush=True)
    try:
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
    except Exception as e:
        # No usable database yet: serve the Setup Wizard instead of exiting.
        print(f"CRITICAL: Cannot connect to the database: {e}", flush=True)
        fastapi_app.state.setup_mode = True
        return

    try:
        upgrade_database(engine)
    except Exception as e:
        # The database is reachable but its schema couldn't be updated. Stop rather
        # than run against a half-migrated schema (or reopen the setup wizard on a
        # configured server); systemd will retry and the error is in the journal.
        print(f"CRITICAL: Database migration failed: {e}", flush=True)
        raise SystemExit(1)

    print("Database schema is up to date.", flush=True)
    fastapi_app.state.setup_mode = False

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Starting Hearth on {host}:{port}...")
    uvicorn.run(fastapi_app, host=host, port=port, log_level="info")
