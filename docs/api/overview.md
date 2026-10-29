# API Overview

The SpeakWise API is a JSON HTTP API built with Django REST Framework. This page
describes conventions that apply across endpoints. Endpoint-specific behaviour
is documented in the [Endpoint reference](endpoints.md).

## Base URL

All domain endpoints are mounted under `/api/`:

```text
https://apis.speak-wise.live/api/
```

Locally:

```text
http://localhost:8000/api/
```

Several routes sit outside that prefix:

| Route | Purpose |
|---|---|
| `GET /health/` | Liveness and PostgreSQL readiness probe. |
| `/admin/` | Django admin. |
| `/ckeditor5/` | CKEditor upload endpoints for rich-text content. |

Generated API tooling:

| Route | Purpose |
|---|---|
| `GET /api/schema/` | OpenAPI 3 schema. |
| `GET /api/docs/` | Swagger UI. |
| `GET /api/docs/redoc/` | ReDoc. |
| `GET /api/redoc/` | ReDoc alias. |

The schema UI is public in this codebase. It reflects serializer fields and
`@extend_schema` annotations; where the generated schema is incomplete, this
documentation is the behavioural source of truth.

## Versioning

The project uses DRF's `AcceptHeaderVersioning`:

- Default version: `1.0`
- Allowed version: `1.0`
- There is no `/v1/` path prefix.

Clients may omit the version. To be explicit:

```http
Accept: application/json; version=1.0
```

An unsupported version is rejected with `406 Not Acceptable` rather than
silently downgraded. Omitting the version keeps the default `1.0`.

## Request and response formats

- Requests use `application/json` unless the endpoint accepts a file. File
  uploads use `multipart/form-data`.
- Responses are JSON for API clients that request JSON, except for the QR PNG
  endpoint. DRF's browsable renderer can return HTML when a browser sends an
  HTML `Accept` header; use `Accept: application/json` in clients and scripts.
- Timestamps are ISO 8601 with timezone information where Django stores an aware
  datetime, for example `2026-10-24T12:30:00Z`.
- Date-only fields use `YYYY-MM-DD`.
- Most resource identifiers are UUIDs. `OrganizationCFP` has an integer primary
  key and is only returned nested inside an organization, never as a standalone
  API resource.
- Field names are `snake_case`. Do not convert them to camelCase in requests.
- Trailing slashes matter. Most routes end with `/`; the password-reset confirm
  route is the notable exception (`/api/users/auth/password-reset/confirm`).

### Example request

```bash
curl -s "https://apis.speak-wise.live/api/events/?country=Germany" \
  -H "Accept: application/json; version=1.0"
```

Authenticated request:

```bash
curl -s "https://apis.speak-wise.live/api/users/me/" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer <access-token>"
```

## Authentication summary

The API uses JWT bearer tokens:

```http
Authorization: Bearer <access-token>
```

Missing or invalid credentials produce `401 Unauthorized` on protected routes.
An authenticated user who lacks the required verification or role gets
`403 Forbidden`.

See [Authentication](authentication.md) for login, OTP, OAuth, logout, and
password reset flows.

## Pagination

Page-number pagination is the default for list endpoints:

| Setting | Value |
|---|---|
| Default page size | 20 |
| Client parameter | `page_size` |
| Maximum page size | 100 |
| Page parameter | `page` |

Paginated responses use DRF's standard envelope:

```json
{
  "count": 42,
  "next": "https://apis.speak-wise.live/api/events/?page=2",
  "previous": null,
  "results": []
}
```

Not every collection is paginated:

- `/api/speakers/<slug>/followers/` and `/following/` return at most 100 entries
  in a custom envelope and do not accept `page`.
- Health and schema endpoints are not collections.
- Some detail-adjacent endpoints return a single object or a fixed wrapper.

If a `page` is out of range, DRF returns `404 Not Found`.

## Filtering

Filtering is endpoint-specific and uses `django-filter` or explicit query-param
handling. Common examples:

- Events: `title`, `event_nickname`, `country`, `location`, `slug`,
  `submitted_by`, `is_active`, `is_free`, `cfp_open`, `cfp_open_date`,
  `cfp_deadline`, `start_date_time`, `end_date_time`.
- Talks: `title`, `category`, `speaker`.
- Users (staff only): `email`, `username` (case-insensitive contains).
- Speaker requests: `status`, `event`; email requests: `request_from`,
  `request_to`, `event`.
- Notifications: `is_read` (only the literal value `true`, case-insensitive,
  means true; any other supplied value is treated as false).
- Feedback list: `experience` (feedback slug).

Unknown query parameters are generally ignored. Invalid values may produce
`400 Bad Request` from the filter backend or may be ignored, depending on the
filter type. Do not rely on unvalidated query strings for access control.

## Ordering

Ordering is defined per queryset, not via a global ordering parameter. Notable
orders:

- Events and CFPs: model `Meta.ordering` / queryset order.
- Blogs: `-published_date`, then `-created_at`.
- Team members: `display_order`, then `name`.
- Notifications: newest first.
- Feedback: newest first.

There is no general `ordering` query parameter.

## Throttling

Default DRF throttles:

