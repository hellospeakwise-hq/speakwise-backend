# Endpoint Reference

This page documents every routed domain endpoint. All paths are relative to the
server root. The API base path is `/api/`; the health check is `/health/`.

- Authentication details: [Authentication](authentication.md)
- Access-control details and known gaps: [Permissions](permissions.md)
- Cross-cutting conventions: [API overview](overview.md)

The documentation describes **routed** endpoints only. Views without a URL
pattern (for example `PublicEventListView` and `MyEventsListView`) are not part of
the API.

## Endpoint index

| Group | Count | Paths |
|---|---:|---|
| Health | 1 | `/health/` |
| Authentication and users | 14 | `/api/users/...` |
| Speaker profiles and activity | 13 | `/api/speakers/...`, `/api/notifications/...` |
| Organizations | 2 | `/api/organization/...` |
| Events and CFP Market | 5 | `/api/events/...` |
| Talks and reviews | 5 | `/api/talks/...`, `/api/speakers/<slug>/talks/` |
| Feedback | 3 | `/api/feedbacks/...` |
| Speaker requests | 6 | `/api/speaker-requests/...` |
| Blogs | 2 | `/api/blogs/...` |
| Teams | 1 | `/api/teams/` |

## Common response shapes

### User and auth payload

`UserSerializer` fields:

```json
{
  "id": "e4b5d7d5-3c1a-4f4e-9f0f-6f7a8b9c0d1e",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "nationality": "British",
  "username": "ada",
  "is_email_verified": true
}
```

`password` is write-only and never returned. `id` and `is_email_verified` are
read-only.

Auth responses add `refresh`, `access`, and (on login/OAuth exchange) `profile`.

### Pagination

All paginated lists use:

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

