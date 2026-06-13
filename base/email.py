"""Shared email sending utility with retry logic and structured logging."""

import logging
from functools import wraps

from django.conf import settings
from django.core.mail import send_mail as django_send_mail

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries=2, delay=2):
    """Decorator: retry a function with exponential backoff on failure."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait = delay * (2**attempt)
                        logger.warning(
                            "Retrying %s after %.1fs (attempt %d/%d)",
                            func.__name__,
                            wait,
                            attempt + 1,
                            max_retries,
                            exc_info=True,
                        )
                        time.sleep(wait)
            raise last_exception

        return wrapper

    return decorator


@retry_on_failure(max_retries=2, delay=2)
def send_email(
    subject: str,
    plain_body: str,
    html_body: str | None,
    recipient: str,
    from_email: str | None = None,
) -> None:
    """Send an email with retry logic and structured logging."""
    django_send_mail(
        subject=subject,
        message=plain_body,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        html_message=html_body,
        fail_silently=False,
    )
    logger.info(
        "Email sent",
        extra={"recipient": recipient, "subject": subject},
    )
