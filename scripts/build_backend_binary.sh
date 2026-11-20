#!/bin/bash
# Build the single-file Hearth backend binary (backend/dist/hearth) with PyInstaller.
# Used by the release workflow; run it from the repository root with the backend
# requirements and pyinstaller installed.
set -euo pipefail

cd "$(dirname "$0")/../backend"

pyinstaller --onefile --name hearth --noconfirm \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols \
  --hidden-import uvicorn.protocols.http \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.websockets \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.lifespan \
  --hidden-import uvicorn.lifespan.on \
  --hidden-import fastapi_mail \
  --hidden-import aiosmtplib \
  --hidden-import email.mime.multipart \
  --hidden-import email.mime.text \
  --hidden-import email.mime.base \
  --collect-submodules alembic \
  --add-data "alembic:alembic" \
  bundle.py
