import logging
import os
import secrets
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Values that have shipped as SECRET_KEY placeholders in Hearth's sample configs
# (hearth.conf, docker-compose.yml). They are public, so anyone could use them to
# sign login tokens; treat them exactly like an unset key.
INSECURE_SECRET_KEYS = frozenset({"", "your-super-secret-key-change-it-in-production"})


def _default_secret_key_file() -> Path:
    # .deb installs run as the `hearth` user, whose home is /var/lib/hearth.
    system_dir = Path("/var/lib/hearth")
    if system_dir.is_dir() and os.access(system_dir, os.W_OK):
        return system_dir / "secret_key"
    # Development and Docker: next to the backend sources (gitignored).
    return Path(__file__).resolve().parents[2] / ".secret_key"


def _load_or_create_secret_key(path: Path) -> str:
    """Read the generated key at ``path``, creating it on first run."""
    try:
        existing = path.read_text().strip()
        if existing:
            return existing
    except FileNotFoundError:
        pass

    key = secrets.token_hex(32)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Owner-only permissions from the moment the file exists.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(key + "\n")
    except OSError as e:
        logger.warning(
            "No SECRET_KEY is configured and %s could not be written (%s). Using a "
            "temporary key; everyone will be signed out when Hearth restarts. Set "
            "SECRET_KEY to fix this.", path, e,
        )
        return key

    logger.warning("No SECRET_KEY is configured; generated one and saved it to %s", path)
    return key


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "Hearth"
    API_V1_STR: str = "/api/v1"
    # Leave unset to have Hearth generate and persist a random key (see SECRET_KEY_FILE).
    SECRET_KEY: str = ""
    SECRET_KEY_FILE: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    DATABASE_URL: str = "postgresql://hearth:postgres@db:5432/hearth"

    # SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    GEMINI_API_KEY: str | None = None

    # Versioning
    VERSION_FILE: str = "/app/VERSION"
    GITHUB_OWNER: str = "i-am-fyre"
    GITHUB_REPO: str = "Hearth"

    @model_validator(mode="after")
    def _ensure_secret_key(self) -> "Settings":
        if self.SECRET_KEY.strip() in INSECURE_SECRET_KEYS:
            path = Path(self.SECRET_KEY_FILE) if self.SECRET_KEY_FILE else _default_secret_key_file()
            self.SECRET_KEY = _load_or_create_secret_key(path)
        return self


settings = Settings()
