"""Consistent JSON error envelope for the API.

DRF renders API-raised exceptions as JSON, but Django's default 404/500
handlers render HTML. This handler keeps every /api/* error in one shape:
{"detail": ..., "code": ...} so clients never have to parse HTML.
"""

from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Return a client-safe JSON error response.

    Preserves field-level validation errors ({field: [messages]}) while
    normalising generic errors to {"detail": ..., "code": ...} so API
    clients never have to parse HTML error pages when DEBUG=False.
    """
    response = exception_handler(exc, context)
    if response is not None:
        code = getattr(exc, "default_code", "error")
        data = response.data
        if isinstance(data, dict) and "detail" in data and len(data) == 1:
            response.data = {"detail": data["detail"], "code": code}
        elif isinstance(data, dict):
            # Field validation errors: keep per-field messages, add a code.
            response.data = {"code": code, **data}
        return response
    return None
