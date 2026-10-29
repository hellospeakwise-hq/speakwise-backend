# Permissions and Access Control

SpeakWise uses a small set of Django/DRF checks rather than a role or
organization-membership system. This page describes the actors, permission
classes, and the access each endpoint actually enforces.

> **Read this as current behaviour, not ideal policy.** Several endpoints have
> weaker ownership checks than their names or docstrings suggest. Those gaps are
> listed at the end so contributors do not accidentally rely on them.

## Actors

| Actor | Definition |
|---|---|
| **Anonymous** | No valid JWT. |
| **Authenticated** | A valid JWT whose `request.user` is active. |
| **Verified** | Authenticated with `is_email_verified = true`. OAuth users are verified at signup; email/password users become verified through OTP. |
| **Staff** | `is_staff = true`. Django admin access and `IsAdminUser` checks. Staff are not automatically superusers. |
| **Superuser** | `is_superuser = true`. Bypasses most object-level checks and can see/manage pending events. |
| **Owner** | The user referenced by a profile (`SpeakerProfile.user_account`, `OrganizationProfile.owner`), an experience/skill/notification, or the event's `submitted_by`. Ownership is checked in view code, not by a shared organization role. |

There is **no organization membership model**. `OrganizationProfile.owner` is a
single user. Speaker requests and email requests are not scoped to an
organization.

## Permission classes

| Class | Location | Behaviour |
|---|---|---|
| `AllowAny` | DRF | No authentication required. If a client sends an invalid token, JWT authentication may still reject it before permissions run. |
| `IsAuthenticated` | DRF | Requires a valid authenticated user. Missing credentials return `401`; authenticated denial returns `403`. |
| `IsAuthenticatedOrReadOnly` | DRF | Safe methods (`GET`, `HEAD`, `OPTIONS`) are public; mutations require authentication. It does **not** imply object ownership. |
| `IsAdminUser` | DRF | Requires `user.is_staff` (not necessarily `is_superuser`). |
| `IsEmailVerified` | `base.permissions` | Extends `IsAuthenticated`; additionally requires `is_email_verified`. Returns `403` with `"Email verification is required to perform this action."` for unverified users. |
| `IsSuperUser` | `base.permissions` | Requires authentication and `is_superuser`. Checks both view and object permissions. |
| `IsSubmitterOrSuperUser` | `base.permissions` | View-level check requires authentication; object-level check allows the object's `submitted_by` user or any superuser. Used for event management. |

`SpeakerProfile` ownership, experience ownership, skill ownership, notification
ownership, follow ownership, and feedback QR ownership are enforced with
explicit queryset filters and comparisons inside the views, not by reusable
permission classes.

## Access matrix

### Authentication and users

| Endpoint | Anonymous | Authenticated | Additional check |
|---|---|---|---|
| `POST /api/users/auth/register/` | Yes | — | Turnstile when configured; `register` throttle. |
| `POST /api/users/auth/verify-otp/` | Yes | — | OTP rules. |
| `POST /api/users/auth/resend-otp/` | Yes | — | Generic response; cooldown enforced silently. |
| `POST /api/users/auth/login/` | Yes | — | Verified email; lockout; `login` throttle. |
| `POST /api/users/auth/logout/` | No | Yes | Valid refresh token required for blacklist. |
| `POST /api/users/auth/password-reset/` | Yes | — | Generic response; `password_reset` throttle. |
| `POST /api/users/auth/password-reset/confirm` | Yes | — | Valid Django reset token. |
| GitHub/Google start and callback | Yes | — | OAuth state in session. |
| `POST /api/users/auth/oauth/token/` | Yes | — | Single-use exchange code; `oauth_token` throttle. |
| `GET /api/users/me/` | No | Yes | Returns own user. |
| `PATCH /api/users/me/` | No | Verified | Changing email resets verification and issues a new OTP. |
| `GET /api/users/` | No | No | Staff (`is_staff`) only. |

### Speaker profiles and activity