| Scope | Limit |
|---|---|
| Anonymous | 100 requests/hour |
| Authenticated | 1000 requests/hour |

Scoped throttles on authentication endpoints:

| Endpoint | Scope | Limit |
|---|---|---|
| `POST /api/users/auth/register/` | `register` | 5/hour |
| `POST /api/users/auth/login/` | `login` | 10/minute |
| `POST /api/users/auth/verify-otp/` | `otp_verify` | 10/minute |
| `POST /api/users/auth/resend-otp/` | `otp_resend` | 5/minute |
| `POST /api/users/auth/password-reset/` | `password_reset` | 3/hour |
| `POST /api/users/auth/oauth/token/` | `oauth_token` | 10/minute |

Throttle counters are stored in the shared cache table. A throttled request
returns `429 Too Many Requests` with a `detail` and `code`.

Separately, email/password login has a **lockout** after three failed attempts
within five minutes for the same email address. See
[Authentication](authentication.md#login-lockout).

## Error responses

The shared exception handler and root handlers normalise API errors so clients
receive JSON. This applies to DRF exceptions and, when `DEBUG=False`, to
unhandled errors; with `DEBUG=True` Django may still show its debug page for an
unhandled exception.

General errors:

```json
{
  "detail": "Authentication credentials were not provided.",
  "code": "not_authenticated"
}
```

Field validation errors keep the field keys and add a top-level code:

```json
{
  "email": ["Enter a valid email address."],
  "code": "invalid"
}
```

Custom root handlers return:

```json
{"detail": "Not found.", "code": "not_found"}
```

for an unknown route and:

```json
{"detail": "Internal server error.", "code": "server_error"}
```

for an unhandled server error.

Some endpoints deliberately return domain-shaped errors instead of the generic
envelope. For example, OAuth callbacks return `{"error": "..."}`. Always check the
endpoint documentation rather than assuming every error has `detail`.

### Status codes used

| Code | Meaning |
|---|---|
| `200 OK` | Successful read/update action. |
| `201 Created` | Resource created, or a follow/request action created a record. |
| `204 No Content` | Successful deletion with no body. |
| `205 Reset Content` | Logout completed; no body. |
| `400 Bad Request` | Validation failure, duplicate action, invalid state, or malformed input. |
| `401 Unauthorized` | Missing/invalid authentication on a protected endpoint. |
| `403 Forbidden` | Authenticated but not allowed (unverified, wrong role, not owner, or closed resource). |
| `404 Not Found` | Unknown resource or out-of-range page. |
| `405 Method Not Allowed` | Method not supported by the route. |
| `429 Too Many Requests` | Throttle or cooldown active. |
| `500 Internal Server Error` | Unhandled exception. |
| `503 Service Unavailable` | Health check cannot reach PostgreSQL. |

DRF may return `401` rather than `403` for an `IsAuthenticated` failure when no
credentials are supplied. `IsEmailVerified` returns `403` for a signed-in but
unverified user.

## File uploads

Endpoints accepting files use multipart form data:

| Content | Endpoint | Constraints |
|---|---|---|
| Speaker avatar | `POST /api/speakers/`, `PATCH /api/speakers/me/` or speaker detail | JPG/JPEG/PNG/WebP, max 5 MB. |
| Organization branding | `POST/PUT /api/organization/` | JPG/JPEG/PNG/WebP, max 5 MB. |
| Event image | Event create/update | JPG/JPEG/PNG/WebP, max 5 MB. |
| Talk presentation | Talk create/update | PDF/PPT/PPTX/JPG/JPEG/PNG/WebP, max 20 MB. |
| Blog image | Blog create/update | JPG/JPEG/PNG/WebP, max 5 MB. |

Django limits non-file request data to 10 MB (`DATA_UPLOAD_MAX_MEMORY_SIZE`) and
spills file parts larger than 10 MB (`FILE_UPLOAD_MAX_MEMORY_SIZE`) to temporary
storage rather than rejecting them. A 20 MB presentation can therefore pass
Django's file validators, but the reverse proxy or hosting platform may impose a
smaller body limit. Send files as multipart file parts; with `curl`, use `-F`
rather than embedding base64 JSON.

## Health check

`GET /health/` is public and not versioned:

```json
{"status": "ok", "database": "ok"}
```

If PostgreSQL cannot be reached:

```json
{"status": "ok", "database": "unavailable"}
```

with HTTP `503`. The `status` field indicates that the process is alive; the
`database` field indicates readiness.

## API behaviour notes

- **Lists can be scoped unexpectedly.** `GET /api/talks/` returns only the
  authenticated user's talks; anonymous callers get an empty page. Public talk
  discovery uses the slug-based endpoints.
- **Event detail is visibility-aware.** Active events are public; inactive
  events are visible only to their submitter or a superuser.
- **No refresh endpoint exists.** Access tokens expire after 60 minutes and
  cannot be renewed through the API.
- **No global search endpoint.** Use the per-resource filters above.
- **No bulk operations.** Mutations apply to one resource at a time unless an
  endpoint explicitly says otherwise.
- **No JSON:API or envelope wrapper** for single resources. A detail response is
  the serialized object itself.
