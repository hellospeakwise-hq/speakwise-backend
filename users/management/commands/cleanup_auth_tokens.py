"""Management command to purge used or expired auth codes."""

from django.core.management.base import BaseCommand

from users.services.otp_services import purge_expired_auth_tokens


class Command(BaseCommand):
    """Purge used or expired OTP and OAuth exchange codes."""

    help = (
        "Delete OTP and OAuth exchange codes that are used or expired, so the "
        "tables do not grow without bound. Intended to be scheduled to run "
        "periodically (e.g. daily) alongside purge_expired_auth_tokens_task."
    )

    def handle(self, *args, **options):
        """Run the purge and report how many codes were removed."""
        purged = purge_expired_auth_tokens()
        self.stdout.write(self.style.SUCCESS(f"Purged {purged} auth code(s)."))
