# Contributing

[`AGENTS.md`](../AGENTS.md) is the normative contribution guide. Read it in full
before changing code. This page is the practical checklist for getting a change
reviewed and merged.

## Before you start

- Read the app you are about to change: models, serializers, views, permissions,
  URLs, services, tests, and admin.
- Check whether the behaviour already exists somewhere.
- Identify every file the change should touch — and the ones it should not.
- If the task is ambiguous, requires a schema change outside scope, or reveals a
  bug in unrelated code, **stop and ask** rather than guessing.
- For API changes, read [API conventions](api/overview.md) and
  [Permissions](api/permissions.md) first.

If you believe an existing pattern is wrong, say so in the PR or issue. Do not
quietly refactor it as part of an unrelated feature.

## Branches

Use the prefixes defined in `AGENTS.md`:

```text
feature/<short-description>     # new functionality
fix/<short-description>         # bug fixes
chore/<short-description>       # dependencies, config, docs
refactor/<short-description>    # restructuring without behaviour change
test/<short-description>        # test-only changes
```

Keep branches short-lived. Open a draft PR early if a change is growing beyond a
20-minute review. Do not commit directly to the deployment branches; open a pull
request against the team's integration branch.

CI runs on pull requests targeting `main` and `development`. Deployment
workflows also react to pushes to `main`, so merge there only when the commit is
intended to ship.

## Commits

Use Conventional Commits:

```text
<type>(<scope>): <imperative short description>
```

Examples:

```text
feat(profiles): add availability filter to speaker list endpoint
fix(events): reject duplicate normalized event websites
refactor(speakerrequests): extract response transitions to a service
test(profiles): cover anonymous access to the experiences detail endpoint
chore(deps): upgrade djangorestframework to 3.16.1
docs(api): document OAuth exchange-code flow
```

Rules:

- Present tense, imperative mood: "add", not "added" or "adds".
- Scope is the Django app or module (`speakers`, `events`, `users`).
- Subject under 72 characters.
- Add a body after a blank line when the *why* is not obvious.
- One logical change per commit. Keep formatting-only changes separate.
- Do not commit generated secrets, `.env`, database dumps, media, or coverage
  artifacts.

## Making the change

### API changes

1. Update the model and migration if the data shape changes.
2. Update the serializer for validation/shape.
3. Put business rules in a service or model method, not the view.
4. Declare permissions explicitly, including per-action permissions.
5. Add filters/query parameters with validation.
6. Update URL names and `basename`s consistently.
7. Add `@extend_schema` where practical.
8. Update the endpoint reference and any affected docs.

Do not change response envelopes or status-code conventions without agreement.
Do not expose internal IDs where the existing resource uses UUIDs or slugs.

### Database changes

- Create a migration with `uv run python manage.py makemigrations`.
- Review the generated SQL/migration; add data migrations separately.
- Consider existing rows, nullability, defaults, indexes, and reverse migration.
- Run `uv run python manage.py makemigrations --check --dry-run` before pushing.
- Flag table-size and locking implications for large tables.
- Never modify a migration that has already been deployed; add a new one.

### Background jobs

- Add tasks in the app's `tasks.py` using the existing `@task()` pattern.
- Pass IDs/primitives, not model instances.
- Make retries safe where possible.
- Do not log sensitive data.
- Test the service logic directly; the test settings run tasks inline.

### Documentation changes

- Keep documentation under `docs/` and relative links working.
- Describe **current behaviour**, and explicitly label known gaps instead of
  presenting them as intended policy.
- Mark examples as abridged when they omit fields.
- Do not invent endpoints, fields, defaults, or guarantees.
- Docs are excluded from pre-commit. The pre-commit and migrations workflows
  also ignore Markdown changes, but the staging deploy workflow still runs its
  test job on every `development` push. Review formatting and links manually.

## Required checks

Run these before requesting review:

```bash
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test --settings=speakwise.settings.test
uv run pre-commit run --all-files
```

If you touched PostgreSQL-specific behaviour, run the suite against PostgreSQL
as CI does, not only the in-memory SQLite test settings. See [Testing](testing.md).

If `ruff check .` is run directly, exclude migrations:

```bash
uv run ruff check . --exclude '*/migrations/*'
```

