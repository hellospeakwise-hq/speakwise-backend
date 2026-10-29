# Deployment

This project is deployment-ready as a Docker image, but the repository contains
several partially overlapping deployment paths. This page recommends **one**
target, documents the environment it needs, and calls out the gaps in the other
manifests so you do not deploy a web process without its workers.

> **Recommended path:** build the provided `Dockerfile`, run it on **DigitalOcean
> App Platform** with managed PostgreSQL and S3-compatible media storage, and add
> a **worker component** plus scheduled jobs. The existing `.do/app.yaml` is the
> starting point, but it currently defines only the web service. The worker and
> scheduler additions are mandatory, not optional.

The alternatives are AWS-style VPS + Gunicorn/Nginx and Railway. They are
described below because the repository already contains configuration for them.

## Runtime topology

```mermaid
flowchart TD
    Internet[Internet] --> Proxy[TLS / load balancer]
    Proxy --> Web[Gunicorn web container]
    Web --> DB[(PostgreSQL)]
    Web --> Cache[(django_cache table)]
    Web --> Media[(S3-compatible bucket)]
    Web --> Queue[(django_tasks_db queue)]
    Worker[db_worker container] --> Queue
    Worker --> DB
    Worker --> Mail[Mailgun]
    Scheduler[Scheduled jobs] --> DB
```

Required processes:

| Process | Command | Purpose |
|---|---|---|
| Web | Docker `CMD` → Gunicorn on `0.0.0.0:8000` | Serve HTTP. |
| Worker | `python manage.py db_worker` | Consume queued email tasks. |
| Scheduler (external) | `python manage.py close_expired_cfps` | Daily CFP cleanup. |
| Scheduler (external) | `python manage.py cleanup_auth_tokens` | Daily OTP/OAuth code cleanup. |

There is no in-process scheduler. Without a worker, queued emails (OTP, welcome,
password reset, organization, and invitation emails) never send. Follower
notifications are created synchronously in the database and do not depend on
the worker. Without the scheduled commands, expired CFPs and auth rows
accumulate.

## Container behaviour

`Dockerfile`:

- Builds Python 3.14 slim and installs dependencies with `uv sync --frozen`.
- Runs as the non-root `django` user.
- Sets `DJANGO_SETTINGS_MODULE=speakwise.settings.production`.
- Runs `collectstatic` at build time with a dummy build-only `SECRET_KEY`.
- Executes `entrypoint.sh`, which runs `migrate --noinput` and
  `createcachetable`, then execs Gunicorn.
- Starts Gunicorn with 3 workers, port 8000, 60-second timeout.
- Defines a Docker `HEALTHCHECK` against `http://localhost:8000/health/`.

`entrypoint.sh` means every container start attempts migrations. With multiple
web replicas, migrations can race at deploy time. On platforms that support a
release/pre-deploy command, run migrations once there and remove the dependency
on concurrent startup. The commands are idempotent, but a lock is still safer.

### Docker health-check caveat

Production sets `SECURE_SSL_REDIRECT = True`. The image's internal health check
requests plain HTTP without `X-Forwarded-Proto: https`, so it receives a redirect
to `https://localhost:8000/health/`; following that redirect inside the container
fails TLS. Use the platform's HTTP health check (`.do/app.yaml` uses `/health/`
through the load balancer) as authoritative, or make the internal check send
`X-Forwarded-Proto: https`. Do not assume the Docker `HEALTHCHECK` is green in
production.

## Environment variables

Create these in the platform's secret manager or a root-owned `.env` with mode
`600`. Never commit them.

### Required

| Variable | Notes |
|---|---|
| `SECRET_KEY` | Production refuses to start without it. Use a long random value. |
| `DJANGO_SETTINGS_MODULE` | `speakwise.settings.production`. The image already sets it. |
| Database | `DATABASE_URL` **or** `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. |
| `ALLOWED_HOSTS` | Comma-separated hostnames, no scheme. Defaults to the speak-wise domains. |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated full origins, including `https://`. |
| `FRONTEND_URL` | Used in OAuth redirects, reset links, and feedback QR URLs. |
| Email | `MAILGUN_API_KEY`, `MAILGUN_SENDER_DOMAIN`, `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`. Production always uses the Mailgun backend; unset values cause delivery failures. |

