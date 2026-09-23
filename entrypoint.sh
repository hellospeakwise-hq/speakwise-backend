#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Run migrations (includes django_tasks_db tables for the DB task backend)
echo "Running migrations..."
python manage.py migrate --noinput

# Create the Postgres cache table for the DatabaseCache backend.
# Skipped silently when the table already exists (fresh deploys need it).
echo "Ensuring cache table exists..."
python manage.py createcachetable || true

# Collect static files (optional, but good for production)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Execute the CMD from the Dockerfile
exec "$@"
