#!/bin/sh
# SpotWeldPro AI — production startup script (DEMO_RENDER_02)
#
# Execution order:
#   1. alembic upgrade head      — idempotent schema migration
#   2. seed_demo_user.py         — idempotent READ_ONLY demo account (skipped if DEMO_PASSWORD unset)
#   3. uvicorn                   — production ASGI server
#
# Environment variables consumed:
#   DEMO_USERNAME  (default: demo)   — canonical demo username
#   DEMO_PASSWORD  (required)        — demo user password; skipped if not set
#   All other vars passed through to app.main as-is.
set -e

echo "[start] Running database migrations..."
alembic upgrade head

if [ -n "$DEMO_PASSWORD" ]; then
  echo "[start] Seeding demo user..."
  python scripts/seed_demo_user.py
else
  echo "[start] DEMO_PASSWORD not set — skipping demo user seed."
fi

echo "[start] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
