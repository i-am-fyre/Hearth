"""Tests that don't need a database."""
import os
import stat
import sys
from pathlib import Path

import pytest

from app.api.endpoints import system
from app.api.endpoints.system import is_newer_version
from app.core.config import Settings
from app.db.url import normalize_database_url

REPO_VERSION = (Path(__file__).resolve().parents[2] / "VERSION").read_text().strip()


def test_current_version_is_read_from_the_repo_version_file():
    assert system.get_current_version() == REPO_VERSION


def test_version_file_setting_wins_and_empty_files_are_skipped(tmp_path, monkeypatch):
    empty = tmp_path / "EMPTY"
    empty.write_text("\n")
    monkeypatch.setattr(system.settings, "VERSION_FILE", str(empty))
    assert system.get_current_version() == REPO_VERSION  # falls through to the next file

    explicit = tmp_path / "VERSION"
    explicit.write_text("v9.9.9\n")
    monkeypatch.setattr(system.settings, "VERSION_FILE", str(explicit))
    assert system.get_current_version() == "v9.9.9"


def test_version_is_unknown_without_a_version_file(tmp_path, monkeypatch):
    monkeypatch.setattr(system, "_version_file_candidates", lambda: [tmp_path / "missing"])
    assert system.get_current_version() == "unknown"


@pytest.mark.parametrize(
    "url, expected",
    [
        ("postgresql://u:p@h:5432/db", "postgresql+psycopg://u:p@h:5432/db"),
        ("postgres://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgresql+psycopg2://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("sqlite:///x.db", "sqlite:///x.db"),
    ],
)
def test_normalize_database_url(url, expected):
    assert normalize_database_url(url) == expected


@pytest.mark.parametrize(
    "latest, current, expected",
    [
        ("v0.1.10", "v0.1.9", True),  # the case plain string comparison gets wrong
        ("v0.2.0", "v0.1.10", True),
        ("v0.1.10", "v0.1.10", False),
        ("v0.1.9", "v0.1.10", False),
        ("unknown", "v0.1.10", False),
        ("v0.1.11", "unknown", False),
    ],
)
def test_is_newer_version(latest, current, expected):
    assert is_newer_version(latest, current) is expected


@pytest.mark.parametrize("placeholder", ["", "  ", "your-super-secret-key-change-it-in-production"])
def test_missing_or_placeholder_secret_key_is_generated_and_persisted(tmp_path, placeholder):
    key_file = tmp_path / "nested" / "secret_key"
    first = Settings(SECRET_KEY=placeholder, SECRET_KEY_FILE=str(key_file))
    assert first.SECRET_KEY not in {"", "your-super-secret-key-change-it-in-production"}
    assert len(first.SECRET_KEY) == 64
    assert key_file.read_text().strip() == first.SECRET_KEY

    # Restarting reuses the saved key, so people stay signed in.
    second = Settings(SECRET_KEY=placeholder, SECRET_KEY_FILE=str(key_file))
    assert second.SECRET_KEY == first.SECRET_KEY


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions")
def test_generated_secret_key_file_is_private(tmp_path):
    key_file = tmp_path / "secret_key"
    Settings(SECRET_KEY="", SECRET_KEY_FILE=str(key_file))
    assert stat.S_IMODE(os.stat(key_file).st_mode) == 0o600


def test_explicit_secret_key_is_used_as_is(tmp_path):
    key_file = tmp_path / "secret_key"
    s = Settings(SECRET_KEY="my-own-key", SECRET_KEY_FILE=str(key_file))
    assert s.SECRET_KEY == "my-own-key"
    assert not key_file.exists()
