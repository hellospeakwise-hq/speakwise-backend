"""Service module for handling email operations in the users application."""

import logging

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for sending emails, particularly password reset emails."""

    @staticmethod
    def send_password_reset_email(user, request=None):
        """Send a password reset email to the user.

        Args:
            user: The User object to send the email to.
            request: The HTTP request object (optional).

        Returns:
            str: The generated token for the password reset.

        Raises:
            Exception: If email sending fails.
        """
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        subject = (
            f"Password Reset Request - {getattr(settings, 'SITE_NAME', 'SpeakWise')}"
        )
        message = f"Hi {user.username},\n\nClick the link below to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email."
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )

            logger.info(f"Password reset email sent successfully to user ID: {user.id}")

        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {e}")
            raise

        return token
