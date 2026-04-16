# System Permissions Review: Stress Test Report

I’ve reviewed your permissions architecture, and honestly, it's a structural mess. If this goes into production, your system is Swiss cheese. You asked me not to sugarcoat it, so here is why your implementation is weak and exactly how to fix it to make it bulletproof.

## 🚨 CRITICAL VULNERABILITY 1: Wide Open by Default
Your DRF configuration in `speakwise/settings/base.py` is missing `DEFAULT_PERMISSION_CLASSES`.
- **The Flaw:** By default, DRF uses `AllowAny`. This means any view or viewset that neglects to explicitly declare `permission_classes` is fully open to unauthenticated users. This is a massive rookie mistake. You are currently opting **into** security rather than opting **out**.
- **The Fix:** Set the global default to `IsAuthenticated` so that if a developer forgets to add permissions to a new endpoint, the default behavior is secure.
```python
REST_FRAMEWORK = {
    ...
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
```

## 🚨 CRITICAL VULNERABILITY 2: Custom Permissions Are Broken
Look at `base/permissions.py`. Every single custom permission (e.g., `IsOrganizationAdmin`, `IsOrganizationMember`) only implements `has_object_permission`. None of them implement `has_permission`.
- **The Flaw:** `BasePermission` unconditionally returns `True` for `has_permission`. By missing this method, your custom classes grant view-level access to **absolutely everyone**.
- **The Proof:** In `events/views.py` (`EventListView.post`), you try to restrict event creation by returning `[IsOrganizationAdmin()]`. Because that class lacks `has_permission`, `IsOrganizationAdmin().has_permission()` evaluates to `True`. **Anyone can POST and create an event right now.**
- **The Fix:** Implement `has_permission` in all your custom permissions. If a permission requires an object, you often need `IsAuthenticated` at the view level first.

## 🚨 CRITICAL VULNERABILITY 3: Bypassing DRF and Hardcoding Security
Because your custom object permissions are broken and confusing to use, you've started hardcoding security checks directly into the view logic.
- **The Flaw:** In `organizations/views.py`, you manually call `self.check_object_permissions(request, organization)` repeatedly. In `events/views.py` (`EventDetailView`), you forgot to call it entirely and resorted to writing manual `if`/`else` membership logic inside the `patch` and `delete` methods:
```python
# From EventDetailView.patch
if event.organizer:
    membership = OrganizationMembership.objects.filter(...)
    if not membership or not membership.is_admins():
        raise PermissionDenied("...")
```
- **The Verdict:** This defeats the entire purpose of DRF permission classes. It's unmaintainable, copy-pasted trash. If you change a generic organization permission rule later, you'll have to hunt through every view method manually.
- **The Fix:** Build a proper, generic `IsEventOrganizationAdmin` permission class and use it natively in the `permission_classes` array. Let DRF handle the object checks seamlessly.

## ❌ VULNERABILITY 4: Missing Permissions on Sensitive Views
Because of Vulnerability 1 (AllowAny by default), several views are mistakenly public:
- `UserLogoutView` in `users/views.py`: `permission_classes` is missing entirely. Unauthenticated users can hit this endpoint.
- `LoginBaseClass` / `UserLoginView`: While it should technically be public, relying on the missing global default is poor practice. Make it explicitly `[AllowAny]`.

## ❌ VULNERABILITY 5: No Generic "IsOwner" Permission
In `speakers/views.py` and `talks/views.py`, you manually check ownership logic in the endpoints:
```python
if speaker_profile.user_account != request.user:
    raise PermissionDenied(...)
```
- **The Flaw:** Repeating this logic in multiple places ensures someone will eventually forget it.
- **The Fix:** Write a generic `IsOwnerOrReadOnly` or `IsOwnerProfile` in `base/permissions.py`. Apply it via `permission_classes`. Stop writing imperative security checks inside your generic views.

## 🛠️ Your Action Plan
1. Set the global default to `IsAuthenticated` in `base.py`.
2. Rewrite `base/permissions.py` to correctly implement `has_permission` (or compose permissions properly like `IsAuthenticated & IsOrganizationAdmin`).
3. Strip out the manual `if/else` permission checks in `events/views.py`, `speakers/views.py`, and `organizations/views.py`, and replace them with properly functioning DRF permission classes.

Stop duct-taping your security layer. Go fix the foundation. Let me know if you are ready to start patching these.
