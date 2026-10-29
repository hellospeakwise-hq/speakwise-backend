# Testing

The project uses **Django's built-in test runner**. There is no pytest
dependency, no factory library, and no coverage gate. Tests live inside each
Django app, either in a `tests.py` module or in a `tests/` package.

At the documentation baseline the suite contains **353 tests** and passes:

```bash
uv run python manage.py test --settings=speakwise.settings.test
```

## Test settings

`speakwise.settings.test` imports `local.py` and then overrides:

| Setting | Test value | Consequence |
|---|---|---|
| Database | In-memory SQLite | Fast, isolated, no PostgreSQL service required. |
| Password hasher | MD5 | Faster account creation; never use in production. |
| Cache | `LocMemCache` | No `django_cache` table needed; state is per-process. |
| Tasks | `ImmediateBackend` | `.enqueue()` runs synchronously. |
| Email | Inherited console backend | Override to locmem when asserting `mail.outbox`. |

Because tests use SQLite, PostgreSQL-specific behaviour (case-sensitive
uniqueness, `NULL` ordering, transaction isolation, `select_for_update`) is not
exercised locally. The CI migration/test job runs the suite against PostgreSQL
with `speakwise.settings.local`, so a green local run is necessary but not
sufficient for database-sensitive changes.

Without `--settings=speakwise.settings.test`, `manage.py` uses
`speakwise.settings.local` and expects the development PostgreSQL database.

## Running tests

```bash
# Whole suite, isolated settings
uv run python manage.py test --settings=speakwise.settings.test

# One app
uv run python manage.py test users --settings=speakwise.settings.test

# One module
uv run python manage.py test users.tests.tests_auth --settings=speakwise.settings.test

# One class or method
uv run python manage.py test \
  users.tests.tests_auth.UserLoginProfileDataTests \
  --settings=speakwise.settings.test

# Stop on first failure / show timings
uv run python manage.py test --settings=speakwise.settings.test --failfast
uv run python manage.py test --settings=speakwise.settings.test --timing
```

Django discovers files matching `test*.py`. The repository's names (`tests.py`,
`tests_auth.py`, `test_models.py`, etc.) all match. Test classes must subclass
`django.test.TestCase` or `rest_framework.test.APITestCase` (or another Django
test case); bare pytest-style functions are not discovered.

## Test layout

| Tests | Coverage |
|---|---|
| `base/tests.py` | Health check, pagination envelope, API error shape, upload validators. |
| `users/tests/` | Auth, login profiles, OTP, password reset, OAuth, account model. |
| `profiles/tests/` | Speaker profiles, experiences, skills, follows, notifications, organizations. |
| `events/tests/` | Event CRUD, CFP Market, CFP closing. |
| `talks/tests/` | Models, serializers, URLs, views, IDOR/security. |
| `feedbacks/tests.py` | Rating model, rate date gating and IP cooldown, QR ownership, feedback list, and profile summary. |
| `blogs/tests.py` | Public reads, authenticated create/update/delete, creator attribution, image upload, validation. |
| `teams/tests.py` | Team models, serializers, and the public team list. |
| `speakerrequests/tests.py` | Placeholder only: no test cases at this baseline. |

`speakerrequests` is the only app with a test module but no test coverage. The
absence of tests is a gap, not permission to skip tests for a change there. New
behaviour needs tests in the app it belongs to.

## Patterns used in this codebase

### Authenticated API calls

```python
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from profiles.models import SpeakerProfile
from users.models import User


class SpeakerProfileAccessTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ada",
            email="ada@example.com",
            password="correct-horse-battery-staple",
            is_email_verified=True,
        )
        SpeakerProfile.objects.create(user_account=self.user, country="UK")
        self.client.force_authenticate(self.user)

    def test_me_returns_own_profile(self):
        response = self.client.get(reverse("speakers:speakers_me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "ada")
        self.assertEqual(response.data["country"], "UK")
```

`force_authenticate()` bypasses JWTs and is the standard pattern here. Add at
least one test that exercises real authentication when changing auth itself.

### Clear cache state

Throttles and login lockout are cached. Tests that submit login, OTP, register,
or feedback requests should start with a clean cache:

```python
from django.core.cache import cache

def setUp(self):
    cache.clear()
    ...
```

With test settings the cache is locmem and isolated per process, but it is still
shared between tests in the same process.

### Emails

The local/test email backend prints to the console. To assert delivery, override
the backend and inspect `mail.outbox`:

```python
from django.core import mail
from django.test import override_settings


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
def test_registration_sends_otp(self):
    response = self.client.post(reverse("users:register"), {...}, format="json")
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertEqual(len(mail.outbox), 1)
```

Because tasks run inline under test settings, email tasks execute before the
response returns. If you switch a test to the database task backend, you must
run the queue or call the task directly.

### Time-dependent behaviour

Use `django.utils.timezone.now()` in test data and set explicit past/future
dates. Do not rely on the wall clock being just before or after a boundary.

```python
from datetime import timedelta
from django.utils import timezone

event = Event.objects.create(
    title="Yesterday",
    website="https://example.com",
    start_date_time=timezone.now() - timedelta(days=1),
    is_active=True,
)
```

Feedback tests need an experience whose linked event start (or `event_date`) has
passed. CFP tests should cover both inside and outside the open/deadline window.

### External services

Mock provider HTTP calls and Turnstile rather than making network requests.
The OAuth tests use `unittest.mock.patch` around the service functions. Never
commit real provider tokens or call Mailgun from tests.

### Direct task checks

The DB task backend is not active in tests. For a task wrapper, call the
underlying function or `.call()` where the API supports it, and separately test
the enqueuing path with a mocked `.enqueue()` if needed.

## What a good test asserts

A status-code assertion alone is noise. Cover:

- The exact response shape and important field values.
- Database side effects (`refresh_from_db()`, counts, state transitions).
- That forbidden rows are absent from lists, not merely that the request failed.
- Anonymous, authenticated non-owner, owner, staff, and superuser where relevant.
- Validation errors for missing/invalid input.
- Empty results returning `200` with an empty page, not an error.
- Boundary conditions: OTP expiry, cooldown, feedback date gate, CFP deadline,
  duplicate follows/requests, one-profile rule.

`AGENTS.md` requires tests for every change:
[Testing requirements](../AGENTS.md#35-tests-are-compulsory--write-them-properly).

## CI behaviour

| Workflow | Trigger | What it runs |
|---|---|---|
| `precommit.yml` | PR/push to `main` or `development` | `pre-commit run --all-files` on Python 3.12. Docs-only changes are ignored. |
| `migrations-test.yml` | PR/push to `main` or `development` | PostgreSQL 15; `migrate`, `makemigrations --check --dry-run`, and `manage.py test` with local settings. Markdown-only changes are ignored. |
| `deploy-staging.yml` | Push to `development` | Migrate and test with `speakwise.settings.test`; deployment steps are commented out. |
| `deploy.yml`, `deploy-prod.yml` | Push to `main` | Deployment workflows; see [Deployment](deployment.md). |

Notes:

- The migrations workflow uses Python 3.14 and a PostgreSQL service; the
  pre-commit workflow uses Python 3.12 only to run tooling.
- The pre-commit workflow ignores `docs/**`; documentation correctness is not
  validated by CI.
- There is no coverage threshold and no `pytest.ini`/`conftest.py`.
- `project.toml` contains stale pytest configuration referencing
  `config.settings.test` and `nebula`. Running `pytest` is unsupported.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `relation "django_cache" does not exist` | You are running with local settings without `createcachetable`. Use test settings or create the table. |
| Throttle/lockout test passes alone, fails in suite | Cached state leaked. Call `cache.clear()` in `setUp`. |
| `mail.outbox` is empty | The active backend is console. Override to locmem for that test. |
| `pytest` cannot find `config.settings.test` | Stale config; use `manage.py test`. |
| Test database cannot connect | You omitted `--settings=speakwise.settings.test`; local settings expect PostgreSQL. |
| PostgreSQL-specific constraint not caught locally | Run the suite against PostgreSQL, as CI does. |
| OTP/task side effects missing | Test settings use immediate tasks; check that `.enqueue()` is actually called or the task is mocked. |

For setup failures, see [Installation](installation.md#troubleshooting). For
review expectations, see [Contributing](contributing.md).