| Endpoint | Anonymous | Authenticated | Additional check |
|---|---|---|---|
| `GET /api/speakers/` | Yes | Yes | Public list. |
| `POST /api/speakers/` | No | Verified | One-profile rule; no speaker profile already. |
| `GET /api/speakers/me/` | No | Yes | Own speaker profile. |
| `PATCH /api/speakers/me/` | No | Verified | Own profile. |
| `GET /api/speakers/<slug>/` | Yes | Yes | Public detail; accepts slug or UUID. |
| `PATCH/DELETE /api/speakers/<slug>/` | No | Verified | Must be `profile.user_account == request.user`. |
| `GET/POST /api/speakers/experiences/` | No | Yes | Own experiences only. |
| `GET /api/speakers/experiences/<uuid:pk>/` | Technically declared read-only | Yes | Lookup filters by `request.user`; anonymous requests raise an unhandled Django `ValidationError` and return `500`, not a public read. |
| `PATCH/DELETE /api/speakers/experiences/<uuid:pk>/` | No | Yes | Own experience via queryset filter. `PATCH` can change `speaker`, transferring the row. |
| `GET /api/speakers/<slug>/experiences/` | Yes | Yes | Public experiences for that speaker. |
| `GET/POST /api/speakers/skills/` | No | Yes | Own skill tags; POST requires a speaker profile. |
| `GET/PATCH/DELETE /api/speakers/skills/<uuid:pk>/` | No | Yes | Own skill tag. |
| `GET /api/notifications/` | No | Yes | Own notifications. |
| `PATCH /api/notifications/<uuid:pk>/read/` | No | Yes | Own notification. |
| `GET /api/speakers/<slug>/follow/` | No | Yes | Follow status for the requester. |
| `POST /api/speakers/<slug>/follow/` | No | Yes | Cannot follow yourself; duplicate is `400`. |
| `DELETE /api/speakers/<slug>/follow/` | No | Yes | Must currently follow. |
| `GET /api/speakers/<slug>/followers/` | Yes | Yes | Public; at most 100 entries. |
| `GET /api/speakers/<slug>/following/` | Yes | Yes | Public; at most 100 entries. |

### Organizations

| Endpoint | Anonymous | Authenticated | Additional check |
|---|---|---|---|
| `GET /api/organization/` | Yes | Yes | Public list. |
| `POST /api/organization/` | No | Verified | Owner is set by the serializer; one-profile rule. |
| `GET /api/organization/<uuid:pk>/` | Yes | Yes | Public detail. |
| `PUT /api/organization/<uuid:pk>/` | No | Verified | **No ownership check.** Any verified user can update any organization. |
| `DELETE /api/organization/<uuid:pk>/` | No | Verified | **No ownership check.** Any verified user can delete any organization. |

### Events and CFP Market

| Endpoint | Anonymous | Authenticated | Additional check |
|---|---|---|---|
| `GET /api/events/` | Yes | Yes | Active events only. |
| `POST /api/events/` | No | Yes | Regular users submit inactive events; superusers may set `is_active`. |
| `GET /api/events/me/` | No | Yes | Events where `submitted_by == request.user`. |
| `GET /api/events/cfp-market/` | Yes | Yes | Open CFP criteria. |
| `GET /api/events/private/<slug>/` | No | Yes | Submitter or superuser. |
| `PATCH/DELETE /api/events/private/<slug>/` | No | Yes | Submitter or superuser; non-superusers cannot set `is_active`. |
| `GET /api/events/<slug>/` | Yes | Yes | Anonymous: active only. Authenticated: active or own pending; superuser: any. |
| `PATCH/DELETE /api/events/<slug>/` | No | Yes | Submitter or superuser; non-superusers cannot set `is_active`. |

### Talks and reviews

| Endpoint | Anonymous | Authenticated | Additional check |
|---|---|---|---|
| `GET /api/talks/` | Empty page | Yes | Authenticated users see only their own talks. |
| `POST /api/talks/` | No | Yes | Requires a speaker profile; speaker is inferred. |
| `GET /api/talks/<uuid:pk>/` | Yes | Yes | Any talk, including non-public. |
| `PATCH/DELETE /api/talks/<uuid:pk>/` | No | Yes | Own talk (queryset filtered by speaker user). |
| `GET /api/talks/<slug>/` | Yes | Yes | Public talks only (`is_public=True`). |
| `GET /api/speakers/<slug>/talks/` | Yes | Yes | Public talks for that speaker. |
| `GET /api/talks/<slug>/reviews/` | Yes | Yes | Public talk reviews only. |
| `POST /api/talks/<slug>/reviews/` | Yes | Yes | Talk must exist and `is_reviewable=True`; anonymous throttle 100/hour. |

