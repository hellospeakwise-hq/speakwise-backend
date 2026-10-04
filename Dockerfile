# Production image for DigitalOcean (App Platform / Droplet) and Railway.
# Same Dockerfile is used on both platforms for build parity.
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies into /app/.venv (locked via uv.lock).
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-install-project

# Final stage: slim runtime, non-root user, no build tools.
FROM python:3.14-slim

RUN addgroup --system django && \
    adduser --system --group django

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE="speakwise.settings.production"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

# Copy project files (respects .dockerignore: excludes .env, .git, media).
COPY . .

# Collect static files at build time so WhiteNoise can serve them without
# requiring a writable disk or database at runtime.
RUN SECRET_KEY=build-only-dummy-key DJANGO_SETTINGS_MODULE=speakwise.settings.production \
    python manage.py collectstatic --noinput --clear || \
    SECRET_KEY=build-only-dummy-key DJANGO_SETTINGS_MODULE=speakwise.settings.production \
    python manage.py collectstatic --noinput

RUN chown -R django:django /app

ENTRYPOINT ["/app/entrypoint.sh"]

USER django

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request;urllib.request.urlopen(f\"http://localhost:{os.getenv('PORT','8000')}/health/\")"

# Production WSGI server. Never use manage.py runserver in production.
CMD ["gunicorn", "speakwise.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
