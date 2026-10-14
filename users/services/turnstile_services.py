"""Cloudflare Turnstile verification used to block automated signups."""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TURNSTILE_TIMEOUT_SECONDS = 5


def verify_turnstile_token(token: str | None, remote_ip: str | None = None) -> bool:
    """Return True when Cloudflare confirms the Turnstile token is valid.

    When ``TURNSTILE_SECRET_KEY`` is not configured the check is skipped so
    local development and tests work without Cloudflare. If the configured
    check cannot be completed (missing token or Cloudflare unreachable) the
    request is rejected.
    """
    secret = getattr(settings, "TURNSTILE_SECRET_KEY", "")
    if not secret:
        return True
    if not token:
        return False

    payload = {"secret": secret, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        response = requests.post(
            TURNSTILE_VERIFY_URL, data=payload, timeout=TURNSTILE_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return bool(response.json().get("success"))
    except (requests.RequestException, ValueError):
        logger.exception("Turnstile verification request failed")
        return False