The pre-commit configuration excludes migrations and docs. The pre-commit and
migrations workflows ignore Markdown-only changes, but the staging deploy
workflow still runs its test job on every `development` push.

## Pull request expectations

A PR should be reviewable in under 20 minutes. If it is not, split it.

Include:

1. **Title** in Conventional Commit form.
2. **What changed** and **why**.
3. **How it was tested**, including the command and any PostgreSQL-only run.
4. **Non-obvious decisions** and alternatives considered.
5. **Known limitations** or follow-up work.
6. **Documentation updates**, or a reason none were needed.
7. Confirmation that existing tests pass.

Example:

```markdown
## What
Adds a verified-email check to organization updates and scopes the queryset to
the owner.

## Why
Any verified user could previously update or delete any organization.

## Tests
- `uv run python manage.py test --settings=speakwise.settings.test`
- Added owner/non-owner/anonymous/staff cases in `profiles/tests/organization_tests.py`

## Notes
Supersedes the access-control gap documented in `docs/api/permissions.md`.
Migration not required.
```

### Scope discipline

Touch only what the task requires. Do not include drive-by renames, dependency
upgrades, formatting sweeps, or unrelated fixes. If you find a minor issue in a
file you are already changing, fix it in a **separate commit** and say so. For a
larger unrelated issue, open a separate PR or issue.

## Pre-PR checklist

- [ ] I read `AGENTS.md` and the relevant app.
- [ ] The branch name follows the convention.
- [ ] Commits are logical, imperative, and scoped.
- [ ] Only files in scope were changed.
- [ ] Shared logic was abstracted rather than copied.
- [ ] Business logic is not in views or serializers.
- [ ] Every new public function/class has a docstring.
- [ ] Unused imports and commented-out code are gone.
- [ ] Every new view declares explicit permissions.
- [ ] Owned resources are checked by owner/user scope, not just authentication.
- [ ] No N+1 queries were introduced; related objects are selected/prefetched.
- [ ] Inputs are validated; raw query params are not passed to querysets.
- [ ] No secrets, tokens, OTPs, raw IPs, or PII are logged or committed.
- [ ] Migrations are included and reviewed.
- [ ] Tests cover happy path, permissions, validation, and edge cases.
- [ ] The full test suite passes.
- [ ] Documentation reflects the change.
- [ ] I reviewed my own diff before requesting review.

## Review conversations

- Treat review comments as design discussion, not personal feedback.
- Resolve a thread only after the change is made or the reasoning is recorded.
- If a reviewer requests a change that conflicts with `AGENTS.md`, ask which
  standard wins; do not silently pick one.
- Do not force-push over review history unless the team explicitly asks.
- Keep CI green. A red pipeline is not "ready for review".

## Reporting bugs and security issues

For functional bugs, include:

- The endpoint or command.
- Exact request/payload (redact tokens and personal data).
- Expected vs actual response and status code.
- Relevant logs with secrets removed.
- Whether it reproduces with test settings or only PostgreSQL.

For security vulnerabilities, do not open a public issue with exploit details.
Contact the maintainers privately and include a minimal reproduction. The known
access-control gaps are listed in
[Permissions](api/permissions.md#current-access-control-gaps); a fix should be
scoped, tested, and documented as a behaviour change.

## Deployment awareness

Merging to `main` can trigger deployment workflows. Before merging:

- Confirm migrations are safe to run automatically at container start.
- Confirm the worker is running if the change adds a task.
- Confirm static/media configuration if the change adds an upload.
- Confirm new environment variables are set in production **before** the code
  reaches the server.
- Confirm only one deployment path is active. Both `deploy.yml` and
  `deploy-prod.yml` currently trigger on `main`; see
  [Deployment](deployment.md#cicd-workflows).

## Getting unstuck

Ask early, with specifics:

- "The task says filter by expertise, but the model has a free-text `organization`
  field and a `skill_tags` relation. Which one should this use?"
- "This requires adding a field to `SpeakerProfile`, which is outside the stated
  scope. Do you want a migration in this PR or a follow-up?"
- "The existing endpoint returns all requests to every authenticated user. Should
  I preserve that behaviour or fix it here?"

Do not fill gaps with assumptions. A five-minute question is cheaper than a
rejected PR.
