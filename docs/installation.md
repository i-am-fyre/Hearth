# Installation

Hearth uses Docker and Docker Compose to provide an easy, consistent, and quick installation process.

## Prerequisites

Before starting, ensure that your system has the following installed:

1. **[Docker Engine](https://docs.docker.com/engine/install/)**
2. **[Docker Compose](https://docs.docker.com/compose/install/)**
3. **[Node.js](https://nodejs.org/)** (v18 or higher) for local frontend development.
4. **[Python](https://www.python.org/)** (v3.10 or higher) for local backend development.

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/hearth.git
cd hearth
```

## Step 2: Configure Environment Variables

Copy the example environment file and fill in your values:

```bash
cp backend/.env.example backend/.env
```

At minimum, **change the `SECRET_KEY`** before running:

```bash
# Generate a secure random key:
python -c "import secrets; print(secrets.token_hex(32))"
```

See [Configuration](configuration.md) for all available variables.

---

## Quick Start (Recommended)

Hearth includes a `dev.sh` script that automates the starting of all services (Database, Backend, Frontend, and Documentation).

```bash
chmod +x dev.sh
./dev.sh
```

This will:
1. Start the **PostgreSQL** database and **FastAPI** backend via Docker Compose.
2. Start the **MkDocs** documentation server on [http://localhost:8001](http://localhost:8001).
3. Start the **SvelteKit** frontend on [http://localhost:5173](http://localhost:5173).

---

## Alternative: Manual Setup

### 1. Database & Backend
```bash
docker compose up -d
```

### 2. Apply Database Migrations
```bash
docker compose exec backend alembic upgrade head
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Your Hearth instance will now be available at [http://localhost:5173](http://localhost:5173).

---

*Once installed, proceed to [Configuration](configuration.md) to finalize your settings.*
