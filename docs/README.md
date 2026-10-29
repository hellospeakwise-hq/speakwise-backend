# SpeakWise Backend Documentation

SpeakWise is a Django REST Framework backend for a speaker-sourcing platform. It
connects conference organizers with speakers and provides profiles, event and
CFP discovery, talk publishing and review, audience feedback, direct speaker
requests, follows, notifications, blogs, and a public team page.

This directory is the entry point for engineers working on the backend. The
documentation is based on the code at commit `8064e29` (15 October 2026) and
describes the system as it is implemented, including known gaps.

## Start here

| I want to... | Read |
|---|---|
| Set up the project on my machine | [Installation](installation.md) |
| Understand how the system fits together | [Architecture](architecture.md) |
| Learn the API conventions | [API overview](api/overview.md) |
| Authenticate against the API | [Authentication](api/authentication.md) |
| Look up an endpoint | [Endpoint reference](api/endpoints.md) |
| Understand who can call what | [Permissions](api/permissions.md) |
| Understand the database | [Models](models.md) |
| Match the team's code conventions | [Coding style](coding-style.md) |
| Work on the project day to day | [Development](development.md) |
| Run or write tests | [Testing](testing.md) |
| Deploy the service | [Deployment](deployment.md) |
| Open a pull request | [Contributing](contributing.md) |

## Technology stack

| Layer | Technology |
|---|---|
| Language | Python 3.14 |
| Web framework | Django 5.2.5 |
| API | Django REST Framework 3.16.1 |
| Authentication | `djangorestframework-simplejwt` (JWT) |
| Database | PostgreSQL (SQLite in the test settings) |
| Cache and throttling | PostgreSQL `DatabaseCache` |
| Background jobs | `django-tasks` with the database backend |
| API schema | `drf-spectacular` (OpenAPI 3) |
| Filtering | `django-filter` |
| File storage | Local filesystem or S3-compatible object storage |
| Email | Console backend locally; Mailgun via Anymail in production |
| Packaging | `uv` / `pyproject.toml` |
| Static files | WhiteNoise |
| Rich text | `django-ckeditor-5` |

## Applications

| App | Responsibility |
|---|---|
| `users` | Custom email-based user model, JWT auth, OTP verification, OAuth, password reset, admin user list. |
| `profiles` | Speaker profiles, experiences, skills, follows, notifications, organization profiles and CFPs. |
| `events` | Event catalog, community event submission and approval, CFP Market. |
| `talks` | Speaker talks, public talks, talk reviews and review comments. |
| `feedbacks` | Public QR-code feedback collection, per-IP cooldown, speaker feedback summaries. |
| `speakerrequests` | Organizer-to-speaker requests and lightweight email requests. |
| `blogs` | Blog posts with rich-text content. |
| `teams` | Public "Meet the team" content. |
| `base` | Shared timestamped models, pagination, permissions, validators, error handling, health check. |

## API at a glance

- **Base path:** `/api/` for domain endpoints. Generated schema tooling lives at
  `/api/schema/`, `/api/docs/`, and `/api/redoc/`.
- **Health check:** `GET /health/` (outside `/api`).
- **Authentication:** `Authorization: Bearer <access-token>`.
- **Versioning:** `Accept: application/json; version=1.0`.
- **Pagination:** 20 results per page by default, `page_size` up to 100.
- **Error envelope:** `{"detail": "...", "code": "..."}` for general errors;
  field validation errors include the field keys.
- **Throttling:** global anonymous/user limits plus tighter scoped limits on
  authentication endpoints.
- **Domain endpoints:** 51 routes across authentication, profiles, events,
  talks, feedback, speaker requests, blogs, and teams, plus `/health/`.

The full inventory is in the [endpoint reference](api/endpoints.md).

## Repository layout

```text
.
├── base/                 Shared abstractions and the health check
├── blogs/                Blog content
├── events/               Events, CFP Market, submission approval
├── feedbacks/            Audience feedback and QR codes
├── profiles/             Speaker and organization profiles, follows
├── speakerrequests/      Speaking invitations and email requests
├── speakwise/            Project configuration and URL root
│   ├── settings/         base.py, local.py, production.py, test.py
│   ├── scripts/          Legacy Black/Flake8 helper scripts
│   ├── asgi.py
│   ├── urls.py
│   └── wsgi.py
├── talks/                Talks and reviews
├── teams/                Public team members
├── users/                Auth, user model, OTP/OAuth services
├── docs/                 This documentation
├── Dockerfile
├── docker-compose.yaml   Base compose file with a task worker
├── docker-compose.yml    Alternative simple compose file
├── entrypoint.sh
├── manage.py
├── pyproject.toml
└── uv.lock
```

## Key domain rules

- A user has **either** a speaker profile **or** an organization profile, never
  both and never more than one. This is enforced by the profile serializers.
- New email/password accounts are unverified until they complete OTP
  verification. OAuth accounts are verified by the provider.
- Community-submitted events are created as inactive and require admin
  approval. Organization profiles start in `pending` status.
- Speaker experiences carry an opaque `feedback_slug`; audience feedback is
  submitted against that slug rather than an internal ID.
- Speaker and organization profile data is public. Speaker serializers do not
  expose the user's account email; organization responses include the
  organization's `contact_email` and (currently) `admin_notes`.
- Email work is queued in PostgreSQL and requires a worker process in
  production. Follower notifications are created synchronously in the database.

## Conventions used in this documentation

- Example identifiers are synthetic UUIDs or opaque tokens; none refer to real
  records.
- Examples marked **abridged** omit repetitive or deeply nested fields while
  keeping the documented shape accurate.
- All paths are relative to the server root unless stated otherwise.
- The documentation intentionally does **not** describe endpoints that are
  defined but not routed. For example, `PublicEventListView` and
  `MyEventsListView` exist in code but have no URL pattern.
- When current behaviour differs from the intended convention, that difference
  is called out explicitly instead of being presented as policy.

## Getting help

- Read [`AGENTS.md`](../AGENTS.md) before making changes. It is the normative
  contribution guide for this repository.
- API schema and interactive documentation are available at `/api/docs/`
  (Swagger UI) and `/api/redoc/` while the server is running.
- For setup problems, see the troubleshooting section in
  [Installation](installation.md).
