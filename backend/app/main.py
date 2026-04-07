from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys

from app.core.config import settings
from app.api.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve static files for the frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "build")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    # Fallback for production location
    prod_path = "/usr/share/hearth/frontend"
    if os.path.exists(prod_path):
        app.mount("/", StaticFiles(directory=prod_path, html=True), name="static")


@app.get("/")
def root():
    return {"message": "Welcome to Hearth API"}
