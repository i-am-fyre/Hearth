from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, field_validator
import os
import threading
import time
import sqlalchemy
from app.db.url import normalize_database_url

router = APIRouter()

CONF_PATH = "/etc/hearth/hearth.conf"


def _in_setup_mode(request: Request) -> bool:
    return bool(getattr(request.app.state, "setup_mode", False))


def require_setup_mode(request: Request) -> None:
    """Only allow the wizard's actions while Hearth has no working database.

    These endpoints are unauthenticated by necessity (there are no users until a
    database exists), so once setup is done they must stop working. Otherwise anyone
    who can reach the server could restart it or point it at a database they control.
    """
    if not _in_setup_mode(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hearth is already set up. The setup wizard is disabled.",
        )


class SetupConfig(BaseModel):
    database_url: str

    @field_validator("database_url")
    @classmethod
    def _safe_for_config_file(cls, v: str) -> str:
        v = v.strip()
        # The URL is written into a systemd EnvironmentFile as DATABASE_URL="...".
        # A newline would let it smuggle in other settings; quotes and backslashes
        # would break the quoting. URL-encode such characters in passwords instead.
        if any(c in v for c in '\r\n"\\'):
            raise ValueError("Database URL must not contain line breaks, quotes, or backslashes.")
        if not v.startswith(("postgres://", "postgresql://", "postgresql+")):
            raise ValueError("Database URL must be a PostgreSQL URL (postgresql://...).")
        return v


class DbTestResult(BaseModel):
    success: bool
    message: str


@router.get("/status")
def get_setup_status(request: Request):
    """Tell the setup page whether the wizard is active."""
    if not _in_setup_mode(request):
        return {"setup_mode": False, "database_connected": True}
    return {
        "setup_mode": True,
        "database_connected": False,
        "config_path": CONF_PATH,
        "is_writable": os.access(CONF_PATH, os.W_OK) if os.path.exists(CONF_PATH) else os.access(os.path.dirname(CONF_PATH), os.W_OK),
    }


@router.post("/test-db", response_model=DbTestResult, dependencies=[Depends(require_setup_mode)])
def test_database_connection(config: SetupConfig):
    """Test a provided connection string without saving it."""
    engine = None
    try:
        engine = sqlalchemy.create_engine(
            normalize_database_url(config.database_url), connect_args={"connect_timeout": 5}
        )
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return {"success": True, "message": "Connection successful!"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        if engine is not None:
            engine.dispose()


@router.post("/save-config", dependencies=[Depends(require_setup_mode)])
def save_configuration(config: SetupConfig):
    """Save the valid configuration to the hearth.conf file."""
    # 1. Verify connection one last time
    test = test_database_connection(config)
    if not test["success"]:
        raise HTTPException(status_code=400, detail=f"Cannot save invalid configuration: {test['message']}")

    # 2. Write to config file
    conf_path = CONF_PATH

    # In dev/non-linux, we might not have /etc/hearth
    if not os.access(os.path.dirname(conf_path), os.W_OK) and not os.path.exists(conf_path):
        # Fallback to local file for dev testing
        conf_path = "hearth.conf.local"

    try:
        # Read existing file to preserve other settings if possible
        existing_lines = []
        if os.path.exists(conf_path):
            with open(conf_path, "r") as f:
                existing_lines = f.readlines()

        # Update or add DATABASE_URL
        found = False
        new_lines = []
        for line in existing_lines:
            if line.startswith("DATABASE_URL="):
                new_lines.append(f"DATABASE_URL=\"{config.database_url}\"\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"DATABASE_URL=\"{config.database_url}\"\n")

        with open(conf_path, "w") as f:
            f.writelines(new_lines)

        return {"message": "Configuration saved. The service will now restart to apply changes."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config file: {e}")


def _exit_soon(delay: float = 1.0) -> None:
    """Exit the process after a short delay so the response reaches the client first."""
    def _exit():
        time.sleep(delay)
        os._exit(0)

    threading.Thread(target=_exit, daemon=True).start()


@router.post("/restart", dependencies=[Depends(require_setup_mode)])
def restart_application():
    """Trigger an application exit. systemd will handle the restart."""
    _exit_soon()
    return {"message": "Application is restarting..."}
