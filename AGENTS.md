# agents.md — AI Agent Contribution Guide

> This document governs how AI agents (Claude, Copilot, Cursor, Windsurf, or any other)
> contribute to this codebase. Every engineer on this team uses different tooling.
> This file exists so the *output* of those tools is consistent, regardless of the tool.
>
> **Read this file in full before making any changes. No exceptions.**

---

## 0. The Prime Directive

> **An agent's job is to implement the engineer's intent — not to think for them.**

You are a skilled executor, not a decision-maker. If the engineer says "add a filter for
speaker availability", you add that filter. You do not redesign the availability model,
rename existing fields, or restructure the serializer because you think it is cleaner.
If you believe there is a better approach, you **say so and ask** — you do not act unilaterally.

**When in doubt: stop and ask. Never hallucinate a solution.**

---

## 1. Before You Write a Single Line

Run through this checklist mentally before touching the codebase:

- [ ] Have I read the full task description and understood what is being asked?
- [ ] Have I explored the existing structure of the relevant app(s)?
- [ ] Have I checked whether this functionality already exists somewhere?
- [ ] Do I know exactly which files I need to touch — and why?
- [ ] Is there anything I am unclear about that could cause a wrong decision?

If any checkbox fails → **ask the engineer before proceeding.**

---

## 2. Understand the Project First

This is a **Django REST Framework** project for sourcing speakers for conference events.
Core domain concepts include: `conferences`, `speakers`, `events`, `applications`,
`profiles`, and `bookings`. Before working in any app, spend a moment understanding:

- What the app's models represent in the domain.
- How its serializers shape data in and out of the API.
- What permission classes guard its views.
- How it relates to adjacent apps.

Do not work in an app you have not read through first.

---

## 3. The Non-Negotiable Rules

These are hard rules. Violating any of them is grounds for a PR rejection regardless
of how correct the logic is.

### 3.1 Follow the Existing Structure — Always

Before writing anything, read how the same pattern is handled elsewhere in the codebase.
If views use `APIView`, your new view uses `APIView`. If serializers inherit from a base
class, yours does too. If utilities live in `utils.py`, yours live there too.

**Do not introduce new patterns.** If you believe an existing pattern is inadequate,
raise it in the PR description and let the team decide — do not resolve it yourself.

Examples of what this means in practice:

- If the project uses `ModelViewSet`, do not switch to `APIView` for convenience.
- If response formatting goes through a shared serializer base class, use it.
- If pagination is configured globally, do not set it per-view unless explicitly instructed.
- If the project uses `snake_case` for URL parameter names, keep them `snake_case`.

### 3.2 Abstract Shared Logic — No Exceptions

Any piece of logic used in more than one place **must** be abstracted. This applies to:

- Business rules (e.g. "a speaker is eligible if…") → service function or manager method.
- Repeated queryset filters → model manager or utility function.
- Common validation logic → shared validator or mixin.
- Response shaping patterns → serializer mixin or base class.
- Permission patterns → custom permission class.

```python
# ❌ Wrong — logic duplicated across two views
class SpeakerListView(APIView):
    def get(self, request):
        speakers = Speaker.objects.filter(is_verified=True, is_available=True)
        ...

class EventSpeakerSuggestView(APIView):
    def get(self, request):
        speakers = Speaker.objects.filter(is_verified=True, is_available=True)
        ...

# ✅ Correct — abstracted into the manager
class SpeakerManager(models.Manager):
    def available(self):
        return self.filter(is_verified=True, is_available=True)

# Both views then call: Speaker.objects.available()
```

If you find yourself copying and pasting logic — stop. Abstract it first, then use it.

### 3.3 Clean Code is Not Optional

This project ships fast, but it ships clean. Speed is not an excuse for mess.

**Naming:**
- Names must be unambiguous and domain-accurate. `get_eligible_speakers()` is correct.
  `get_data()`, `process()`, or `handle()` are not acceptable.
- Do not abbreviate unless the abbreviation is universally understood (`id`, `url`, `pk`).
- Boolean fields and variables must read as questions: `is_verified`, `has_applied`,
  `can_be_contacted` — not `verified`, `applied`, `contactable`.

**Functions and methods:**
- A function does one thing. If you need an "and" to describe what it does, split it.
- Keep functions under 20 lines as a strong default. Longer functions require justification.
- Pure functions over stateful side effects wherever possible.

