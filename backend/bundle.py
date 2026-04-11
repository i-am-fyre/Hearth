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
    
    @fastapi_app.exception_handler(404)
    async def spa_fallback(request, exc):
        return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))

# Database Initialization
def init_db():
    from app.db.database import Base, engine
    import app.models  # Import models to register them with Base
    import sqlalchemy
    
    print(f"Checking database connection: {settings.DATABASE_URL.split('@')[-1]}...")
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("Database schema verified/initialized successfully.")
        fastapi_app.state.setup_mode = False
    except Exception as e:
        print(f"CRITICAL: Failed to initialize database: {e}")
        fastapi_app.state.setup_mode = True
        # We don't exit here as the app will serve the Setup Wizard

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Starting Hearth on {host}:{port}...")
    uvicorn.run(fastapi_app, host=host, port=port, log_level="info")
