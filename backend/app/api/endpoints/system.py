from fastapi import APIRouter, HTTPException
import httpx
import os
import time
from app.core.config import settings

router = APIRouter()

# Simple in-memory cache
cache = {
    "latest_version": None,
    "last_check": 0
}

CACHE_TTL = 3600 * 12 # 12 hours

def get_current_version():
    try:
        if os.path.exists(settings.VERSION_FILE):
            with open(settings.VERSION_FILE, "r") as f:
                return f.read().strip()
        else:
            # Fallback for development if /app/VERSION is not mapped
            local_path = os.path.join(os.getcwd(), "VERSION")
            if os.path.exists(local_path):
                 with open(local_path, "r") as f:
                    return f.read().strip()
        return "unknown"
    except Exception:
        return "unknown"

async def fetch_latest_github_version():
    """Fetch latest release tag from GitHub."""
    now = time.time()
    if cache["latest_version"] and (now - cache["last_check"]) < CACHE_TTL:
        return cache["latest_version"]

    url = f"https://api.github.com/repos/{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                latest = data.get("tag_name", "unknown")
                cache["latest_version"] = latest
                cache["last_check"] = now
                return latest
            elif response.status_code == 404:
                # If no releases yet, check the latest commit on main (optional improvement)
                return "v0.1.0" # Default for now
    except Exception as e:
        print(f"Error checking GitHub updates: {e}")
        return cache["latest_version"] or "unknown"
    
    return "unknown"

@router.get("/info")
async def get_system_info():
    current = get_current_version()
    latest = await fetch_latest_github_version()
    
    update_available = False
    if current != "unknown" and latest != "unknown":
        # Simple string comparison (works for v0.1.0 vs v0.2.0)
        # Note: In production you might want a more robust semver comparison
        update_available = latest > current

    return {
        "version": current,
        "latest_version": latest,
        "update_available": update_available,
        "github_url": f"https://github.com/{{settings.GITHUB_OWNER}}/{{settings.GITHUB_REPO}}"
    }
