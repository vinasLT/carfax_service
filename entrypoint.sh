#!/bin/bash
set -e

echo "⏳ Waiting for DB"
until pg_isready -h "$CARFAX_DB_HOST" -p "$CARFAX_DB_PORT" -U "$CARFAX_DB_USER"; do
  sleep 1
done
echo "📦 Applying migrations"
alembic upgrade head

echo "🚀 Start App"
exec "$@"