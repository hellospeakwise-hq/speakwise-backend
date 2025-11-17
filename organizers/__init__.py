"""Compatibility shim package for legacy imports.

This package exists to keep imports like `from organizers.models import ...`
working while the authoritative Django app remains `organizations`.

Do NOT add this package to INSTALLED_APPS. It only re-exports symbols.
"""
