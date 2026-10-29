# Installation

This guide takes you from a fresh clone to a running local API with a migrated
PostgreSQL database. It covers setup only; for architecture and development
workflows, see [Architecture](architecture.md) and
[Development](development.md).

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.14 | Pinned in `.python-version` and `pyproject.toml` (`requires-python = ">=3.14"`). |
| [uv](https://docs.astral.sh/uv/) | Installs Python and dependencies from `uv.lock`. |
| PostgreSQL 15+ | The `local` settings module uses PostgreSQL. Tests can use SQLite. |
| Git | To clone the repository. |
| Docker (optional) | Only needed for the container-based workflow. |

> **Note:** The root `README.md` still mentions Python 3.10+ and
> `requirements.txt`. Those instructions are out of date. This project uses
> `uv` and `pyproject.toml`; there is no `requirements.txt`.

## 1. Clone the repository

```bash
git clone https://github.com/hellospeakwise-hq/speakwise-backend.git
cd speakwise-backend
```

## 2. Install Python and dependencies

`uv` reads `.python-version` and `uv.lock` automatically.

```bash
uv python install 3.14
uv sync
```

`uv sync` creates a `.venv` directory in the project root and installs the
locked dependency set. You do not need to activate the environment when using
`uv run`; if you prefer a shell, run `source .venv/bin/activate`.

Verify the interpreter:

```bash
uv run python --version
# Python 3.14.x
```

## 3. Create the PostgreSQL database

Create a database and a user that can own it. The commands below assume a local
PostgreSQL installation:

```bash
createdb speakwise
```

If you use a dedicated role:

```sql
CREATE USER speakwise WITH PASSWORD 'speakwise';
ALTER ROLE speakwise CREATEDB;
CREATE DATABASE speakwise OWNER speakwise;
```

The `CREATEDB` privilege is needed if you later run the Django test runner
against PostgreSQL, because Django creates a temporary `test_speakwise`
database.

## 4. Create the environment file

The repository ships `.env_example`. Copy it and edit the values:

```bash
cp .env_example .env
```

At minimum, set these values:

```dotenv
SECRET_KEY="replace-with-a-generated-secret"
DJANGO_SETTINGS_MODULE="speakwise.settings.local"
DEBUG="True"

DB_NAME="speakwise"
DB_USER="speakwise"
DB_PASSWORD="speakwise"
DB_HOST="localhost"
DB_PORT=5432

FRONTEND_URL="http://localhost:3000"
```

Generate a suitable secret key with the helper script:

```bash
./speakwise/scripts/secretkey.sh
```

or directly:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Environment variables used locally

| Variable | Required | Purpose |
|---|---|---|
| `SECRET_KEY` | Yes in production | Django signing key. `local.py` hard-codes a development key and ignores this variable; production refuses to start without it. |
| `DJANGO_SETTINGS_MODULE` | Recommended | Selects `speakwise.settings.local`. `manage.py` defaults to it. |
| `DEBUG` | No | Read by `base.py`; `local.py` forces `DEBUG = True`. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Yes | PostgreSQL connection used by `local.py`. |
| `DATABASE_URL` | Production only | Alternative to the split `DB_*` variables. |
| `FRONTEND_URL` | Recommended | Base URL used in emails, OAuth redirects, reset links, and feedback QR payloads. Notification links are relative paths. Defaults to `http://localhost:3000`. |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI` | For GitHub login | OAuth app credentials. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | For Google login | OAuth app credentials. |
| `TURNSTILE_SECRET_KEY` | Optional | When empty, the Cloudflare Turnstile check on registration is skipped. |
| `ALLOWED_HOSTS` | Production | Comma-separated hostnames. Local settings allow localhost. |
| `CORS_ALLOWED_ORIGINS_EXTRA` | Production | Additional CORS origins. |
| `MAILGUN_API_KEY`, `MAILGUN_SENDER_DOMAIN` | Production | Mailgun credentials. Local email prints to the console. |
| `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL` | Production | Sender addresses. |
| `ADMIN_NOTIFICATION_EMAILS` | Optional | Comma-separated recipients for new-organization alerts. |
| `AWS_*` / `R2_*` | Optional | S3-compatible media storage. Without them, uploads use local disk. |

> **Gotcha:** `local.py` uses Django's PostgreSQL `DatabaseCache`. You must run
> `createcachetable` (step 6) before making authenticated or throttled API
> requests, otherwise login lockout and throttle checks can fail.

### OAuth configuration (optional)

Register callback URLs with each provider:

- GitHub: `http://localhost:8000/api/users/auth/github-callback/`
- Google: `http://localhost:8000/api/users/auth/google-callback/`

Set the matching `*_REDIRECT_URI` values in `.env`. The backend stores OAuth
`state` in the Django session, so callback requests must reach the same backend
instance that served the login redirect.

### Cloudflare Turnstile (optional)

Registration accepts an extra `turnstile_token` field. If
`TURNSTILE_SECRET_KEY` is set, the token is verified with Cloudflare and a
missing or invalid token is rejected. If the key is empty, verification is
skipped, which is the normal local and test configuration.

## 5. Apply migrations

```bash
uv run python manage.py migrate
```

This creates the application tables, the `django_tasks_db` queue tables, and
the SimpleJWT token-blacklist table.

## 6. Create the database cache table

```bash
uv run python manage.py createcachetable
```

The table is named `django_cache` by default. It is used for:

- DRF throttling counters,
- the failed-login lockout,
- anything else using `django.core.cache.cache`.

The production entrypoint runs this command automatically. Locally, you must
run it yourself.

## 7. Create an administrator (optional)

```bash
uv run python manage.py createsuperuser
```

The custom user manager uses email as the login field and also prompts for a
username. The Django admin is available at `http://localhost:8000/admin/`.

## 8. Run the development server

```bash
uv run python manage.py runserver
```

Verify:

- API root/schema UI: <http://localhost:8000/api/docs/>
- ReDoc: <http://localhost:8000/api/redoc/>
- Health check: <http://localhost:8000/health/>
- Django admin: <http://localhost:8000/admin/>

The health endpoint returns `200` when PostgreSQL is reachable and `503` when
it is not.

## 9. Run the background worker (optional locally)

Local settings use the **immediate** task backend. Email tasks execute inline,
so OTP codes and welcome emails appear in the `runserver` terminal without a
worker.

If you run with `speakwise.settings.production` or otherwise use the database
task backend, start a worker in a second terminal:

```bash
uv run python manage.py db_worker
```

## Docker workflow

The repository contains more than one Compose file. Always pass the file you
intend to use explicitly.

### Base Compose with worker

`docker-compose.yaml` defines PostgreSQL, the web container, and a
`db_worker` container. The web container defaults to production settings; the
worker defaults to `speakwise.settings.local`:

```bash
cp .env_example .env
# Set SECRET_KEY, DB_* values, and FRONTEND_URL in .env

docker compose -f docker-compose.yaml up --build
```

The API is exposed on port `8000`. The entrypoint applies migrations and creates
the cache table before starting Gunicorn.

> **Worker caveat:** the `db_worker` service in this file uses local settings,
> which select the immediate task backend. It therefore does not consume the
> PostgreSQL task queue. Set `DJANGO_SETTINGS_MODULE=speakwise.settings.production`
> on the worker as well if you need to exercise asynchronous email locally.

> **Local Docker caveat:** this compose file uses
> `speakwise.settings.production`, which sets `DEBUG=False` and reads
> `ALLOWED_HOSTS` from the environment. Add `localhost,127.0.0.1` to
> `ALLOWED_HOSTS` in `.env` if you want to browse the container from your host.
> The built-in Docker `HEALTHCHECK` also calls `/health/` over plain HTTP while
> production settings redirect HTTP to HTTPS; platform health checks are the
> supported path in deployed environments.

### Simple Compose file

`docker-compose.yml` is a smaller alternative that runs only PostgreSQL and the
web service using `.env`. It does **not** publish a host port by itself, so it
is not reachable from the host until an override adds one:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

That pair exposes port `8000`. The override only adds the host port and restart
policy; the settings still come from `.env` (the shipped example selects
`speakwise.settings.local`). It does not start a task worker. Add one if you
enable the database task backend.

### Staging overrides

The staging deployment uses an override file and a separate environment file:

```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build
```

This expects `.env.staging` and exposes the API on port `8001` on the host.

## Verification checklist

- [ ] `uv run python manage.py check` reports no issues.
- [ ] `uv run python manage.py showmigrations` shows all migrations applied.
- [ ] `/health/` returns `{"status":"ok","database":"ok"}`.
- [ ] `/api/docs/` loads the OpenAPI UI.
- [ ] An admin account can sign in at `/admin/`.
- [ ] Registering a local account prints an OTP in the server terminal.
- [ ] `uv run python manage.py test --settings=speakwise.settings.test` passes.

## Troubleshooting

### `connection refused` when running the server or migrations

PostgreSQL is not running, or the `DB_*` values in `.env` are wrong. Confirm the
database exists and test the connection:

```bash
psql -h localhost -U speakwise -d speakwise
```

### `relation "django_cache" does not exist`

Run:

```bash
uv run python manage.py createcachetable
```

### `DisallowedHost` or `Invalid HTTP_HOST header`

You are using production settings without adding the host to `ALLOWED_HOSTS`.
Set `ALLOWED_HOSTS=localhost,127.0.0.1` in the environment used by that process.

### OTP email never arrives

Locally, OTPs are printed to the `runserver` terminal by the console email
backend. If you switched to the database task backend, start `db_worker`.
Check that `FRONTEND_URL` and `DEFAULT_FROM_EMAIL` are set; Mailgun is only
configured in production.

### Login is locked after repeated failures

The failed-login counter is stored in the Postgres cache and survives process
restarts. Clear it during development:

```bash
uv run python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

### `No module named ...` after pulling changes

The lockfile changed. Re-run:

```bash
uv sync
```

### Python 3.14 not found

```bash
uv python install 3.14
uv sync
```

## Next steps

- Read [Development](development.md) for the day-to-day workflow.
- Read [API overview](api/overview.md) before integrating a client.
- Read [Testing](testing.md) before opening a pull request.
