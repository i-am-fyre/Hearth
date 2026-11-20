"""Bring the database schema up to date with Alembic when Hearth starts.

Packaged (.deb) installs have no way to run `alembic upgrade head` by hand, so the
startup code in bundle.py calls upgrade_database().
"""
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Releases up to v0.1.10 built packaged databases with metadata.create_all(), so
# they have the full schema but no alembic_version table. Their schema matches this
# revision; they are marked as being at it and then upgraded normally.
LEGACY_BASELINE_REVISION = "c1d2e3f4g5h6"

# backend/ in a source checkout; the bundle root in the PyInstaller build.
_BACKEND_DIR = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    # No alembic.ini: its logging section would replace the app's log setup.
    cfg = Config()
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
    return cfg


def upgrade_database(engine: Engine) -> None:
    """Apply any pending migrations. Raises if a migration fails."""
    cfg = _alembic_config()
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        tables = set(inspect(connection).get_table_names())
        if "alembic_version" not in tables and "users" in tables:
            logger.warning(
                "Database has Hearth tables but no migration history; "
                "marking it as revision %s before upgrading.",
                LEGACY_BASELINE_REVISION,
            )
            command.stamp(cfg, LEGACY_BASELINE_REVISION)
        command.upgrade(cfg, "head")
