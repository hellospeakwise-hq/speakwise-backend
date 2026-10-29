# Coding Style

The normative guide for contributors is [`AGENTS.md`](../AGENTS.md). This page
summarises it and records how the repository's tooling actually enforces it.
Where the two disagree, follow `AGENTS.md` and raise the tooling gap rather than
silently copying an old pattern.

## Tooling reality

| Tool | Status |
|---|---|
| **Ruff** | Active linter and formatter, run by pre-commit and CI. Configuration: `ruff.toml`. |
| **pre-commit** | Active. Runs Ruff, codespell, and generic file checks. |
| **Black** | Present in `pyproject.toml` and `speakwise/scripts/black.sh`, but not run by CI. Do not treat the script as the standard. |
| **Flake8** | Present in dependencies and `speakwise/scripts/flake8.sh`, but not run by CI. |
| **pytest** | Not a dependency. `project.toml` contains a stale `config.settings.test` configuration. Use Django's test runner; see [Testing](testing.md). |
| **mypy / django-stubs** | Dependencies and stale config exist, but no type-check step runs in CI. Type hints are encouraged, not gated. |

`ruff.toml` is the effective configuration. Ruff does **not** read the separate
`project.toml` file, so its `[tool.ruff]` block is stale and inactive — for
example `force-single-line` is false in the effective config and line length is
the default 88. Do not cite `project.toml` as enforced style; use
`uv run ruff check --show-settings` if you need to confirm a rule.

### Commands

```bash
# Install the Git hooks once per clone.
uv run pre-commit install

# Run everything CI runs.
uv run pre-commit run --all-files

# Lint without scanning migration files (the pre-commit hook excludes them).
uv run ruff check . --exclude '*/migrations/*'

# Format application code.
uv run ruff format .

# See which config and settings Ruff is actually using.
uv run ruff check --show-settings
```

The pre-commit configuration excludes `docs/`, migrations, JSON, the frontend,
and several legacy directories. The generic file hooks have a `files:` pattern
that only matches a top-level `SpeakWise/` directory, which this repository does
not have. In practice, Ruff is the hook doing meaningful Python enforcement.
Do not "fix" pre-commit by enabling a flood of unrelated lint changes in a
feature PR.

## What Ruff enforces

`ruff.toml` selects `B`, `D`, `E`, `F`, `I`, `SIM`, and `W` with a Google
docstring convention. Notable consequences:

- Missing docstrings on public modules, classes, and functions are errors.
- Imports must be sorted and unused imports removed (`F401`, `I001`).
- Line length is ignored for lint (`E501`), but the formatter still wraps at 88.
- Double quotes are the formatter default.
- Tests have relaxed module/class/function docstring rules
  (`D100`, `D103`, `D104`) but still enforce other selected rules.

Docstrings should describe purpose, inputs, outputs, side effects, and
non-obvious decisions. Do not write a docstring that merely restates the name.

```python
# Good: explains a domain rule that is not obvious from the code.
def is_feedback_open(experience):
    """Return whether audience feedback is currently accepted.

    A linked event's start time takes precedence over ``event_date`` so an
    audience cannot submit feedback before the talk has happened.
    """
```

## Python style

- Use 4-space indentation. Black/Ruff formats the code; do not hand-align.
- Prefer clear domain names over abbreviations. `eligible_speakers()`, not
  `get_data()` or `process()`.
- Boolean names read as questions: `is_active`, `has_applied`,
  `can_be_contacted`.
- Import order is stdlib → Django → DRF → third-party → local, with a blank line
  between groups. Settings modules are the documented wildcard-import exception.
- No wildcard imports in application code. Remove unused imports.
- No commented-out code. Git history is the archive.
- Comment **why**, not **what**. Remove comments that narrate obvious code.
- Keep functions small and focused. The 20-line guidance in `AGENTS.md` is a
  default, not a hard linter rule; split when a function carries multiple
  responsibilities.
- Use timezone-aware datetimes (`django.utils.timezone.now()`), never
  `datetime.now()` for persisted timestamps.
- Prefer Django's ORM. Raw SQL requires a documented performance reason,
  approval, and parameterised queries.
- Never put secrets in source or docs. Use environment variables.

### Imports example

```python
import hashlib
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from feedbacks.models import Feedback
from profiles.models.speaker_models import SpeakerExperiences

from .services import hash_submitter_ip
```

## Django conventions

### Models

- Inherit shared timestamp behaviour from `base.models.TimeStampedModel` unless
  there is a reason not to.
- Put reusable filtering and business queries in a `Manager`/`QuerySet` method,
  not in views. Existing examples: `EventQuerySet.with_open_cfp()`,
  `SpeakerProfileQuerySet.matching_skill_names()`.
- Add `__str__` and domain-meaningful `Meta.verbose_name` values. The codebase
  has models missing these; do not remove existing ones, and add them when you
  are already changing that model for an in-scope reason.
- `AGENTS.md` says avoid `null=True` on strings. The existing schema uses it
  widely. For a new field, follow `AGENTS.md`; for changing an existing field,
  raise a migration plan instead of quietly normalising it.