Default page size 20, maximum 100. See [API overview](overview.md#pagination).

### Speaker profile (list shape)

```json
{
  "id": "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
  "user_account": "e4b5d7d5-3c1a-4f4e-9f0f-6f7a8b9c0d1e",
  "events_spoken": [],
  "organization": "Analytical Engines Ltd",
  "short_bio": "Mathematician and computing pioneer.",
  "long_bio": null,
  "country": "United Kingdom",
  "avatar": null,
  "slug": "ada-lovelace",
  "social_links": [],
  "skill_tags": [],
  "speaker_name": "Ada Lovelace",
  "username": "ada",
  "experiences": [],
  "followers_count": 0,
  "following_count": 0,
  "is_following": false
}
```

The detail serializer adds `feedback_summary` and omits nothing else of note. It
is returned only by `GET /api/speakers/<slug>/`.

### Event shape

See [Events](#events) for the full field description. A response always includes
`date`, `date_range`, and `is_cfp_currently_open` in addition to the model fields.

## Health

### GET /health/

Public liveness/readiness probe.

**Auth:** public  
**Response `200 OK`:**

```json
{"status": "ok", "database": "ok"}
```

**Response `503 Service Unavailable`:**

```json
{"status": "ok", "database": "unavailable"}
```

The endpoint is outside `/api/` and is not versioned or paginated.

## Authentication and users

Full flow details are in [Authentication](authentication.md).

### POST /api/users/auth/register/

**URL name:** `users:register`  
**Auth:** public  
**Throttle:** `register` — 5/hour  
**Turnstile:** required when `TURNSTILE_SECRET_KEY` is configured.

**Request:**

```json
{
  "email": "ada@example.com",
  "username": "ada",
  "password": "correct-horse-battery-staple",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "nationality": "British",
  "turnstile_token": "<optional-token>"
}
```

`turnstile_token` is not part of `UserSerializer`; it is read directly by the
view and is ignored when Turnstile is not configured.

**Response `201 Created`:** auth payload with `is_email_verified: false`.

**Status codes:** `201`; `400` for validation, duplicate email/username, weak
password, or failed bot check; `429` for throttle.

### POST /api/users/auth/verify-otp/

**URL name:** `users:verify-otp`  
**Auth:** public  
**Throttle:** `otp_verify` — 10/minute

**Request:**

```json
{"email": "ada@example.com", "otp": "123456"}
```

**Response `200 OK`:**

```json
{"detail": "Email verified successfully."}
```

**Status codes:** `200`; `400` for unknown email, expired/used/incorrect code, or
attempt limit; `429` for throttle.

### POST /api/users/auth/resend-otp/

**URL name:** `users:resend-otp`  
**Auth:** public  
**Throttle:** `otp_resend` — 5/minute

**Request:**

```json
{"email": "ada@example.com"}
```

**Response `200 OK`:** always generic:

```json
{"detail": "A new verification code has been sent."}
```

No email is sent when the account is unknown, already verified, or still inside
the two-minute cooldown. The endpoint still returns `200` to avoid account
enumeration. `429` is returned when the throttle is exceeded.

### POST /api/users/auth/login/

**URL name:** `users:login`  
**Auth:** public  
**Throttle:** `login` — 10/minute  
**Lockout:** 3 failures within 5 minutes for the same email.

**Request:**

```json
{"email": "ada@example.com", "password": "correct-horse-battery-staple"}
```

**Response `200 OK`:** auth payload plus `profile`:

```json
{
  "id": "e4b5d7d5-3c1a-4f4e-9f0f-6f7a8b9c0d1e",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "nationality": "British",
  "username": "ada",
  "is_email_verified": true,
  "refresh": "<refresh-token>",
  "access": "<access-token>",
  "profile": {
    "speaker_profile": {
      "id": "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
      "slug": "ada-lovelace",
      "speaker_name": "Ada Lovelace",
      "username": "ada"
    }
  }
}
```

The example is abridged; the profile object uses the full profile serializers.
`profile` is `{}` when the user has no profile, or contains
`organization_profile` instead of `speaker_profile`.

**Status codes:** `200`; `400` for invalid credentials, unverified email, or
lockout; `429` for throttle.

### POST /api/users/auth/logout/

**URL name:** `users:logout`  
**Auth:** required  
**Request:** `{"refresh": "<refresh-token>"}`  
**Response `205 Reset Content`:** empty body.  
**Errors:** `400` invalid/blacklisted refresh token; `401` unauthenticated.

### POST /api/users/auth/oauth/token/

**URL name:** `users:oauth-token-exchange`  
**Auth:** public  
**Throttle:** `oauth_token` — 10/minute

**Request:** `{"code": "<one-time-code>"}`  
**Response `200 OK`:** auth payload with `profile`, same shape as login.

The code is single-use and expires after 120 seconds. Invalid, used, or expired
codes return `400`.

### GET /api/users/auth/github-login/ and /google-login/

**URL names:** `users:github-login`, `users:google-login`  
**Auth:** public

Return `302` to the provider. The OAuth `state` is stored in the Django session.

### GET /api/users/auth/github-callback/ and /google-callback/

**URL names:** `users:github-callback`, `users:google-callback`  
**Auth:** public

On success, return `302` to:

```text
{FRONTEND_URL}/auth/callback?code=<one-time-code>
```

On failure, return `400 Bad Request` with `{"error": "..."}` (for example an
invalid state or provider error).

### POST /api/users/auth/password-reset/

**URL name:** `users:password_reset_request`  
**Auth:** public  
**Throttle:** `password_reset` — 3/hour

**Request:** `{"email": "ada@example.com"}`  
**Response `200 OK`:** `{"detail": "Password reset email sent successfully."}`

The response is identical for unknown emails; no email is sent in that case.

### POST /api/users/auth/password-reset/confirm

**URL name:** `users:password_reset_confirm`  
**Auth:** public  
**Note:** no trailing slash.

**Request:**

```json
{
  "email": "ada@example.com",
  "token": "<token-from-email>",
  "new_password": "a-new-strong-password"
}
```

**Response `200 OK`:** `{"detail": "Password reset successfully."}`  
**Errors:** `400` for unknown email, invalid/expired token, or weak password.

### GET/PATCH /api/users/me/

**URL name:** `users:retrieve_update_authenticated_user`

| Method | Auth | Notes |
|---|---|---|
| `GET` | Authenticated | Returns own `UserSerializer` data. |
| `PATCH` | Verified | Partial update. Changing `email` sets `is_email_verified=false` and issues a new OTP. |

**Request example (`PATCH`):**

```json
{"first_name": "Augusta", "nationality": "British"}
```

**Response `200 OK`:** user object. `PATCH` does not return tokens.

Changing the email address also invalidates the current verification state; the
new address must be verified with the OTP sent by the service.

### GET /api/users/

**URL name:** `users:user-list`  
**Auth:** staff (`is_staff`) only  
**Query params:** `email`, `username` (case-insensitive contains)

**Response `200 OK`:** paginated `UserSerializer` objects. Supports `page` and
`page_size`. `401` without credentials; `403` for non-staff.

## Speaker profiles and activity

### GET/POST /api/speakers/

**URL name:** `speakers:speakers_list_create`

| Method | Auth | Behaviour |
|---|---|---|
| `GET` | Public | Paginated list of all speaker profiles. |
| `POST` | Verified | Create the requesting user's speaker profile. |

**POST request fields:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `organization` | string | No | Free-text organization name. |
| `short_bio` | string | No | Max 255. |
| `long_bio` | string | No | May be null. |
| `country` | string | No | Free text. |
| `avatar` | file | No | Image constraints. |
| `events_spoken` | UUID[] | No | Event IDs. |
| `social_links` | object[] | No | `{name, link}` entries. |
| `skill_tags` | object[] | No | `{name, description, duration}` entries. |

`user_account` and `slug` are read-only and generated by the server. The
one-profile rule is enforced: a user with a speaker or organization profile
receives `400`.

**Response `201 Created`:** speaker profile list shape. `400` for duplicate
profile, invalid nested data, or unsupported file; `401`/`403` for auth issues.

### GET/PATCH /api/speakers/me/

**URL name:** `speakers:speakers_me`

| Method | Auth | Behaviour |
|---|---|---|
| `GET` | Authenticated | Return own profile or `404`. |
| `PATCH` | Verified | Partial update of own profile. |

**Response `200 OK`:** speaker profile list shape. PATCH can update nested
`social_links`; links are synced by `name` (submitted links are created/updated,
omitted links are removed). Skill tags are handled as nested writable data by
`WritableNestedModelSerializer`. The response for `PATCH` uses the list
serializer, so it does not include `feedback_summary`.

**Errors:** `404` if the user has no speaker profile; `401` unauthenticated;
`403` unverified.

### GET/PATCH/DELETE /api/speakers/<slug>/

**URL name:** `speakers:speakers_retrieve_update_delete`  
**Lookup:** slug or UUID.

| Method | Auth | Behaviour |
|---|---|---|
| `GET` | Public | Public detail with `feedback_summary`. |
| `PATCH` | Verified + owner | Update own profile. |
| `DELETE` | Verified + owner | Delete own profile; returns `204`. |

**Response `200 OK` (detail):** detail shape with `feedback_summary`:

```json
{
  "id": "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
  "slug": "ada-lovelace",
  "speaker_name": "Ada Lovelace",
  "username": "ada",
  "feedback_summary": {
    "total_count": 3,
    "overall_rating": {
      "average": 9.0,
      "distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 1, "9": 1, "10": 1}
    }
  }
}
```

The example is abridged; all rating criteria use the same `average` and
`distribution` shape. With no feedback, `total_count` is `0`, every
distribution is all zeros, and every `average` is `null`.

**Errors:** `404` unknown; `403` authenticated non-owner; `401` unauthenticated
mutation; `400` invalid data.

### GET/POST /api/speakers/experiences/

**URL name:** `speakers:speakers_experiences_list_create`  
**Auth:** authenticated

`GET` lists the requester's experiences, newest first, paginated. `POST` creates
an experience for the requester's speaker profile.

**POST request:**

```json
{
  "event_name": "PyCon UK",
  "event_date": "2026-09-18",
  "topic": "Analytical engines today",
  "description": "A retrospective.",
  "presentation_link": "https://example.com/slides",
  "video_recording_link": null,
  "event": "8a7b6c5d-4e3f-4a2b-9c1d-0e1f2a3b4c5d",
  "feedback_enabled": true
}
```

`event` is an optional platform event UUID. `speaker` is writable in the
serializer but overwritten with the requester's profile. `feedback_slug` is
read-only and generated. `feedback_enabled` defaults to `true`.

**Response `201 Created`:**

```json
{
  "id": "6c5d4e3f-2a1b-4c9d-8e7f-0a1b2c3d4e5f",
  "event_name": "PyCon UK",
  "event_date": "2026-09-18",
  "topic": "Analytical engines today",
  "description": "A retrospective.",
  "presentation_link": "https://example.com/slides",
  "video_recording_link": null,
  "speaker": "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
  "event": "8a7b6c5d-4e3f-4a2b-9c1d-0e1f2a3b4c5d",
  "feedback_slug": "aB3dEf",
  "feedback_enabled": true
}
```

**Errors:** `400` missing date, no speaker profile, or invalid event; `401`.

### GET/PATCH/DELETE /api/speakers/experiences/<uuid:pk>/

**URL name:** `speakers:speakers_experiences_retrieve_update_delete`

| Method | Declared permission | Actual access |
|---|---|---|
| `GET` | `IsAuthenticatedOrReadOnly` | In practice authenticated; anonymous lookup filters by `AnonymousUser` and raises an unhandled `ValidationError` (`500`). |
| `PATCH` | Authenticated | Owner only (queryset scoped to `request.user`). |
| `DELETE` | Authenticated | Owner only; returns `204`. |

**Response `200 OK`:** experience object. **Errors:** anonymous `GET` returns
`500` as described above; `401` unauthenticated `PATCH`/`DELETE`; `404` unknown
or foreign; `400` invalid update. `PATCH` accepts the writable `speaker` field,
so an owner can transfer an experience to another speaker profile; this is not
restricted by the view.

### GET/POST /api/speakers/skills/

**URL name:** `speakers:skills_list`  
**Auth:** authenticated

`GET` lists the requester's skill tags, paginated. `POST` creates one for the
requester's speaker profile.

**POST request:**

```json
{"name": "Django", "description": "Web framework", "duration": 8}
```

`name`, `description`, and `duration` are all optional at the serializer level;
`name` is nullable. An empty `POST {}` is valid and creates a tag with
`name: null`, so validate required fields in the client if your product needs
them. `speaker` is not accepted in the body.

**Response `201 Created`:**

```json
{
  "id": "f1e2d3c4-b5a6-4978-8a9b-0c1d2e3f4a5b",
  "name": "Django",
  "description": "Web framework",
  "duration": 8
}
```

**Errors:** `400` invalid field values or no speaker profile; `401`. A missing
`name` is not an error at this layer.

### GET/PATCH/DELETE /api/speakers/skills/<uuid:pk>/

**URL name:** `speakers:skills_detail`  
**Auth:** authenticated; owner only.

`GET` returns the skill; `PATCH` partially updates it; `DELETE` returns `204`.
Unknown or foreign IDs return `404`.

### GET /api/speakers/<slug>/experiences/

**URL name:** `speakers:public_speaker_experiences`  
**Auth:** public  
**Lookup:** speaker slug or UUID.

Returns paginated public experiences for the speaker. An unknown speaker returns
an empty page, not a `404`. Each item has the experience shape above.

### GET/POST/DELETE /api/speakers/<slug>/follow/

**URL name:** `speakers:speaker_follow`  
**Auth:** authenticated  
**Lookup:** slug only.

| Method | Response | Notes |
|---|---|---|
| `GET` | `200` | `{"is_following": false, "followers_count": 12, "following_count": 4}` |
| `POST` | `201` | Follow; returns `detail`, `followers_count`, and `following_count`. |
| `DELETE` | `200` | Unfollow; returns the same summary shape. |

`POST` when already following or when following yourself returns `400`.
`DELETE` when not following returns `400`. Unknown speaker slug returns `404`.

### GET /api/speakers/<slug>/followers/

**URL name:** `speakers:speaker_followers_list`  
**Auth:** public  
**Pagination:** none; `followers` is capped at 100.

```json
{
  "followers_count": 128,
  "followers": [
    {
      "id": "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d",
      "username": "grace",
      "full_name": "Grace Hopper",
      "avatar": null,
      "slug": "grace-hopper",
      "short_bio": "Compiler pioneer.",
      "country": "United States",
      "organization": "US Navy",
      "created_at": "2026-10-01T10:00:00Z"
    }
  ]
}
```

Followers without a speaker profile have `slug: null` and empty profile fields.

### GET /api/speakers/<slug>/following/

**URL name:** `speakers:speaker_following_list`  
**Auth:** public  
**Pagination:** none; capped at 100.

```json
{"following_count": 12, "following": []}
```

Each entry uses the same follower detail shape and refers to a speaker the
profile follows.

### GET /api/notifications/

**URL name:** `speakers:notification_list`  
**Auth:** authenticated  
**Query params:** `is_read`  
**Pagination:** yes, 20/page.

Only the literal `true` (case-insensitive) selects read notifications; any other
supplied value selects unread notifications.

```json
{
  "id": "5d4c3b2a-1f0e-4d9c-8b7a-6f5e4d3c2b1a",
  "user": "e4b5d7d5-3c1a-4f4e-9f0f-6f7a8b9c0d1e",
  "message": "Ada Lovelace added a new speaking experience.",
  "link": "/speakers/ada-lovelace",
  "is_read": false,
  "created_at": "2026-10-20T14:30:00Z"
}
```

### PATCH /api/notifications/<uuid:pk>/read/

**URL name:** `speakers:notification_mark_read`  
**Auth:** authenticated; own notification only.

No request body. Returns the updated notification with `is_read: true`. Unknown
or foreign notification returns a custom `404`
`{"detail": "Notification not found."}`.

## Organizations

### GET/POST /api/organization/

**URL name:** `organizations:organization-list-create`

| Method | Auth | Behaviour |
|---|---|---|
| `GET` | Public | Paginated list, newest first. |
| `POST` | Verified | Create the requester's organization profile. |

**POST request fields:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | Unique. |
| `description` | string | No | May be null. |
| `website` | URL | No | May be null. |
| `branding` | file | No | Image constraints. |
| `contact_email` | email | No | May be null. |

`owner`, `status`, `admin_notes`, `id`, and `cfps` are read-only. New
organizations start in `pending` status. The one-profile rule applies.

**Response `201 Created`:**

```json
{
  "id": "9f8e7d6c-5b4a-4938-8271-6a5b4c3d2e1f",
  "owner": "e4b5d7d5-3c1a-4f4e-9f0f-6f7a8b9c0d1e",
  "name": "Analytical Engines Ltd",
  "description": "A computing consultancy.",
  "website": "https://example.com",
  "branding": null,
  "contact_email": "hello@example.com",
  "status": "pending",
  "admin_notes": null,
  "cfps": null
}
```

`cfps` is a single nested object (or `null`), not a list:

```json
{
  "cfps": {
    "url": "https://example.com/cfp",
    "description": "Our 2027 CFP.",
    "open_at": "2026-10-01T00:00:00Z",
    "close_at": "2027-01-31T23:59:59Z"
  }
}
```

**Errors:** `400` duplicate name, existing profile, invalid file; `401`/`403`.

### GET/PUT/DELETE /api/organization/<uuid:pk>/

**URL name:** `organizations:organization-detail`

| Method | Auth | Behaviour |
|---|---|---|
| `GET` | Public | Retrieve. |
| `PUT` | Verified | Full update. **No owner check.** |
| `DELETE` | Verified | Delete and return `204`. **No owner check.** |

`PATCH` is not implemented and returns `405`.

**PUT request:** same writable fields as create (`name`, `description`,
`website`, `branding`, `contact_email`). All fields required by the serializer
must be present for a full update; `name` is the important one.

**Errors:** `404` unknown; `400` invalid data/duplicate name; `401`/`403`;
`403` for unverified users.

> **Security gap:** any verified user can update or delete any organization.
> Do not build a client that treats this endpoint as owner-protected. The public
> response also exposes `owner` and `admin_notes`; see
> [Permissions](permissions.md#current-access-control-gaps).

## Events

### GET /api/events/

**URL name:** `events:event-list-create`  
**Auth:** public for GET  
**Pagination:** yes  
**Filters:** `title`, `event_nickname`, `country`, `location`, `slug`,
`submitted_by`, `is_active`, `is_free`, `cfp_open`, `cfp_open_date`,
`cfp_deadline`, `start_date_time`, `end_date_time`.

Only active events are listed. Because the base queryset is already
`is_active=True`, `?is_active=false` returns no results.

**Response `200 OK`:** paginated event objects.

Event object:

```json
{
  "id": "8a7b6c5d-4e3f-4a2b-9c1d-0e1f2a3b4c5d",
  "title": "PyCon UK 2026",
  "event_nickname": "PyCon UK",
  "event_image": null,
  "description": "The UK Python conference.",
  "website": "https://pyconuk.example",
  "submitted_by": "e4b5d7d5-3c1a-4f4e-9f0f-6f7a8b9c0d1e",
  "start_date_time": "2026-09-18T09:00:00Z",
  "end_date_time": "2026-09-20T17:00:00Z",
  "is_active": true,
  "slug": "pycon-uk-2026",
  "location": "Manchester",
  "country": "United Kingdom",
  "is_free": false,
  "cfp_open": true,
  "cfp_link": "https://pyconuk.example/cfp",
  "cfp_open_date": "2026-01-01T00:00:00Z",
  "cfp_deadline": "2026-05-31T23:59:59Z",
  "cfp_speaker_notification_date": "2026-06-30",
  "date": "2026-09-18 to 2026-09-20",
  "date_range": {
    "start": "2026-09-18T09:00:00+00:00",
    "end": "2026-09-20T17:00:00+00:00"
  },
  "is_cfp_currently_open": true
}
```

### POST /api/events/

**URL name:** `events:event-list-create`  
**Auth:** authenticated  
**Pagination:** n/a

Regular users submit an event for approval. Superusers may create an active
event directly.

**Request (regular user, `EventSubmitSerializer`):**

```json
{
  "title": "PyCon UK 2026",
  "event_nickname": "PyCon UK",
  "description": "The UK Python conference.",
  "website": "https://pyconuk.example",
  "cfp_open": true,
  "cfp_open_date": "2026-01-01T00:00:00Z",
  "cfp_deadline": "2026-05-31T23:59:59Z",
  "cfp_speaker_notification_date": "2026-06-30",
  "cfp_link": "https://pyconuk.example/cfp",
  "location": "Manchester",
  "country": "United Kingdom",
  "is_free": false,
  "start_date_time": "2026-09-18T09:00:00Z",
  "end_date_time": "2026-09-20T17:00:00Z"
}
```

`is_free` is required on create (`true` or `false`). `title` and `website` are
required. The server sets `submitted_by` and forces `is_active=false` for
non-superusers. An attempt to send `is_active` is ignored by the submit
serializer.

Superusers may use the full `EventSerializer`, including `is_active`.

**Response `201 Created`:** full event object. The returned object is the
serializer shape, including server-calculated fields and `is_active` (false for
regular submissions).

**Errors:** `400` duplicate title/website, missing `is_free`, validation failure,
or invalid image; `401` unauthenticated; `429` when the authenticated default
throttle (1000/hour) is exceeded. `Event.title` is globally unique, so a repeated
title can fail even when the website differs; the service also checks the
normalized title+website pair.

### GET /api/events/me/

**URL name:** `events:events-me`  
**Auth:** authenticated  
**Pagination:** yes

Returns events where `submitted_by=request.user`, active or pending, newest
first.

### GET /api/events/cfp-market/

**URL name:** `events:cfp-market`  
**Auth:** public  
**Pagination:** yes

Returns active events whose `cfp_open` is true and whose optional open/deadline
window contains the current time.

```json
{
  "id": "8a7b6c5d-4e3f-4a2b-9c1d-0e1f2a3b4c5d",
  "slug": "pycon-uk-2026",
  "title": "PyCon UK 2026",
  "name": "PyCon UK 2026",
  "event_image": null,
  "cfp_open": true,
  "cfp_link": "https://pyconuk.example/cfp",
  "cfp_deadline": "2026-05-31T23:59:59Z",
  "cfp_open_date": "2026-01-01T00:00:00Z",
  "is_cfp_currently_open": true
}
```

### GET/PATCH/DELETE /api/events/private/<slug>/

**URL name:** `events:event-private-detail`  
**Auth:** authenticated + submitter or superuser.

| Method | Behaviour |
|---|---|
| `GET` | Retrieve a pending or active managed event. |
| `PATCH` | Partial update. Non-superusers cannot set `is_active`. |
| `DELETE` | Delete; returns `204`. |

**PATCH example:** any writable event field. `is_active` is removed for
non-superusers before validation. `submitted_by` and `slug` are current
serializer fields and are not protected; see the permissions gaps.

**Errors:** `401`; `403` non-owner; `404` unknown.

### GET/PATCH/DELETE /api/events/<slug>/

**URL name:** `events:event-detail`  
**Auth:** GET public with visibility rules; mutations authenticated + submitter
or superuser.

GET visibility:

- Anonymous: only `is_active=True`.
- Authenticated non-superuser: active events, plus their own inactive events.
- Superuser: any event.

PATCH/DELETE behave like the private detail route. `PATCH` returns the full event
object; `DELETE` returns `204`.

Because `Event.slug` is not unique, duplicate slugs make these lookups ambiguous.
`get_object_or_404` then raises `MultipleObjectsReturned`, which surfaces as
`500` rather than a clean `404`.

**Errors:** `404` for unknown/invisible events; `403` non-owner mutation; `500`
if the slug matches more than one event.

## Talks and reviews

### GET/POST /api/talks/

**URL name:** `talks:talk-list`  
**Auth:** `IsAuthenticatedOrReadOnly`  
**Pagination:** yes (generic view default)  
**Filters:** `title` (contains), `category` (contains), `speaker` (exact username).

**Important:** authenticated `GET` returns only the requester's talks; anonymous
`GET` returns an empty paginated page because the queryset is `none()`. This is
not a public catalog despite the path. Use the slug-based public endpoints for
discovery.

Talk object:

```json
{
  "id": "2d3e4f5a-6b7c-4d8e-9f0a-1b2c3d4e5f6a",
  "title": "Analytical engines today",
  "description": "A tour of Victorian computing.",
  "speaker": "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
  "duration": 45,
  "category": "software architecture",
  "presentation_files": null,
  "event": "8a7b6c5d-4e3f-4a2b-9c1d-0e1f2a3b4c5d",
  "speaker_name": "Ada Lovelace",
  "slug": "analytical-engines-today-abc123def456",
  "is_public": true,
  "is_reviewable": true
}
```

`speaker`, `slug`, and `speaker_name` are read-only on write. `event` is
optional and nullable. `presentation_files` is a file field.

> **Unsupported session field:** `TalkSerializer` declares a nested writable
> `session` field, but `Talks` has no `session` attribute. It is skipped on read,
> so responses omit it. Do not send it on create: there is no talk-session API,
> and the create path does not support the field. `TalkSession` exists only in
> Django admin/database.

**POST request:**

```json
{
  "title": "Analytical engines today",
  "description": "A tour of Victorian computing.",
  "duration": 45,
  "category": "software architecture",
  "is_public": true,
  "is_reviewable": true,
  "event": "8a7b6c5d-4e3f-4a2b-9c1d-0e1f2a3b4c5d"
}
```

`category` must be one of the values in `talks.choices.TalkCategoryChoices` (for
example `"backend"`, `"frontend"`, `"ai and ml"`, `"software architecture"`).
The speaker is inferred from the authenticated user; no speaker profile returns
`400` `{"speaker": "No speaker profile found for this user."}`.

**Response `201 Created`:** talk object. **Errors:** `400` invalid/missing fields
or no speaker profile; `401`; file validation errors.

### GET/PATCH/DELETE /api/talks/<uuid:pk>/

**URL name:** `talks:talk-detail`

| Method | Access |
|---|---|
| `GET` | Public; any talk, including non-public. |
| `PATCH` | Authenticated owner only. |
| `DELETE` | Authenticated owner only; `204`. |

Non-owner mutations return `404` because the queryset is filtered to the
requester's talks. **Errors:** `404` unknown/foreign; `400` invalid data.

### GET/POST /api/talks/<slug>/reviews/

**URL name:** `talks:talk-review-submit`  
**Auth:** public  
**Pagination:** yes for GET

`GET` returns reviews for a public talk, newest first:

```json
{
  "id": "3c4d5e6f-7a8b-4c9d-0e1f-2a3b4c5d6e7f",
  "talk": "2d3e4f5a-6b7c-4d8e-9f0a-1b2c3d4e5f6a",
  "rating": 5,
  "comment": "Excellent walkthrough."
}
```

`POST` creates a review. The talk is resolved from the URL, so the `talk` body
field is ignored/overwritten.

**POST request:**

```json
{"rating": 5, "comment": "Excellent walkthrough."}
```

**Response `201 Created`:** review object. **Errors:** `400` if the talk does not
exist; `403` if `is_reviewable=false`; `429` for anonymous throttle (100/hour).
The creation check does not require `is_public=true`; a non-public talk with a
known slug can still be reviewed if `is_reviewable` is true.

### GET /api/talks/<slug>/

**URL name:** `talks:talk-public-detail`  
**Auth:** public

Returns a talk only if `is_public=true`, otherwise `404`. Same talk shape as
above.

### GET /api/speakers/<slug>/talks/

**URL name:** `talks:speaker-public-talks`  
**Auth:** public  
**Pagination:** yes

Returns public talks for the given speaker slug. An unknown speaker returns an
empty page.

## Feedback

Feedback is submitted against the opaque `feedback_slug` on a speaker
experience. The raw IP is never stored; a salted hash is used for the cooldown.

### GET /api/feedbacks/

**URL name:** `feedbacks:feedback_list`  
**Auth:** authenticated  
**Pagination:** yes  
**Query param:** `experience` (feedback slug, optional)

Returns feedback for the requester's own speaker profile, newest first. A user
without a speaker profile gets an empty page. An unknown `experience` slug
returns `404`.

```json
{
  "id": "4d5e6f7a-8b9c-4d0e-9f1a-2b3c4d5e6f7a",
  "experience": {
    "feedback_slug": "aB3dEf",
    "event_name": "PyCon UK",
    "event_date": "2026-09-18",
    "topic": "Analytical engines today"
  },
  "speaker": "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
  "name": "Grace",
  "is_anonymous": false,
  "overall_rating": 9,
  "engagement": 8,
  "clarity": 9,
  "content_depth": 10,
  "speaker_knowledge": 10,
  "practical_relevance": 8,
  "comments": "Wonderful.",
  "created_at": "2026-09-18T16:00:00Z"
}
```

### GET /api/feedbacks/rate/<feedback_slug>/

**URL name:** `feedbacks:feedback_rate`  
**Auth:** public

Public presentation context; exposes no internal IDs.

```json
{
  "topic": "Analytical engines today",
  "event_name": "PyCon UK",
  "event_date": "2026-09-18",
  "speaker_name": "Ada Lovelace",
  "feedback_enabled": true,
  "is_open": true
}
```

`is_open` reflects the date gate. Unknown slug returns `404`.

### POST /api/feedbacks/rate/<feedback_slug>/

**URL name:** `feedbacks:feedback_rate`  
**Auth:** public  
**Body:**

```json
{
  "name": "Grace",
  "comments": "Wonderful.",
  "overall_rating": 9,
  "engagement": 8,
  "clarity": 9,
  "content_depth": 10,
  "speaker_knowledge": 10,
  "practical_relevance": 8
}
```

All six ratings are required integers from 1 to 10. `name` and `comments` are
optional. Submitting an empty name makes the feedback anonymous (derived on
save). The experience and speaker are resolved from the slug.

**Response `201 Created`:**

```json
{
  "experience": {
    "feedback_slug": "aB3dEf",
    "event_name": "PyCon UK",
    "event_date": "2026-09-18",
    "topic": "Analytical engines today"
  },
  "name": "Grace",
  "is_anonymous": false,
  "overall_rating": 9,
  "engagement": 8,
  "clarity": 9,
  "content_depth": 10,
  "speaker_knowledge": 10,
  "practical_relevance": 8,
  "comments": "Wonderful.",
  "created_at": "2026-09-18T16:05:00Z"
}
```

**Status codes:**

| Status | Condition |
|---|---|
| `201` | Created. |
| `400` | Missing/invalid rating or other field validation. |
| `403` | Feedback has not opened yet or `feedback_enabled=false`. |
| `404` | Unknown feedback slug. |
| `429` | Same IP hash already submitted for this experience within the cooldown (60 minutes by default). |

The date gate opens at the linked event's `start_date_time` when present;
otherwise on `event_date`. The cooldown uses `FEEDBACK_IP_COOLDOWN_MINUTES`.

### GET /api/feedbacks/qrcode/<feedback_slug>/

**URL name:** `feedbacks:feedback_qrcode`  
**Auth:** verified + owner

Returns a `200 image/png` QR code encoding
`{FRONTEND_URL}/feedback/<feedback_slug>`. There is no JSON body.

**Errors:** `401` unauthenticated; `403` unverified or not the owning speaker;
`404` unknown slug.

## Speaker requests

A `SpeakerRequest` is a structured invitation to a speaker profile. A
`SpeakerEmailRequests` row is a lightweight email-only request between users.

Request status values: `pending`, `accepted`, `declined`, `is_expired`,
`cancelled`.

Proposed session types: `online`, `in_person`.

### GET/POST /api/speaker-requests/

**URL name:** `speakerrequests:speaker_requests_list_create`  
**Auth:** authenticated  
**Pagination:** yes

**Current behaviour:** `GET` returns **all** speaker requests in the database,
not just the requester's. The view accepts a `user` argument but does not use it.
Any authenticated user can enumerate invitations, including `notes` and fees.

**POST** creates a request. Any authenticated user can create one; there is no
organizer role or organization check.

**POST request:**

```json
{
  "speaker": "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d",
  "event": "8a7b6c5d-4e3f-4a2b-9c1d-0e1f2a3b4c5d",
  "message": "Would you speak at PyCon UK?",
  "proposed_topic": "Analytical engines today",
  "proposed_duration": 45,
  "proposed_session_type": "in_person",
  "response_deadline": "2026-05-01T23:59:59Z",
  "accommodation_covered": true,
  "travel_covered": true,
  "speaker_fee": "500.00",
  "notes": "Internal note",
  "requested_by": "9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d"
}
```

`speaker` and `requested_by` are `SpeakerProfile` UUIDs. `event` is an Event
UUID. `message` is required. `requested_by` and the remaining fields are
optional; `speaker` is optional at the serializer/model level, but omitting it
causes a `500` after save because the view dereferences `req.speaker`. Always
send `speaker`. A duplicate speaker+event pair is rejected with `400`.

**Response `201 Created`:** created request and an enqueued notification email
to the speaker. The email currently uses the placeholder organization name
`SpeakWise` and organizer name `Admin`.

**Status codes:** `201`; `400` duplicate or validation; `401`; `404` not used
for create.

### GET/PATCH/DELETE /api/speaker-requests/<uuid:pk>/

**URL name:** `speakerrequests:speaker_request_retrieve_update_delete`  
**Auth:** authenticated **and superuser**.

Superuser-only management of any request. `GET` and `PATCH` return the request;
`DELETE` returns `204`. `PATCH` is partial. Non-superusers receive `403`;
unknown IDs return `404`.

### GET /api/speaker-requests/incoming/

**URL name:** `speakerrequests:speaker_requests_list`  
**Auth:** authenticated; target speaker only  
**Pagination:** yes  
**Filters:** `status`, `event`

Returns requests where `speaker.user_account=request.user`. The `event` filter
is declared as a `NumberFilter` against a UUID field, so it may not behave as
expected; filter client-side if needed.

**Errors:** `401`; empty page for a user without a speaker profile.

### PATCH /api/speaker-requests/<uuid:pk>/respond/

**URL name:** `speakerrequests:speaker_request_respond`  
**Auth:** authenticated; target speaker only.

Only requests in `pending` status can be answered; otherwise `400`.

**Request:**

```json
{"status": "accepted", "response_message": "Happy to join."}
```

`status` should be `accepted` or `declined` for the normal workflow. The
serializer accepts other status values, so the API does not strictly validate
the transition.

**Response `200 OK`:** updated request. When the request's event location is
empty, accept/decline queues an email to the organizer (hard-coded to
`admin@speakwise.live` with requester name `Admin`).

> **Known failure:** after saving, the view reads `req.event.location.venue`.
> `Event.location` is a `CharField`; when it is non-empty this raises
> `AttributeError` and returns `500` before the email is enqueued. When it is
> empty, `event_location` is `""` and the email is queued. The status change is
> saved before this failure.

**Errors:** `400` non-pending; `401`; `404` not the target speaker's request.

### GET/POST /api/speaker-requests/email-requests/

**URL name:** `speakerrequests:speaker_email_requests_list_create`  
**Auth:** authenticated  
**Pagination:** yes

`GET` returns requests where the requester is `request_from` or `request_to`,
with optional filters `request_from`, `request_to`, `event`.

`POST` sends a lightweight email request. The view expects `speaker_id`, but
assigns it directly to `request_to`, a `User` foreign key.

**Important:** `speaker_id` is a **User UUID**, not a `SpeakerProfile` UUID,
despite the name. `request_from` is overwritten with the authenticated user.

**POST request:**

```json
{
  "speaker_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "event": "PyCon UK 2026",
  "location": "Manchester",
  "message": "Would you speak at our event?"
}
```

`event` and `location` are strings, not relations. `request_from` and
`request_to` are set by the view. The recipient receives an email; `status`
defaults to `pending`.

**Response `201 Created`:** email request object:

```json
{
  "id": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
  "event": "PyCon UK 2026",
  "location": "Manchester",
  "request_from": "e4b5d7d5-3c1a-4f4e-9f0f-6f7a8b9c0d1e",
  "request_to": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "message": "Would you speak at our event?",
  "status": "pending"
}
```

**Errors:** `400` missing `speaker_id`, missing required fields (`event`,
`location`, `message`), or invalid recipient; `401`.

### PATCH /api/speaker-requests/email-requests/<uuid:pk>/

**URL name:** `speakerrequests:speaker_email_request_retrieve_update`  
**Auth:** authenticated; `request_to` user only.

**Request:** `{"status": "accepted"}` (or another value).

Returns the updated object. Unknown/foreign IDs return `404`. The view does not
validate status transitions or choices; any non-null string is saved, including
values outside `RequestStatusChoices`. Changing the status to the same value
returns `200` with an empty body.

> **Known failure:** if `status` is omitted, `new_status` is `None` and the save
> violates the column's `NOT NULL` constraint, returning `500`.

## Blogs

### GET/POST /api/blogs/

**URL name:** `blogs:blog-list-create`

| Method | Auth | Behaviour |
|---|---|---|
| `GET` | Public | Paginated list of all statuses, ordered by `-published_date`, `-created_at`. |
| `POST` | Authenticated | Create a post; `created_by` is set to the requester. |

**Current behaviour:** public list includes drafts and archived posts. Any
authenticated user may create a post.

**POST request:**

```json
{
  "title": "Our 2026 speaker lineup",
  "short_description": "A preview.",
  "full_description": "<p>Rich HTML content.</p>",
  "published_date": "2026-10-01",
  "status": "published"
}
```

`title` is required. `short_description`, `full_description`, `published_date`,
and `status` are optional. `status` is `draft` (default), `published`, or
`archived`. `image` is an optional image upload. The pair `(created_by, title)`
is unique; a duplicate returns `400` with `{"exception": "..."}` rather than the
standard validation envelope.

**Response `201 Created`:**

```json
{
  "id": "c3d4e5f6-a7b8-4c9d-8e0f-1a2b3c4d5e6f",
  "image": null,
  "title": "Our 2026 speaker lineup",
  "short_description": "A preview.",
  "full_description": "<p>Rich HTML content.</p>",
  "created_by": "e4b5d7d5-3c1a-4f4e-9f0f-6f7a8b9c0d1e",
  "published_date": "2026-10-01",
  "status": "published",
  "created_by_name": "Ada Lovelace"
}
```

### GET/PATCH/DELETE /api/blogs/<uuid:pk>/

**URL name:** `blogs:blog-detail`

| Method | Auth | Behaviour |
|---|---|---|
| `GET` | Public | Retrieve any post, including drafts. |
| `PATCH` | Authenticated | Update any post, including `created_by`. **No ownership check.** |
| `DELETE` | Authenticated | Delete any post; `204`. **No ownership check.** |

**Errors:** `404` unknown; `400` validation; `401` unauthenticated mutation;
`403` only when DRF applies a check that this view does not implement (there is
no owner check here).

## Teams

### GET /api/teams/

**URL name:** `teams:team-list`  
**Auth:** public  
**Pagination:** yes (generic list view)

Returns active team members ordered by `display_order`, then `name`.

```json
{
  "id": "d4e5f6a7-b8c9-4d0e-9f1a-2b3c4d5e6f7a",
  "name": "Ada Lovelace",
  "role": "Founder",
  "short_bio": "Mathematician and computing pioneer.",
  "avatar": null,
  "display_order": 1,
  "avatar_url": null,
  "social_links": [
    {"name": "GitHub", "link": "https://github.com/example"}
  ]
}
```

Inactive members are excluded by the queryset. `avatar_url` is absolute when
the request context is available.

## Schema and admin tooling

| Route | Method | Access | Response |
|---|---|---|---|
| `/api/schema/` | GET | Public | OpenAPI 3 schema. |
| `/api/docs/` | GET | Public | Swagger UI. |
| `/api/docs/redoc/` | GET | Public | ReDoc. |
| `/api/redoc/` | GET | Public | ReDoc alias. |
| `/admin/` | GET | Staff session | Django admin. |
| `/ckeditor5/` | Multiple | Package-configured | CKEditor upload endpoints. |

The generated schema is useful for client generation and field discovery, but
some views lack complete `@extend_schema` annotations. Use this page for actual
behaviour and the [Permissions](permissions.md) page for access rules.
