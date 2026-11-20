# Configuration

Hearth is configured using environment variables. Copy `backend/.env.example` to `backend/.env` and fill in your values.

## Backend Configuration

All configuration is loaded from `backend/.env` at startup. The Docker Compose service also reads this file via `env_file`.

### Essential Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | generated on first start |
| `SECRET_KEY_FILE` | Where a generated key is saved | `/var/lib/hearth/secret_key` (packaged install) or `backend/.secret_key` |
| `POSTGRES_USER` | PostgreSQL username | `hearth` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name | `hearth` |
| `DATABASE_URL` | Full SQLAlchemy connection string | built from above |

> [!NOTE]
> If `SECRET_KEY` is unset (or still the old `your-super-secret-key-change-it-in-production`
> placeholder), Hearth generates a random key on first start and saves it to `SECRET_KEY_FILE`,
> readable only by the Hearth user. To use your own key instead, generate one with:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```
> Changing the key signs everyone out. It does not affect encrypted receipts.

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

No frontend configuration is needed. The dev server (`npm run dev`) talks to the backend at
`http://localhost:8000/api/v1`, and production builds served by the backend use the same
origin (`/api/v1`).

If you host the frontend separately from the backend, create `frontend/.env` before building:

```env
VITE_API_URL=http://your-backend-host:8000/api/v1
```

---

*Proceed to [Account Setup](account_setup.md) to create your first user.*