### Database selection rules

```text
DATABASE_URL is set?
├── yes → parse it; DB_* values are ignored
│         ssl_require=True unless the URL contains "railway.internal"
└── no  → use DB_*; DB_SSLMODE defaults to "require"
          set DB_SSLMODE=disable for a non-SSL database
```

Use `DATABASE_URL` for managed platforms. DigitalOcean Managed PostgreSQL needs
TLS; Railway's internal URL does not support it, hence the special case.

### Recommended and optional

| Variable | Purpose |
|---|---|
| `CORS_ALLOWED_ORIGINS_EXTRA` | Extra browser origins. Production also hard-codes localhost and `speakwise-*.vercel.app` regexes. |
| `STATIC_ROOT` | Defaults to `<BASE_DIR>/staticfiles`. WhiteNoise serves collected files. |
| `MEDIA_ROOT` | Only used with local storage. Ignored effectively when a bucket is configured. |
| `R2_BUCKET_NAME` / `AWS_STORAGE_BUCKET_NAME` | Turns on S3 storage when either is set. |
| `R2_ENDPOINT_URL` / `AWS_S3_ENDPOINT_URL` | S3-compatible endpoint (Spaces, R2, MinIO). |
| `R2_ACCESS_KEY_ID` / `AWS_ACCESS_KEY_ID` | Bucket credentials. |
| `R2_SECRET_ACCESS_KEY` / `AWS_SECRET_ACCESS_KEY` | Bucket credentials. |
| `R2_PUBLIC_URL` / `AWS_S3_CUSTOM_DOMAIN` | Public media domain; the app strips `http(s)://`. |
| `R2_REGION_NAME` / `AWS_S3_REGION_NAME` | Defaults to `auto`. |
| `AWS_DEFAULT_ACL` | Optional canned ACL for the bucket. |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI` | GitHub OAuth. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | Google OAuth. |
| `TURNSTILE_SECRET_KEY` | Enables Cloudflare Turnstile on registration. Empty disables it. |
| `ADMIN_NOTIFICATION_EMAILS` | Comma-separated recipients for new-organization review alerts. |
| `BACKEND_URL` | Absolute backend base used by integrations/emails. |
| `PORT` | Defaults to 8000; platforms usually inject it. |

`DEBUG` in the environment does not enable debug mode in production;
`production.py` hard-codes `DEBUG=False`. Do not set `DEBUG=1` in a production
manifest and assume it changes behaviour.

### Minimal production example

```dotenv
DJANGO_SETTINGS_MODULE=speakwise.settings.production
SECRET_KEY=<generated-secret>
DEBUG=False

DATABASE_URL=postgres://user:password@db.example.com:5432/speakwise?sslmode=require
ALLOWED_HOSTS=apis.speak-wise.live,speak-wise.live
CSRF_TRUSTED_ORIGINS=https://apis.speak-wise.live,https://speak-wise.live
CORS_ALLOWED_ORIGINS_EXTRA=https://speak-wise.live
FRONTEND_URL=https://speak-wise.live

DEFAULT_FROM_EMAIL=SpeakWise <hello@speak-wise.live>
SERVER_EMAIL=errors@speak-wise.live
MAILGUN_API_KEY=<key>
MAILGUN_SENDER_DOMAIN=mg.speak-wise.live

