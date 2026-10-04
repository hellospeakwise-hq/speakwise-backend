"""Management command to close expired event CFPs."""

from django.core.management.base import BaseCommand

from events.tasks import close_expired_cfp_events


class Command(BaseCommand):
    """Close CFP submissions on events whose deadline has passed."""

    help = (
        "Close CFPs for events whose cfp_deadline has passed while cfp_open "
        "is still True. Intended to be scheduled to run once every 24 hours."
    )

    def handle(self, *args, **options):
        """Run the close-expired-CFP routine and report how many were closed."""
        closed = close_expired_cfp_events()
        self.stdout.write(self.style.SUCCESS(f"Closed {closed} expired CFP(s)."))
