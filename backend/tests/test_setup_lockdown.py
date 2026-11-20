import pytest

from app.api.endpoints import setup as setup_endpoints
from app.main import app
from tests.conftest import TEST_DATABASE_URL


@pytest.fixture(autouse=True)
def restarts(monkeypatch):
    """Record /setup/restart calls instead of letting them kill the test run."""
    calls = []
    monkeypatch.setattr(setup_endpoints, "_exit_soon", lambda *a, **k: calls.append(1))
    return calls


@pytest.fixture
def setup_mode(client):
    app.state.setup_mode = True
    yield client
    app.state.setup_mode = False


DB_BODY = {"database_url": "postgresql://hearth:postgres@localhost:5432/hearth"}


def test_wizard_actions_are_locked_once_set_up(client, restarts):
    assert client.post("/api/v1/setup/test-db", json=DB_BODY).status_code == 403
    assert client.post("/api/v1/setup/save-config", json=DB_BODY).status_code == 403
    assert client.post("/api/v1/setup/restart").status_code == 403
    assert restarts == []


def test_status_reports_normal_mode_without_details(client):
    r = client.get("/api/v1/setup/status")
    assert r.status_code == 200
    assert r.json() == {"setup_mode": False, "database_connected": True}


def test_status_in_setup_mode(setup_mode):
    body = setup_mode.get("/api/v1/setup/status").json()
    assert body["setup_mode"] is True
    assert body["database_connected"] is False


def test_test_db_in_setup_mode(setup_mode):
    r = setup_mode.post("/api/v1/setup/test-db", json={"database_url": TEST_DATABASE_URL})
    assert r.json() == {"success": True, "message": "Connection successful!"}

    r = setup_mode.post(
        "/api/v1/setup/test-db",
        json={"database_url": "postgresql://hearth:wrong@127.0.0.1:1/nope"},
    )
    assert r.json()["success"] is False


@pytest.mark.parametrize(
    "url",
    [
        'postgresql://u:p@h/db\nSECRET_KEY=attacker',
        'postgresql://u:p"@h/db',
        "mysql://u:p@h/db",
    ],
)
def test_unsafe_database_urls_are_rejected(setup_mode, url):
    r = setup_mode.post("/api/v1/setup/test-db", json={"database_url": url})
    assert r.status_code == 422


def test_save_config_preserves_other_settings(setup_mode, tmp_path, monkeypatch):
    conf = tmp_path / "hearth.conf"
    conf.write_text('# comment\nDATABASE_URL="postgresql://old@h/db"\nSECRET_KEY="keep-me"\nPORT=8000\n')
    monkeypatch.setattr(setup_endpoints, "CONF_PATH", str(conf))

    r = setup_mode.post("/api/v1/setup/save-config", json={"database_url": TEST_DATABASE_URL})
    assert r.status_code == 200, r.text
    assert conf.read_text() == (
        f'# comment\nDATABASE_URL="{TEST_DATABASE_URL}"\nSECRET_KEY="keep-me"\nPORT=8000\n'
    )


def test_restart_allowed_in_setup_mode(setup_mode, restarts):
    assert setup_mode.post("/api/v1/setup/restart").status_code == 200
    assert restarts == [1]
