# Hearth

**Hearth** is a self-hosted, open-source personal finance manager with double-entry bookkeeping, AI-powered receipt parsing, CSV bank import, and household multi-user support.

> **Personal Finance for Your Household.**

---

## ✨ Features

- **Double-Entry Bookkeeping** – Every transaction is balanced across accounts with debit/credit entries.
- **AI-Powered Receipt Parsing** – Upload receipts and let Gemini AI (or Tesseract OCR as fallback) extract merchant, date, and total automatically.
- **Batch Receipt Upload** – Upload dozens of receipts at once; the Receipt Center lets you review and link them one by one.
- **Receipt Deduplication** – SHA256 file hashing prevents the same receipt from being processed twice.
- **CSV Bank Import** – Import bank statement CSVs, fuzzy-match transactions, and post them to your ledger.
- **Automated Rules Engine** – Auto-categorize transactions based on description patterns.
- **Budgets** – Set monthly spending limits per category and track variance.
- **Households** – Share a ledger with family members, with role-based access.
- **Secure Receipt Storage** – All uploaded receipt images are encrypted at rest.
- **Analytics Dashboard** – Line charts, pie charts, and account balance trends.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit 5 (Svelte Runes), TypeScript, Tailwind CSS |
| Backend | FastAPI (Python 3.11+), SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 15 |
| AI / OCR | Google Gemini API, Tesseract OCR |
| Storage | Encrypted files on disk (AES via `cryptography`) |
| Dev | Docker Compose |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- (Optional) A [Google Gemini API key](https://aistudio.google.com/) for AI receipt parsing

### 1. Clone the repository

```bash
git clone https://github.com/i-am-fyre/hearth.git
cd hearth
```

### 2. Configure environment variables

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in your values. At minimum, **change the `SECRET_KEY`**:

```bash
# Generate a secure key:
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start the services

```bash
docker compose up -d
```

This starts:
- **PostgreSQL** on port `5433`
- **FastAPI backend** on port `8000`

### 4. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📖 Documentation

Full documentation is available via [MkDocs](https://www.mkdocs.org/):

```bash
pip install mkdocs-material
mkdocs serve
```

Then open [http://localhost:8000](http://localhost:8000).

Documentation covers:
- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Account Setup](docs/account_setup.md)
- [Receipt Processing](docs/receipts.md)
- [Bank Feeds & CSV Import](docs/bank_feeds.md)
- [Automated Rules](docs/rules.md)
- [Budgets](docs/budgets.md)
- [Households](docs/households.md)
- [Accounting Terms](docs/accounting_terms.md)
- [API Reference](docs/api.md)

---

## 🔑 Environment Variables

See [`backend/.env.example`](backend/.env.example) for a full list. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | JWT signing key — **must be changed in production** |
| `POSTGRES_PASSWORD` | ✅ | PostgreSQL password |
| `GEMINI_API_KEY` | Optional | Enables AI receipt parsing (falls back to Tesseract) |
| `SMTP_*` | Optional | Email settings for household invites |

---

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

---

## 🙏 Acknowledgments

This project was built with the assistance of **[Google Antigravity](https://deepmind.google/)**, an agentic AI coding assistant by Google DeepMind. The entire application — from the FastAPI backend to the SvelteKit frontend — was developed collaboratively through AI-assisted pair programming.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
