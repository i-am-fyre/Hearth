"""Shared fixtures for Hearth's backend tests.

Database tests need a PostgreSQL database whose name contains "test". The schema
is dropped and rebuilt from the Alembic migrations at the start of each run, so
never point this at real data:

    TEST_DATABASE_URL=postgresql://hearth:postgres@localhost:5433/hearth_test pytest

Tests that don't touch the database run without it.
"""
import os
from pathlib import Path

# Configure the app before anything imports app.core.config.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if TEST_DATABASE_URL:
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "test-only-secret-key-" + "0" * 43
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""
os.environ["GEMINI_API_KEY"] = ""

import pytest  # noqa: E402
from sqlalchemy import make_url, text  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def db_engine():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set")
    db_name = make_url(TEST_DATABASE_URL).database or ""
    if "test" not in db_name:
        pytest.exit(
            f"Refusing to run: database '{db_name}' does not look like a test database. "
            "The tests drop every table in it.",
            returncode=2,
        )

    from alembic import command
    from alembic.config import Config
    from app.db.database import engine

    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def client(db_engine):
    from fastapi.testclient import TestClient
    from app.db.database import Base
    from app.main import app

    app.state.setup_mode = False
    with TestClient(app) as c:
        yield c

    # Leave every table empty for the next test.
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with db_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


def register(client, email: str, password: str = "correct horse battery staple") -> dict:
    """Register a user, log in, and return Authorization headers."""
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    r = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
