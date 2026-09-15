"""User background tasks for email notifications."""

import logging

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_tasks import task

logger = logging.getLogger(__name__)

FRONTEND_URL = getattr(settings, "FRONTEND_URL", "https://speak-wise.live")


@task()
def send_otp_email_task(user_id, otp_code) -> None:
    """Send the email verification OTP code to the user.

    The plaintext code is passed to this task rather than read from the
    database, because only the hash is stored. It must never be logged.

    Args:
        user_id: The ID of the User instance.
        otp_code: The plaintext one-time password to deliver.
    """
    from users.models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error("User with id %s not found for OTP email", user_id)
        return

    html_message = render_to_string(
        "emails/otp.html",
        {
            "user_name": user.first_name or user.username,
            "otp_code": otp_code,
            "expiry_minutes": settings.OTP_EXPIRY_MINUTES,
            "site_name": getattr(settings, "SITE_NAME", "SpeakWise"),
        },
    )

    try:
        send_mail(
            subject=f"Your {getattr(settings, 'SITE_NAME', 'SpeakWise')} verification code",
            message=(
                f"Hi {user.first_name or user.username},\n\n"
                f"Your verification code is: {otp_code}\n\n"
                f"This code expires in {settings.OTP_EXPIRY_MINUTES} minutes "
                "and can only be used once.\n\n"
                "If you did not request this code, you can safely ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("OTP email sent to user ID: %s", user.id)
    except Exception as e:
        logger.error("Failed to send OTP email to %s: %s", user.email, e)


@task()
def send_welcome_email_task(user_id) -> None:
    """Send welcome email after user registration.

    Args:
        user_id: The ID of the User instance (UUID or int).
    """
    from users.models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error("User with id %s not found", user_id)
        return

    role = "speaker"
    dashboard_url = f"{FRONTEND_URL}/dashboard/speaker"

    html_message = render_to_string(
        f"emails/welcome_{role}.html",
        {
            "user_name": user.first_name or user.username,
            "dashboard_url": dashboard_url,
        },
    )

    try:
        send_mail(
            subject="Welcome to SpeakWise!",
            message=(
                f"Hi {user.first_name or user.username},\n\n"
                "Welcome to SpeakWise! Your account is ready.\n\n"
                f"Get started: {dashboard_url}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Welcome email sent to user ID: %s", user.id)
    except Exception as e:
        logger.error("Failed to send welcome email to %s: %s", user.email, e)


@task()
def send_password_reset_email_task(user_id) -> str:
    """Send password reset email to the user.

    Args:
        user_id: The ID of the User instance (UUID or int).

    Returns:
        The generated token for the password reset.
    """
    from users.models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error("User with id %s not found", user_id)
        return ""

    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)

    reset_url = f"{FRONTEND_URL}/reset-password?token={token}&email={user.email}"

    html_message = render_to_string(
        "emails/password_reset.html",
        {
            "user_name": user.first_name or user.username,
            "reset_url": reset_url,
        },
    )

    try:
        send_mail(
            subject=f"Password Reset Request - {getattr(settings, 'SITE_NAME', 'SpeakWise')}",
            message=(
                f"Hi {user.first_name or user.username},\n\n"
                f"Click the link below to reset your password:\n{reset_url}\n\n"
                "If you did not request this, you can safely ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Password reset email sent to user ID: %s", user.id)
    except Exception as e:
        logger.error("Failed to send password reset email to %s: %s", user.email, e)

    return token