**Comments:**
- Do not comment *what* the code does — write code that is clear enough to not need it.
- Comment *why* when the reasoning is non-obvious: business rules, workarounds,
  external constraints.

```python
# ❌ Wrong
# Get the speaker
speaker = Speaker.objects.get(pk=pk)

# ✅ Correct (comment explains a non-obvious why)
# Speakers with pending applications are excluded here per product decision
# (ticket #142) — they appear in a separate endpoint.
queryset = Speaker.objects.exclude(applications__status="pending")
```

**Imports:**
- Group in order: stdlib → Django → DRF → third-party → local. No wildcard imports.
- Remove unused imports before committing. Every unused import is noise.

**Dead code:**
- Do not leave commented-out code in a PR. If it is not needed, delete it.
  Git history exists for a reason.

### 3.4 Scope Your Changes — Touch Only What the Task Requires

If a task says "add an availability filter to the speaker search endpoint", you touch:

- The view or viewset handling speaker search.
- The serializer if query params need to be validated.
- The manager or queryset if filter logic is abstracted there.
- The tests for the above.

You do **not** touch:

- Unrelated views that happen to use the `Speaker` model.
- The speaker `Profile` model if the task does not require it.
- URL configuration beyond what your new endpoint needs.
- Any other app unless the data flow explicitly requires it and the engineer has confirmed.

**If a change you need to make would ripple into a part of the codebase you were not
asked to touch, stop and flag it.** Do not silently extend your scope.

### 3.5 Tests Are Compulsory — Write Them Properly

There is no such thing as "I'll write tests later" or "the tests are passing" if the
tests you wrote do not meaningfully cover your changes.

**What comprehensive tests look like:**

```python
class SpeakerAvailabilityFilterTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_returns_only_available_speakers(self):
        """Only speakers marked available should appear in results."""
        available = SpeakerFactory(is_available=True)
        unavailable = SpeakerFactory(is_available=False)
        response = self.client.get(reverse("speaker-list"), {"available": "true"})
        ids = [s["id"] for s in response.data["results"]]
        self.assertIn(available.id, ids)
        self.assertNotIn(unavailable.id, ids)

    def test_unauthenticated_request_is_rejected(self):
        self.client.logout()
        response = self.client.get(reverse("speaker-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_filter_value_returns_400(self):
        response = self.client.get(reverse("speaker-list"), {"available": "maybe"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_result_returns_empty_list_not_error(self):
        response = self.client.get(reverse("speaker-list"), {"available": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)
```

**Test coverage requirements per change:**

| What you changed | What you must test |
|---|---|
| New endpoint | Happy path, unauthenticated, unauthorised role, invalid input, edge cases |
| Modified queryset / filter | Returns correct results, excludes incorrect results, empty set |
| New serializer field | Valid input, invalid input, read-only enforcement if applicable |
| Permission class | Each role that should be allowed, each role that should be denied |
| Utility / service function | Each branch, expected output, expected exceptions |
| Model method or property | Each condition the method handles |

**Tests must not be written to pass CI. They must be written to catch regressions.**
A test that asserts `response.status_code == 200` on every case is not a test —
it is noise. Assert the shape of the data, the content of the response, and the
correctness of the side effects.

---

## 4. When to Stop and Ask

Do not guess. Do not infer. Do not fill in the gaps with your own judgment.

**Stop and ask the engineer when:**

- The task description is ambiguous about behaviour in an edge case.
- Implementing the task requires modifying code outside your defined scope.
- You find an existing pattern that conflicts with what you have been asked to do.
- The data model does not support what is being asked without a migration or schema change.
- Two valid implementation approaches exist and the choice has meaningful trade-offs.
- You discover a bug in existing code while working on a task.
- You are unsure which existing abstraction (if any) your new code should extend.

**When you ask, be specific.** Do not say "I'm not sure how to proceed."
Say: "The task asks me to filter speakers by `expertise`, but the model has both a
`tags` M2M field and an `expertise` CharField. Which should this filter use?"

---

## 5. Git Discipline

### Branch naming

```
feature/<short-description>       # new functionality
fix/<short-description>           # bug fixes
chore/<short-description>         # non-functional changes (deps, config, docs)
refactor/<short-description>      # restructuring without behaviour change
test/<short-description>          # adding or fixing tests only
```

### Commit messages — Conventional Commits