- Use `blank=True` for optional form/API input and `null=True` only when `NULL`
  has distinct meaning.
- Indexes and constraints are schema decisions. Flag likely large-table filters;
  do not add an index without agreeing on the migration and rollout.

### Serializers

- Keep serializers focused on validation and shaping. Business rules belong in
  a service or model method. Existing services include `users/services/`,
  `feedbacks/services.py`, and `events/utils.py`.
- Field-specific validation goes in `validate_<field>()`; cross-field checks go
  in `validate()`.
- Use `self.context["request"]` rather than reaching into a global request.
- Separate read and write serializers when the shapes diverge. Existing example:
  `EventSerializer` versus `EventSubmitSerializer`.
- Mark server-owned fields read-only (`read_only_fields` or explicit fields).
  Never accept an owner ID from the client when it should come from the request.
- For nested writes, prefer the established `drf-writable-nested` pattern used
  by the speaker profile serializer; document sync semantics (for social links,
  omitted entries are removed on update).

### Views and permissions

- Use the existing generic-view/APIView pattern for the action. Do not switch a
  `ModelViewSet` to `APIView` (or vice versa) just for convenience.
- Plain `APIView` list endpoints must call `base.pagination.paginate_api_view`;
  DRF's global pagination only applies to generic views.
- Build querysets in `get_queryset()`, choose serializers in
  `get_serializer_class()`, and permissions in `get_permissions()` when they vary
  by action.
- Views handle HTTP. They should not contain multi-step domain logic, email
  construction, or repeated authorization checks.
- Every view must declare permissions explicitly. Use `IsEmailVerified` for
  verified-only mutations and `IsSubmitterOrSuperUser` for event ownership.
- Scope owned-object lookups by the user so foreign objects return `404` rather
  than revealing existence.
- Do not copy the known access-control gaps documented in
  [Permissions](api/permissions.md#current-access-control-gaps).

### URLs

- Use `app_name` namespaces and `reverse()`/named routes.
- Register ViewSets with an explicit `basename`.
- Keep parameter names consistent: `slug` for speaker/event/talk public routes,
  `pk` for UUID-keyed details, `feedback_slug` for public feedback.
- Match trailing-slash conventions. The password-reset confirm route is the
  existing exception.

### Errors and responses

- Raise DRF exceptions (`ValidationError`, `PermissionDenied`, `NotFound`,
  `Throttled`) instead of returning raw error dictionaries from views.
- Never return `200` with an error body; use the correct status code.
- Keep list responses in the standard pagination envelope.
- Do not catch an exception and silently continue. If swallowing is intentional
  (for example an email delivery failure logged by a task), comment why.
- Use `@extend_schema` on API views where practical. The generated schema is not
  complete; behavioural documentation lives in [Endpoints](api/endpoints.md).

## Service and task style

- Put multi-step business rules in a service function with a clear name:
  `resolve_feedback_experience()`, `build_feedback_qr_payload()`,
  `issue_otp()`, `build_auth_payload()`.
- Background tasks live in `<app>/tasks.py` and use `@task()` from
  `django_tasks`.
- Pass IDs or primitive values into tasks, not model instances.
- Never log OTP codes, tokens, passwords, raw IPs, or other sensitive values.
  Existing task docstrings make this explicit; preserve that contract.
- Tasks must be idempotent where retries are possible, or clearly document why
  they are not.
- Email sending failures are logged rather than re-raised in the existing user
  tasks. If you change that behaviour, consider retry semantics first.

## Testing style

Tests are part of the coding standard, not a separate afterthought. Every
behaviour change needs tests for the happy path, permissions, validation, and
edge cases. Use Django `TestCase`/`APITestCase`, `reverse()`, and
`force_authenticate()` consistently with the existing suites. See
[Testing](testing.md).

## Documentation style

- Public functions/classes need docstrings, but endpoint docs need more than
  docstrings: request/response shapes, status codes, permissions, and failure
  modes.
- Update `docs/` when changing API behaviour. Documentation is excluded from
  pre-commit and from the pre-commit/migrations CI path filters, but the
  staging workflow still tests every `development` push; review formatting and
  links manually.
- Use relative links between documentation pages.
- Mark abridged examples as abridged; do not present invented fields as real.

## What not to copy

The codebase contains known inconsistencies. They are current behaviour, not
style guidance:

- Organization update/delete has no owner check.
- Blog update/delete has no ownership check and the public list exposes drafts.
- `GET /api/speaker-requests/` returns all requests.
- Event `submitted_by` and `slug` remain writable on PATCH.
- `SpeakerRequestAcceptView` reads `event.location.venue` even though
  `location` is a string.
- `TalkSerializer` declares a `session` field that `Talks` cannot provide; reads skip it and the create path does not support it.
- Some model docstrings are stale (for example the OTP hash algorithm).

If a task touches one of these areas, fix it deliberately with tests and a
separate commit or PR — do not quietly extend the pattern.
