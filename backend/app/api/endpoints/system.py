from fastapi import APIRouter, HTTPException
import httpx
import time
from pathlib import Path
from app.core.config import settings

router = APIRouter()

# Simple in-memory cache
cache = {
    "latest_version": None,
    "last_check": 0
}

CACHE_TTL = 3600 * 12 # 12 hours

_HERE = Path(__file__).resolve()


def _version_file_candidates() -> list[Path]:
    return [
        # Explicit setting; docker-compose mounts the repo's VERSION at /app/VERSION.
        Path(settings.VERSION_FILE),
        # Next to the app package: /app in the Docker image, and the bundle root in
        # the packaged binary (scripts/build_backend_binary.sh bundles VERSION there).
        _HERE.parents[3] / "VERSION",
        # Repository root, when running from a source checkout.
        _HERE.parents[4] / "VERSION",
    ]


def get_current_version() -> str:
    """The installed version (e.g. "v0.1.10"), or "unknown"."""
    for path in _version_file_candidates():
        try:
            version = path.read_text().strip()
        except OSError:
            continue
        if version:
            return version
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

def parse_version(version: str) -> tuple[int, ...] | None:
    """Turn 'v0.1.10' into (0, 1, 10) so versions compare numerically, not as text."""
    parts = version.strip().lstrip("vV").split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def is_newer_version(latest: str, current: str) -> bool:
    latest_v, current_v = parse_version(latest), parse_version(current)
    if latest_v is None or current_v is None:
        return False
    return latest_v > current_v


@router.get("/info")
async def get_system_info():
    current = get_current_version()
    latest = await fetch_latest_github_version()

    return {
        "version": current,
        "latest_version": latest,
        "update_available": is_newer_version(latest, current),
        "github_url": f"https://github.com/{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}"
    }