Format: `<type>(<scope>): <imperative short description>`

```
feat(speakers): add availability filter to speaker list endpoint
fix(events): correct date validation for past event submissions
refactor(bookings): extract status transition logic to service layer
test(speakers): add edge case coverage for availability filter
chore(deps): upgrade djangorestframework to 3.15.1
```

Rules:
- Present tense, imperative mood: "add", not "added" or "adds".
- Scope is the Django app name or module being changed.
- Keep the subject line under 72 characters.
- If the commit needs more explanation, add a body after a blank line.
- **One logical change per commit.** Do not bundle unrelated changes.

### What a PR must contain

Every pull request must include:

1. A clear title following the commit convention.
2. A description of **what** was changed and **why**.
3. Notes on any non-obvious implementation decisions.
4. Confirmation that all existing tests pass.
5. New tests for every change made.
6. No unrelated changes — if you spotted something else while working, open a
   separate PR or file an issue.

---

## 6. Django & DRF Conventions

### Models

- All models inherit from the project's base model (check `core/` or `common/` for it).
- Use `verbose_name` and `verbose_name_plural` on every model's `Meta`.
- Add `__str__` to every model. It must return something human-readable and domain-meaningful.
- Custom queryset logic belongs in a `Manager` — not in views.
- Avoid `null=True` on string fields (`CharField`, `TextField`) — use `blank=True`
  and an empty string default instead. Only use `null=True` for non-string fields
  where `NULL` and empty carry different meanings.
- Every model that represents a user-created resource should have `created_at` and
  `updated_at` timestamp fields (the base model likely provides these already).

### Serializers

- Serializers belong in `serializers.py` inside the app they primarily represent.
- Separate read and write serializers if the shapes differ meaningfully.
- Validation logic specific to a field goes in `validate_<field_name>`.
- Cross-field validation goes in `validate()`.
- Never access `request` directly inside a serializer field. Pass context and
  access via `self.context["request"]` when necessary.
- Do not put business logic in serializers. A serializer validates and shapes data.
  Business logic belongs in a service function or model method.

### Views and ViewSets

- Use `get_queryset()` to build querysets — not inline in the action methods.
- Use `get_serializer_class()` when different actions require different serializers.
- Use `get_permissions()` when different actions require different permission sets.
- Do not put business logic in views. Views handle HTTP, delegate everything else.