### Feedback

| Endpoint | Anonymous | Authenticated | Additional check |
|---|---|---|---|
| `GET /api/feedbacks/` | No | Yes | Feedback for the requester's speaker profile. |
| `GET /api/feedbacks/rate/<feedback_slug>/` | Yes | Yes | Opaque slug; 404 if unknown. |
| `POST /api/feedbacks/rate/<feedback_slug>/` | Yes | Yes | Feedback window open, `feedback_enabled`, IP cooldown. |
| `GET /api/feedbacks/qrcode/<feedback_slug>/` | No | Verified | Must own the experience's speaker profile. |

### Speaker requests

| Endpoint | Anonymous | Authenticated | Additional check |
|---|---|---|---|
| `GET /api/speaker-requests/` | No | Yes | **Returns every request in the database**, despite the organizer-oriented docstring. |
| `POST /api/speaker-requests/` | No | Yes | Any authenticated user; no organization/role check. Duplicate speaker+event is rejected. |
| `GET/PATCH/DELETE /api/speaker-requests/<uuid:pk>/` | No | Superuser | Requires both `IsAuthenticated` and `IsSuperUser`. |
| `GET /api/speaker-requests/incoming/` | No | Yes | Requests where `speaker.user_account == request.user`. |
| `PATCH /api/speaker-requests/<uuid:pk>/respond/` | No | Yes | Must be the target speaker; request must be `pending`. |
| `GET /api/speaker-requests/email-requests/` | No | Yes | Requests sent by or addressed to the requester. |
| `POST /api/speaker-requests/email-requests/` | No | Yes | Any authenticated user can send; `speaker_id` is treated as a user ID. |
| `PATCH /api/speaker-requests/email-requests/<uuid:pk>/` | No | Yes | Must be the `request_to` user. |

### Blogs and teams

| Endpoint | Anonymous | Authenticated | Additional check |
|---|---|---|---|
| `GET /api/blogs/` | Yes | Yes | Returns **all** statuses, including drafts and archived posts. |
| `POST /api/blogs/` | No | Yes | Any authenticated user. |
| `GET /api/blogs/<uuid:pk>/` | Yes | Yes | Any post, including drafts. |
| `PATCH/DELETE /api/blogs/<uuid:pk>/` | No | Yes | **No ownership check.** Any authenticated user can edit or delete any post; `PATCH` can also rewrite `created_by`. |
| `GET /api/teams/` | Yes | Yes | Active team members only. |

### Tooling

| Endpoint | Access |
|---|---|
| `GET /health/` | Public. |
| `GET /api/schema/`, `/api/docs/`, `/api/docs/redoc/`, `/api/redoc/` | Public. |
| `/admin/` | Django staff/superuser login. |
| `/ckeditor5/` | CKEditor upload views; staff-only permissions are configured by the package. |

## Ownership rules in detail

### Speaker profiles

- Creation is allowed only for a verified user with no speaker or organization
  profile.
- `GET /api/speakers/me/` requires any authenticated user but returns `404` if
  that user has no speaker profile.
- Patching a profile by slug/UUID requires both a verified email and
  `profile.user_account == request.user`.
- Deleting a speaker profile deletes the profile only; the `User` row remains.

### Experiences and skills

- List/create endpoints always operate on the authenticated user's speaker
  profile. Creating an experience without a speaker profile returns an error.
- Detail endpoints fetch by primary key **and** `speaker__user_account=user`, so
  another user's experience or skill returns `404`, not `403`.
- `SpeakerExperiencesRetrieveUpdateDestroyView` declares
  `IsAuthenticatedOrReadOnly`, but `get_object()` receives `request.user`. An
  anonymous detail GET filters on `AnonymousUser`, raises an unhandled Django
  `ValidationError`, and returns `500` rather than a public read.
- `PATCH` on an experience is scoped to the current owner, but the serializer
  accepts `speaker`; the owner can move the experience to another profile.

### Notifications

- List is filtered by `user=request.user`.
- Mark-read fetches by primary key and `user=request.user`; unknown or foreign
  notifications return a custom `404`.

