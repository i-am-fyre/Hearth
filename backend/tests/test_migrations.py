"""Startup migrations (app.db.migrations.upgrade_database) against real PostgreSQL."""
import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from app.db import migrations
from app.db.database import Base

HEAD = ScriptDirectory.from_config(migrations._alembic_config()).get_current_head()


def _reset_schema(engine):
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


@pytest.fixture
def blank_db(db_engine):
    """An empty schema; the full schema is restored afterwards for other tests."""
    _reset_schema(db_engine)
    yield db_engine
    _reset_schema(db_engine)
    migrations.upgrade_database(db_engine)


def _version(engine) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def _receipt_fk_count(engine) -> int:
    fks = inspect(engine).get_foreign_keys("receipts")
    return sum(1 for fk in fks if fk["referred_table"] == "transactions")


def _insert_user_and_receipt(conn, transaction_id):
    conn.execute(text(
        "INSERT INTO users (id, email, password_hash, created_at) "
        "VALUES (1, 'a@example.com', 'x', now())"
    ))
    conn.execute(text(
        "INSERT INTO receipts (user_id, transaction_id, file_path, original_filename, mime_type, status, created_at) "
        "VALUES (1, :tid, 'f', 'r.jpg', 'image/jpeg', 'linked', now())"
    ), {"tid": transaction_id})


def test_fresh_database_is_migrated_to_head(blank_db):
    migrations.upgrade_database(blank_db)
    assert _version(blank_db) == HEAD
    assert _receipt_fk_count(blank_db) == 1


def test_running_twice_is_a_no_op(blank_db):
    migrations.upgrade_database(blank_db)
    migrations.upgrade_database(blank_db)
    assert _version(blank_db) == HEAD


def test_legacy_create_all_database_is_adopted(blank_db):
    """Packaged releases up to v0.1.10 used create_all() and kept no migration history."""
    Base.metadata.create_all(blank_db)
    assert "alembic_version" not in inspect(blank_db).get_table_names()
    with blank_db.begin() as conn:
        _insert_user_and_receipt(conn, None)

    migrations.upgrade_database(blank_db)

    assert _version(blank_db) == HEAD
    assert _receipt_fk_count(blank_db) == 1  # kept, not duplicated
    with blank_db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM receipts")).scalar_one() == 1


def test_dangling_receipt_link_is_cleared_when_adding_fk(blank_db):
    """Databases built from migrations lacked the FK, so links could point at deleted transactions."""
    cfg = migrations._alembic_config()
    with blank_db.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, migrations.LEGACY_BASELINE_REVISION)
    assert _receipt_fk_count(blank_db) == 0
    with blank_db.begin() as conn:
        _insert_user_and_receipt(conn, 999)  # no such transaction

    migrations.upgrade_database(blank_db)

    assert _receipt_fk_count(blank_db) == 1
    with blank_db.connect() as conn:
        assert conn.execute(text("SELECT transaction_id FROM receipts")).scalar_one() is None
