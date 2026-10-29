# Development Guide

This page covers day-to-day work after the project is installed. Start with
[Installation](installation.md) if the application is not running yet.

## Settings modules

`manage.py` defaults to `speakwise.settings.local`. `wsgi.py` and `asgi.py`
default to `speakwise.settings.production`, but an explicit
`DJANGO_SETTINGS_MODULE` environment variable wins.

| Module | Purpose | Database | Email | Background tasks |
|---|---|---|---|---|
| `speakwise.settings.base` | Shared configuration. Not a standalone entry point. | Not configured | — | DB backend (default) |
| `speakwise.settings.local` | Default for `manage.py` and local dev. | PostgreSQL from `DB_*` env vars | Console | Immediate (inline) |
| `speakwise.settings.production` | Deployed runtime. | `DATABASE_URL`, else `DB_*` with SSL | Mailgun via Anymail | DB-backed queue |
| `speakwise.settings.test` | Automated tests. | In-memory SQLite | Console | Immediate |

`local.py` forces `DEBUG=True` and uses a hard-coded development `SECRET_KEY`.
Do not use it in a deployed environment. `production.py` refuses to start
without `SECRET_KEY`, forces `DEBUG=False`, enables HSTS/secure cookies, and
trusts `X-Forwarded-Proto`.

## Daily commands

All Python commands go through `uv`:

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py createcachetable
uv run python manage.py runserver
```

`createcachetable` is not optional locally. The default cache is Django's
`DatabaseCache` in the `django_cache` table; throttling, login lockout, and
other cache reads fail without it.

Useful commands:

```bash
# Django checks
uv run python manage.py check

# New migration after a model change
uv run python manage.py makemigrations

# Verify no model changes are missing a migration
uv run python manage.py makemigrations --check --dry-run

# Interactive shell / database shell
uv run python manage.py shell
uv run python manage.py dbshell

# Clear database cache (throttles, login lockout, etc.)
uv run python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

Migrations are real code: review them, keep them forward-only when possible,
and include data migrations separately from schema migrations. CI runs
`migrate` against PostgreSQL and then `makemigrations --check --dry-run`; a
missing migration fails the workflow.

## Background tasks

Tasks are declared with `django_tasks` in each app's `tasks.py`:

- `users.tasks` — OTP, welcome, password-reset emails; auth-token cleanup task.
- `profiles.tasks` — organization review and status emails.
- `speakerrequests.tasks` — invitation and response emails.
- `events.tasks` — close expired CFPs.

Follower notifications are **not** tasks: `profiles.signals` writes `Notification`
rows synchronously via `transaction.on_commit`.

In local development the task backend is `ImmediateBackend`, so `.enqueue()`
runs synchronously and OTP/welcome emails print to the terminal. You do **not**
need a worker locally.

In production the backend is `django_tasks_db.DatabaseBackend`: tasks are rows in
PostgreSQL and must be consumed by:

```bash
uv run python manage.py db_worker
```

There is no scheduler in the application. Two maintenance routines are
management commands intended to be scheduled externally:

```bash
# Close CFPs whose deadline passed. Intended daily.
uv run python manage.py close_expired_cfps

# Delete used/expired OTP and OAuth exchange codes. Intended daily.
uv run python manage.py cleanup_auth_tokens

# Dry-run stale unverified accounts. Add --delete --yes to remove.
uv run python manage.py purge_unverified_users --days 30
```

`purge_unverified_users` has an admin UI equivalent under **Users → Purge
unverified users** (superusers only) that streams a CSV backup before deletion.

> **Local Docker caveat:** `docker-compose.yaml` runs the web service with
> production settings but the `db_worker` service with local settings. Since
> local settings use the immediate backend, that worker does not consume the
> database queue. For a production-like queue locally, run the worker with a
> settings module that uses `DatabaseBackend` and the same database as the web
> process.

## Database workflow

- The development database is PostgreSQL. Configure `DB_NAME`, `DB_USER`,
  `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` in `.env`.
