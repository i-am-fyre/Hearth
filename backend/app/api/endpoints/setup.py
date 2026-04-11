from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import os
import sqlalchemy
from app.core.config import settings

router = APIRouter()

class SetupConfig(BaseModel):
    database_url: str

class DbTestResult(BaseModel):
    success: bool
    message: str

@router.get("/status")
def get_setup_status():
    """Check if the app is currently in setup mode."""
    # We'll determine this at the app level, but this check is for the UI
    return {
        "database_connected": False, # If they reached this API, it means it's not connected or we are in setup mode
        "config_path": "/etc/hearth/hearth.conf",
        "is_writable": os.access("/etc/hearth/hearth.conf", os.W_OK) if os.path.exists("/etc/hearth/hearth.conf") else os.access("/etc/hearth", os.W_OK)
    }

@router.post("/test-db", response_model=DbTestResult)
def test_database_connection(config: SetupConfig):
    """Test a provided connection string without saving it."""
    try:
        engine = sqlalchemy.create_engine(config.database_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return {"success": True, "message": "Connection successful!"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/save-config")
def save_configuration(config: SetupConfig):
    """Save the valid configuration to the hearth.conf file."""
    # 1. Verify connection one last time
    test = test_database_connection(config)
    if not test["success"]:
        raise HTTPException(status_code=400, detail=f"Cannot save invalid configuration: {test['message']}")

    # 2. Write to config file
    conf_path = "/etc/hearth/hearth.conf"
    
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

@router.post("/restart")
def restart_application():
    """Trigger an application exit. systemd will handle the restart."""
    import sys
    # We use a slight delay to allow the response to reach the client
    import threading
    def t():
        import time
        time.sleep(1)
        os._exit(0)
    
    threading.Thread(target=t).start()
    return {"message": "Application is restarting..."}
