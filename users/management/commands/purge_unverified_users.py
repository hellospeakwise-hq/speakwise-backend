"""Management command to remove stale, never-verified accounts."""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from users.models import User
from users.services.auth_services import stale_unverified_users, write_users_csv


class Command(BaseCommand):
    """Delete accounts that signed up but never verified their email."""

    help = (
        "List (default) or delete users who never verified their email and "
        "never logged in. Staff, superusers, organization owners, event "
        "submitters and verified users are never touched. Pass --delete to "
        "remove them; a CSV backup of the removed accounts is written first."
    )

    def add_arguments(self, parser):
        """Register command options."""
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Only include accounts created more than this many days ago.",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete the matching accounts. Without it this is a dry run.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip the interactive confirmation prompt.",
        )

    def handle(self, *args, **options):
        """Report matching accounts and delete them when --delete is set."""
        queryset = stale_unverified_users(options["days"])
        count = queryset.count()

        if not options["delete"]:
            for email in queryset.values_list("email", flat=True)[:20]:
                self.stdout.write(f"  {email}")
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {count} unverified account(s) would be deleted. "
                    "Re-run with --delete to remove them."
                )
            )
            return

        if count == 0:
            self.stdout.write("Nothing to delete.")
            return

        backup_path = self._write_backup(queryset)
        self.stdout.write(f"Backup of {count} account(s) written to {backup_path}")

        if not options["yes"]:
            answer = input(f"Permanently delete {count} account(s)? Type 'yes': ")
            if answer.strip().lower() != "yes":
                raise CommandError("Aborted. No accounts were deleted.")

        user_ids = list(queryset.values_list("pk", flat=True))
        deleted, _ = User.objects.filter(pk__in=user_ids).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} record(s)."))

    def _write_backup(self, queryset) -> Path:
        """Write the accounts about to be deleted to a timestamped CSV file."""
        stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
        path = Path(f"purged_unverified_users_{stamp}.csv")
        with path.open("w", newline="") as handle:
            write_users_csv(handle, queryset)
        return path