```python
# ❌ Wrong — business logic in the view
class BookingCreateView(generics.CreateAPIView):
    def perform_create(self, serializer):
        speaker = serializer.validated_data["speaker"]
        if speaker.bookings.filter(date=serializer.validated_data["date"]).exists():
            raise ValidationError("Speaker is already booked on this date.")
        serializer.save()

# ✅ Correct — delegated to a service
class BookingCreateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # or call a service function like
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

### URLs

- Use `basename` when registering ViewSets with a router.
- Use named URLs everywhere. Hard-coded paths in code are not acceptable.
- URL parameter names must match the view's `lookup_field` and be consistent with
  the rest of the codebase (`speaker_id`, not `speakerId` or just `id`).

### Permissions

- Never rely on `IsAuthenticated` alone for endpoints that act on owned resources.
- Custom permission classes live in `permissions.py` inside the relevant app,
  or in `core/permissions.py` if they are reused across apps.
- Every permission class must have a `message` attribute set.

### Error Handling

- Use DRF's built-in exception classes (`ValidationError`, `PermissionDenied`,
  `NotFound`, `MethodNotAllowed`) — do not return raw `Response` objects with
  error dicts from views.
- Do not swallow exceptions silently. If you catch an exception and decide not to
  re-raise it, leave a comment explaining why.

---

## 7. API Design Conventions

- **REST semantics must be correct.** `GET` does not modify state. `POST` creates.
  `PATCH` partially updates. `PUT` fully replaces. `DELETE` removes.
- **Response shapes must be consistent.** Check how existing endpoints structure
  their responses and match them. Do not introduce a new response envelope format.
- **Use HTTP status codes correctly.** `200` for success, `201` for creation,
  `204` for no-content deletions, `400` for validation errors, `401` for
  unauthenticated, `403` for unauthorised, `404` for not found. Never return `200`
  with an error message in the body.
- **Pagination is default on list endpoints.** Do not turn it off unless the
  engineer explicitly asks you to and has a documented reason.
- **Filter parameters must be validated.** If an endpoint accepts query params,
  use a filter backend or validate params in the serializer — never pass raw
  query params directly to a queryset.

---

## 8. Security Practices

- **Never trust user-supplied data.** Validate everything through serializers or
  form inputs before it touches the database or business logic.
- **Never expose internal IDs where UUIDs or slugs should be used.** Check the
  existing pattern before adding a new resource identifier.
- **Never log sensitive data.** No passwords, tokens, email addresses, or PII
  in log statements.
- **Permissions must be set explicitly.** A view with no permission class is a
  security hole. Every view must declare its permissions.
- **Never write raw SQL** unless you have a documented performance justification
  and the engineer has approved it. Always prefer the ORM. If you do write raw
  SQL, use parameterised queries — no string formatting into queries, ever.
- **Environment variables for all secrets.** No hardcoded credentials, API keys,
  or secrets in any file that enters version control.

---

## 9. Performance Awareness

You are not expected to over-engineer for performance, but you are expected to
avoid obvious problems:

- **Select related and prefetch related.** Before returning a queryset that will
  be serialised with nested relationships, check whether `select_related()` or
  `prefetch_related()` is needed. N+1 queries are not acceptable in PR.
- **Do not load what you do not use.** If only three fields are needed from a
  queryset, use `.only()` or `.values()`.
- **Avoid queries in loops.** If you find yourself calling `Model.objects.get()`
  inside a `for` loop, stop and rethink.
- **Index awareness.** If you are filtering a model on a field that is not already
  indexed and the table is expected to grow large, flag it — do not silently add
  an index without the engineer's confirmation, but also do not silently ignore it.

---

## 10. Documentation Standards

- Every public function, method, and class must have a docstring.
- Docstrings describe *purpose* and *non-obvious behaviour* — not a restatement
  of the function signature.
- New endpoints must be documented in the inline API schema (drf-spectacular or
  whatever the project uses). Check the existing pattern.
- If you change the behaviour of an existing endpoint, update its documentation.

```python
# ❌ Wrong
def get_eligible_speakers(event):
    """Get eligible speakers for an event."""
    ...

# ✅ Correct
def get_eligible_speakers(event):
    """
    Return speakers who are eligible to be sourced for the given event.

    Eligibility requires: verified profile, available during the event date range,
    and no existing booking conflict. Speakers who have explicitly opted out of
    the event's topic category are excluded.
    """
    ...
```

---

## 11. The Fast-Paced Startup Contract

Working fast does not mean working carelessly. On this team, speed is achieved
through discipline — not through shortcuts that create debt.

| Practice | Expectation |
|---|---|
| **Small PRs** | A PR should be reviewable in under 20 minutes. If yours is not, split it. |
| **No WIP in main** | Never merge code that is not ready to run in production. |
| **Feature flags over long branches** | Long-lived branches create merging pain. Prefer feature flags for incremental work. |
| **Fail fast** | If a task turns out to be more complex than scoped, surface that early — not after three days of work. |
| **Self-review before PR** | Read your own diff before requesting review. Catch your own obvious issues first. |
| **No broken windows** | If you see a minor issue while working (bad variable name, missing docstring), fix it in a single separate commit. Do not let the codebase degrade incrementally. |
| **Ask early, not late** | A 5-minute question at the start of a task saves hours of rework at the end. |

---

## 12. Quick Reference — Pre-PR Checklist

Before you open a pull request, confirm every item:

- [ ] I have only touched files within the scope of this task.
- [ ] All new logic that is used in more than one place has been abstracted.
- [ ] All functions and classes follow the existing naming and structural conventions.
- [ ] No business logic lives in views or serializers — it has been moved to services or model methods.
- [ ] Every new function and class has a docstring.
- [ ] Unused imports have been removed.
- [ ] No commented-out code has been left behind.
- [ ] All new endpoints declare explicit permission classes.
- [ ] No N+1 query issues have been introduced.
- [ ] Tests have been written for every change — not to pass CI, but to cover behaviour.
- [ ] All existing tests still pass.
- [ ] The PR description explains what was changed and why.
- [ ] I have not made any decisions I was not explicitly asked to make.

---

*Last updated: July 2025. This document should be updated whenever the team agrees
on a new convention. If something here conflicts with current practice in the codebase,
raise it — do not silently follow the old pattern or silently ignore this document.*
