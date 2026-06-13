"""Service module for handling email operations in the users application."""

import logging

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string

from base.constants import FRONTEND_URL, SITE_NAME
from base.email import send_email

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for sending emails."""

    @staticmethod
    def send_welcome_email(user) -> None:
        """Send a role-specific welcome email after registration."""
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
            send_email(
                subject="Welcome to SpeakWise!",
                plain_body=(
                    f"Hi {user.first_name or user.username},\n\n"
                    "Welcome to SpeakWise! Your account is ready.\n\n"
                    f"Get started: {dashboard_url}"
                ),
                html_body=html_message,
                recipient=user.email,
            )
            logger.info("Welcome email sent to user ID: %s", user.id)
        except Exception as e:
            logger.error("Failed to send welcome email to %s: %s", user.email, e)

    @staticmethod
    def send_password_reset_email(user, request=None):
        """Send a password reset email to the user.

        Returns:
            str: The generated token for the password reset.
        """
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)

        reset_url = f"{FRONTEND_URL}/reset-password"

        html_message = render_to_string(
            "emails/password_reset.html",
            {
                "user_name": user.first_name or user.username,
                "reset_url": reset_url,
                "reset_code": token,
                "reset_email": user.email,
            },
        )

        try:
            send_email(
                subject=f"Password Reset Request - {SITE_NAME}",
                plain_body=(
                    f"Hi {user.first_name or user.username},\n\n"
                    f"A password reset was requested for your account.\n\n"
                    f"Your reset code: {token}\n\n"
                    f"To reset your password, go to: {reset_url}\n"
                    f"and enter your email ({user.email}) along with the code above.\n\n"
                    "If you did not request this, you can safely ignore this email."
                ),
                html_body=html_message,
                recipient=user.email,
            )
            logger.info("Password reset email sent to user ID: %s", user.id)
        except Exception as e:
            logger.error("Failed to send password reset email to %s: %s", user.email, e)

        return token
