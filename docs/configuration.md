# Configuration

Hearth is configured using environment variables. Copy `backend/.env.example` to `backend/.env` and fill in your values.

## Backend Configuration

All configuration is loaded from `backend/.env` at startup. The Docker Compose service also reads this file via `env_file`.

### Essential Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key — **must be changed in production** | insecure default |
| `POSTGRES_USER` | PostgreSQL username | `hearth` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name | `hearth` |
| `DATABASE_URL` | Full SQLAlchemy connection string | built from above |

> [!WARNING]
> You **must** set a strong, unique `SECRET_KEY` in production. Generate one with:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### Email / SMTP (Optional)

Email is used for household invitation links. Leave blank to disable.

| Variable | Description | Example |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username / email | `you@gmail.com` |
| `SMTP_PASSWORD` | SMTP app password | `xxxx xxxx xxxx xxxx` |
| `SMTP_FROM_EMAIL` | Sender address shown in emails | `you@gmail.com` |
| `FRONTEND_URL` | Base URL for links in emails | `http://localhost:5173` |

> [!NOTE]
> For Gmail, use an **App Password** (not your account password). Enable it at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

### AI Receipt Parsing (Optional)

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key for AI-powered receipt parsing. Falls back to Tesseract OCR if not set. Get a free key at [aistudio.google.com](https://aistudio.google.com/). |

## Frontend Configuration

For local development, ensure the frontend proxy in `vite.config.ts` points to the backend. No additional `.env` file is required for standard local development.

If deploying separately, create `frontend/.env`:

```env
VITE_API_URL=http://your-backend-host:8000/api/v1
```

---

*Proceed to [Account Setup](account_setup.md) to create your first user.*
