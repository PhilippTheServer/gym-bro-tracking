#!/bin/sh
# Runs schema migrations and optional seeding exactly once, before the API starts.
# This must happen here rather than in the FastAPI lifespan: uvicorn forks several
# workers, and they would otherwise race each other to create the same tables.
set -eu

echo "Applying database migrations…"
alembic upgrade head

if [ "${RUN_SEED:-false}" = "true" ]; then
    echo "Seeding exercise library…"
    python scripts/seed.py
fi

exec "$@"