- Tests use in-memory SQLite unless you override the settings module; do not
  assume SQLite behaviour matches production.
- `Event.title` is unique, `Event.slug` is not; see [Models](models.md) before
  changing event uniqueness.
- Deleting a `User` cascades to profiles and auth codes. Use the purge commands
  or a transactionally safe script for bulk deletions, and take a backup.
- No seed/fixture command exists. Create local data through the API, tests, or
  the admin.

To reset a disposable local database only (this destroys data):

```bash
dropdb "$DB_NAME" && createdb "$DB_NAME"
uv run python manage.py migrate
uv run python manage.py createcachetable
uv run python manage.py createsuperuser
```

## Email, OAuth, and Turnstile

**Email:** local settings use the console backend. The email body, including the
OTP, appears in the `runserver` terminal. Tests sometimes override
`EMAIL_BACKEND` to locmem and assert on `django.core.mail.outbox`.

**OAuth:** set the provider credentials and exact callback URLs:

```dotenv
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:8000/api/users/auth/github-callback/
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/users/auth/google-callback/
```

The provider console must allow the same redirect URI. OAuth `state` is stored in
the Django session, so the start and callback requests must hit the same backend
with a working session cookie. See [Authentication](api/authentication.md#oauth-github-and-google).

**Turnstile:** when `TURNSTILE_SECRET_KEY` is non-empty, registration requires a
valid `turnstile_token`. When it is empty, the check is skipped. This is the
intended local/test path.

## Admin and content operations

- `/admin/` is the Django admin. Create a superuser with
  `uv run python manage.py createsuperuser`.
- Staff access (`is_staff`) is distinct from superuser status (`is_superuser`).
- Events are submitted inactive and approved by editing `is_active` in the
  admin or through a superuser API request.
- Organization profiles start as `pending`; status and `admin_notes` are
  managed in admin.
- Blogs, talks, teams, feedback, and speaker requests are registered in their
  apps' `admin.py` modules.
- CKEditor 5 uploads are staff-only (`CKEDITOR_5_FILE_UPLOAD_PERMISSION =
  "staff"`).

## API schema

While the server runs:

| URL | Purpose |
|---|---|
| `/api/schema/` | OpenAPI schema. |
| `/api/docs/` | Swagger UI. |
| `/api/docs/redoc/` | ReDoc. |
| `/api/redoc/` | ReDoc alias. |

Generate a schema file for client tooling with drf-spectacular:

```bash
uv run python manage.py spectacular --file openapi.yaml
```

Warnings about unable-to-guess serializers are expected for a few legacy
`APIView`s. Behavioural documentation in [Endpoints](api/endpoints.md) is more
complete than the generated schema.

## Common change workflow

1. Read [`AGENTS.md`](../AGENTS.md) and the relevant app before editing.
2. Create a branch using the naming convention in
   [Contributing](contributing.md#branches).
3. Change the model, migration, serializer, view, permission, and tests together.
4. Run:

   ```bash
   uv run python manage.py makemigrations
   uv run python manage.py check
   uv run python manage.py test --settings=speakwise.settings.test
   uv run pre-commit run --all-files
   ```

5. If the change affects API behaviour, update `docs/`.
6. Self-review the diff and open a small PR.

## Development gotchas

- **`DEBUG` is hard-coded true in `local.py`.** Setting `DEBUG=False` in `.env`
  does not affect local settings.
- **`.env` is loaded at process start.** Restart `runserver` after editing it.
- **The cache table is mandatory locally**, even though tests use locmem.
- **Local tasks are synchronous.** A slow email task blocks the request.
- **No token-refresh endpoint exists.** Access tokens expire after 60 minutes.
- **Media files are served by Django only in DEBUG.** Production expects a
  reverse proxy or S3-compatible storage.
- **`project.toml` has stale pytest/mypy paths** (`config.settings.test`,
  `nebula`). Ignore them; see [Testing](testing.md).
- **Ruff scans migrations if invoked directly.** Use pre-commit, or add
  `--exclude '*/migrations/*'`.