AWS_STORAGE_BUCKET_NAME=<bucket>
AWS_S3_ENDPOINT_URL=https://fra1.digitaloceanspaces.com
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_S3_CUSTOM_DOMAIN=<cdn-or-bucket-domain>
```

Do not copy placeholder values. The example is intentionally incomplete for
OAuth and Turnstile.

## Recommended: DigitalOcean App Platform

1. Create a managed PostgreSQL 15 database. Set `DATABASE_URL` from its
   connection string (SSL required).
2. Create an S3-compatible bucket (DigitalOcean Spaces or another provider) and
   set the storage variables. Do not rely on local media: App Platform
   containers have ephemeral filesystems.
3. Create the app from the repository using the Dockerfile, or apply
   `.do/app.yaml` and then update it. The manifest sets the health check to
   `/health/`, port 8000, production settings, and production domains.
4. Add the required secrets. At minimum: `SECRET_KEY`, `DATABASE_URL`,
   database credentials if not in the URL, Mailgun values, `FRONTEND_URL`, and
   storage credentials.
5. Add a **worker** component using the same image with run command
   `python manage.py db_worker`. The current manifest defines only `services`
   and a database; without this component, emails stay queued.
6. Add two **scheduled jobs** (or platform cron equivalents):
   - daily: `python manage.py close_expired_cfps`
   - daily: `python manage.py cleanup_auth_tokens`
   Optionally run `purge_unverified_users --days 30 --delete --yes` monthly.
7. Point the domain at the web component, terminate TLS at the platform, and
   keep `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `FRONTEND_URL` aligned.
8. Deploy and verify using the checklist below.

The platform health check should show `database: "ok"`; that is the readiness
signal. The Dockerfile's internal health check is not reliable under HTTPS
redirect, as noted above.

## Alternative: Railway

`railway.toml` builds the same Dockerfile and uses `/health/` with a 60-second
timeout. Railway injects `PORT`; the entrypoint preserves it. If you choose
Railway:

- Use a Railway PostgreSQL service and set `DATABASE_URL`. Internal
  `railway.internal` URLs disable SSL correctly; external URLs force SSL.
- Add a second service from the same image with command
  `python manage.py db_worker`; the current manifest has no worker.
- Use S3-compatible storage. The Railway filesystem is ephemeral.
- Add scheduled jobs outside the repo, or use Railway's cron facility.
- Set `ALLOWED_HOSTS` to the Railway/custom domain; the defaults are the
  speak-wise domains and will reject other hosts.

## Alternative: VPS + Gunicorn + Nginx

This is the path implied by the SSH deploy workflows, but the Nginx and systemd
unit files are **not in this repository**. You must provide and maintain them.

Expected layout, based on the workflows:

```text
/home/speakwise/speakwise-backend     # git checkout
/home/speakwise/speakwise-backend/.env
systemd: gunicorn.service             # runs speakwise.wsgi:application
systemd: speakwise-worker.service     # runs manage.py db_worker
nginx: reverse proxy + /static/ + /media/
cron: close_expired_cfps, cleanup_auth_tokens
```

Deployment:

```bash
cd /home/speakwise/speakwise-backend
git pull origin main
pip install uv
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

Because production settings share the same database cache, the `django_cache`
table must exist (`createcachetable`). The CI workflows do not create it explicitly
in the VPS path; ensure provisioning does.

Use a persistent local `MEDIA_ROOT` and let Nginx serve `/media/`, or configure a
bucket. Production URL patterns do not serve media through Django when
`DEBUG=False`.

## CI/CD workflows

| Workflow | Trigger | Behaviour |
|---|---|---|
| `deploy.yml` | Push to `main` | Runs `precommit` and `migrations-test` reusable workflows, then SSHes to a DigitalOcean droplet with `DO_*` secrets, writes `.env` from secrets, migrates, collects static, restarts Gunicorn/Nginx. |
| `deploy-prod.yml` | Push to `main` | SSHes to a VPS with `VPS_*` secrets, pulls, syncs, migrates, collects static, restarts Gunicorn/Nginx. No test gate. |
| `deploy-staging.yml` | Push to `development` | Runs tests with the SQLite test settings. The SSH deploy job is commented out. |
| `.do/app.yaml` / `railway.toml` | Platform-managed | Build and deploy the Docker image; not driven by the SSH workflows. |

> **Duplicate deployment:** `deploy.yml` and `deploy-prod.yml` both trigger on
> every push to `main` and use different secret sets (`DO_*` vs `VPS_*`). If both
> are enabled they can deploy the same commit to two servers. Choose the target
> you actually operate and disable or remove the other workflow after agreement.

The App Platform/Railway manifests are not wired into either SSH workflow. If
you choose the recommended platform path, do not also leave an SSH workflow
deploying the same branch.

## First-deploy verification

```bash
# Liveness and database readiness
curl -fsS https://<host>/health/

