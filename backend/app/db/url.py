"""Helpers for working with database connection URLs."""

# Hearth installs the psycopg (v3) driver. Plain ``postgresql://`` URLs resolve to
# a different driver depending on the SQLAlchemy version (psycopg2 before 2.1,
# psycopg from 2.1 on), and older configs may name psycopg2 explicitly, so pin
# every PostgreSQL URL to the driver that is actually installed.
_POSTGRES_PREFIXES = ("postgres://", "postgresql://", "postgresql+psycopg2://")
_PSYCOPG_PREFIX = "postgresql+psycopg://"


def normalize_database_url(url: str) -> str:
    """Return ``url`` rewritten to use the psycopg driver if it is a PostgreSQL URL."""
    for prefix in _POSTGRES_PREFIXES:
        if url.startswith(prefix):
            return _PSYCOPG_PREFIX + url[len(prefix):]
    return url
