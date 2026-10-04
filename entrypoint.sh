#!/bin/sh

# Production entrypoint for DigitalOcean and Railway.
# Static files are collected at Docker build time; migrations run here so
# each deploy/redeploy converges the database before serving traffic.

# Exit immediately if a command exits with a non-zero status.
set -e

# Respect the platform-provided PORT (Railway injects PORT; default 8000).
PORT="${PORT:-8000}"

# Run migrations (includes django_tasks_db tables for the DB task backend)
echo "Running migrations..."
python manage.py migrate --noinput

# Create the Postgres cache table for the DatabaseCache backend.
# Skipped silently when the table already exists (fresh deploys need it).
echo "Ensuring cache table exists..."
python manage.py createcachetable || true

# Execute the CMD from the Dockerfile (Gunicorn in production)
exec "$@"
