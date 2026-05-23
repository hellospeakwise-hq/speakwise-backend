#!/bin/bash

echo "Starting staging deploy..."

cd /home/speakwise/speakwise-backend-staging

echo "Pulling latest development branch..."
git fetch origin
git checkout development
git pull origin development

echo "Rebuilding and restarting staging containers..."
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build

echo "Collecting static files..."
docker exec speakwise-backend-staging-web-1 python manage.py collectstatic --noinput

echo "Staging deploy complete!"