# Schema and docs are reachable
curl -fsS https://<host>/api/schema/ >/dev/null
curl -fsS https://<host>/api/docs/ >/dev/null

# Check migration state; output should be empty
uv run python manage.py makemigrations --check --dry-run

# Check deployment configuration and review warnings
uv run python manage.py check --deploy --settings=speakwise.settings.production
```

Then verify end to end:

1. Register a new user and receive the OTP email.
2. Verify the OTP and log in.
3. Create a speaker profile and upload an avatar; open the returned media URL.
4. Submit an event; confirm it is inactive in `/api/events/me/`.
5. Approve it as a superuser and confirm it appears publicly.
6. Submit feedback through a speaker experience QR and confirm the cooldown.
7. Trigger a follower notification and confirm it appears through `/api/notifications/` (this path is synchronous and does not use the worker).
8. Confirm staff can open `/admin/` and CKEditor uploads are staff-only.

## Rollback and backups

- **Web rollback:** redeploy the previous image/commit. Application migrations
  may not be backward compatible; check the migration before rolling back.
- **Database:** enable automated snapshots on the managed PostgreSQL service.
  Test restores, not just backups.
- **Media:** enable bucket versioning or lifecycle backups. Local media on a VPS
  must be part of the backup policy.
- **Secrets:** store `.env` in a secret manager. Losing `SECRET_KEY` invalidates
  sessions and signed tokens.
- **Before destructive commands:** `purge_unverified_users` writes a CSV, but
  `User.delete()` cascades profiles and content. Take a database snapshot first.

## Operational gotchas

1. **No worker in the platform manifests.** `.do/app.yaml` and `railway.toml`
   define web only. Add workers or emails never send.
2. **No scheduler.** `close_expired_cfps` and `cleanup_auth_tokens` are manual/
   cron commands, not automatic tasks.
3. **Ephemeral media.** Without S3, uploads disappear on redeploy or scale-in.
4. **Static files require `collectstatic`.** The Docker build does it; a bare VPS
   checkout must do it on every deploy.
5. **Local Docker Compose is inconsistent.** `docker-compose.yaml` runs web with
   production settings but `db_worker` with local settings (immediate backend),
   so the worker does not consume the DB queue. `docker-compose.yml` is a
   different, simpler file and has no port mapping until a prod override is
   applied. Specify the compose files explicitly.
6. **Two compose filenames exist.** `docker-compose.yaml` and
   `docker-compose.yml` are different. `docker compose up` will not merge them;
   use `-f` deliberately.
7. **`DATABASE_URL` wins over `DB_*`.** Changing `DB_*` after switching to a URL
   has no effect.
8. **PostgreSQL SSL defaults to required.** A local or internal database without
   SSL needs `DB_SSLMODE=disable` (split config) or a URL that is recognized as
   internal.
9. **Mailgun is mandatory in production.** There is no console-email fallback.
10. **CORS allows localhost and `*.vercel.app` in production.** The hard-coded
    dev origins and Vercel regex are intentional preview support; review before
    using a different security posture.
11. **OAuth redirect URIs must match exactly** in the provider console and the
    environment, including scheme, host, path, and trailing slash.
12. **No token refresh endpoint.** Access tokens expire after 60 minutes; clients
    must log in again.
13. **HSTS/SSL redirect can break naive health checks.** See the Docker health
    caveat above.
14. **Migrations run on every container start.** Scale carefully and watch logs
    for lock contention during rolling deploys.

For settings and environment details, see [Development](development.md). For the
request/response contract, see the [Endpoint reference](api/endpoints.md).
