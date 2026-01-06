#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files (optional, but good for production)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Execute the CMD from the Dockerfile
exec "$@"