### Events

- `EventDetailView` and `PrivateEventDetailView` both call object-level checks
  against `submitted_by`.
- Non-superusers have `is_active` removed from PATCH payloads, preventing
  self-approval.
- `EventListView` uses a different serializer for non-superusers and injects
  `is_active=False` plus `submitted_by=request.user`.
- `submitted_by` and `slug` are writable fields in `EventSerializer`. A
  submitter editing an event can therefore change the attribution or slug unless
  the serializer is tightened. Treat this as a current gap.

### Feedback

- The list endpoint identifies the speaker by `speaker__user_account=request.user`.
  Users without a speaker profile get an empty page.
- Public rating uses the experience's `feedback_slug` only.
- QR generation requires a verified email and exact owner match on the
  experience's speaker.

### Speaker requests

- Incoming requests and respond actions are scoped to the target speaker's user
  account.
- The detail endpoint is superuser-only.
- Email-request list is scoped to `request_from`/`request_to`, but creation is
  open to any authenticated user.
- Email-request PATCH checks only `request_to=request.user`; it does not validate
  that the requested status is a valid transition.

## Current access-control gaps

These are real behaviours that should be fixed deliberately, not treated as
intended policy. They are documented here so reviewers can recognise them and
new code does not copy them.

| Area | Current behaviour | Risk |
|---|---|---|
| Organization detail | `PUT` and `DELETE` require only a verified account; no owner or staff check. | Any verified user can alter or delete any organization. |
| Organization public serializer | Includes `owner` UUID and `admin_notes` in public GET responses. | Internal notes and owner identifiers are exposed. |
| Blogs | Any authenticated user can create, edit, or delete any post, and `PATCH` can rewrite `created_by`. Public list/detail exposes drafts, archived posts, and `created_by`. | Unauthorized content changes, author impersonation, and draft disclosure. |
| Speaker request list | `GET /api/speaker-requests/` queries `SpeakerRequest.objects.all()`; the `user` argument is unused. | Every authenticated user can enumerate all invitations, including messages and fees. |
| Speaker request creation | Any authenticated user can create a request for any speaker/event; `requested_by` is client-writable. `speaker` is optional at validation but the view dereferences it after saving, so omitting it produces a `500`. | No organizer identity or organization scoping; malformed requests can create orphan rows before failing. |
| Event serializer | `submitted_by` and `slug` are writable on PATCH. | A submitter can transfer attribution or change URLs. |
| Event CFP creation | A non-superuser can set CFP fields on submission. | Pending events can carry arbitrary CFP metadata, though they are not public until approved. |
| Talk list | `GET /api/talks/` returns only the requester's talks and an empty page anonymously. | It is not a public catalog despite the path. Use the slug/public endpoints. |
| Talk reviews | Creation checks only that the talk exists and `is_reviewable`; it does not require `is_public`. | Reviews can be posted against a non-public talk by anyone who knows the slug. |
| Speaker request response | View reads `req.event.location.venue` although `Event.location` is a `CharField`. | Response can raise `AttributeError` when a location string is set, producing a `500` after the status change is saved. |
| Email request filters | `EmailRequestsFilter.event` is a `CharFilter` on an `event` text field; `SpeakerRequestFilter.event` uses `NumberFilter` against a UUID field. | Filters may not behave as expected. |
| Password reset confirm | Route has no trailing slash. | Clients using a slash get a redirect/404 depending on middleware. |
| Experience update | The owner-scoped `PATCH` accepts a writable `speaker` field. | An owner can transfer the experience to another speaker, moving it out of their own list. |

## Practical rules for new endpoints

1. Declare permissions explicitly; never leave a view without a permission class.
2. Use `IsEmailVerified` (not just `IsAuthenticated`) for creating or mutating
   public-facing profiles and content.
3. Scope object lookups by the requesting user where the resource is owned:
   `Model.objects.get(pk=pk, owner=request.user)` so foreign objects return
   `404` rather than leaking existence.
4. Do not infer organization membership; it does not exist. If a feature needs
   it, raise the data-model change before implementing.
5. Keep staff and superuser semantics distinct. `IsAdminUser` is staff-only.
6. Add tests for anonymous, authenticated non-owner, verified owner, staff, and
   superuser where relevant.
