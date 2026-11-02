"""Management command to revoke or reset a speaker's badge."""

from django.core.management.base import BaseCommand

from badges.choices import BadgeStatusChoices
from badges.models import BadgeDefinition, SpeakerBadge
from profiles.models.speaker_models import SpeakerProfile


class Command(BaseCommand):
    """Command to revoke or reset speaker badges for re-testing."""

    help = "Revoke or reset a speaker badge back to eligible or locked state."

    def add_arguments(self, parser):
        """Configure command line arguments."""
        parser.add_argument(
            "--speaker",
            type=str,
            required=True,
            help="Speaker username or slug (e.g., kwaku or ahenkan-kwaku)",
        )
        parser.add_argument(
            "--token-id",
            type=int,
            default=1,
            help="Badge token ID (1 to 6). Default: 1",
        )
        parser.add_argument(
            "--status",
            type=str,
            default="eligible",
            choices=["eligible", "locked"],
            help="New status after revoking: eligible or locked (default: eligible)",
        )

    def handle(self, *args, **options):
        """Execute command logic to update badge status."""
        speaker_ident = options["speaker"]
        token_id = options["token_id"]
        target_status = options["status"]

        speaker = (
            SpeakerProfile.objects.filter(slug=speaker_ident).first()
            or SpeakerProfile.objects.filter(
                user_account__username=speaker_ident
            ).first()
        )

        if not speaker:
            self.stderr.write(self.style.ERROR(f"Speaker '{speaker_ident}' not found."))
            return

        badge_def = BadgeDefinition.objects.filter(token_id=token_id).first()
        if not badge_def:
            self.stderr.write(
                self.style.ERROR(
                    f"Badge definition with token_id {token_id} not found."
                )
            )
            return

        speaker_badge = SpeakerBadge.objects.filter(
            speaker=speaker, badge=badge_def
        ).first()
        if not speaker_badge:
            self.stderr.write(
                self.style.ERROR(
                    f"No badge record found for {speaker} and badge #{token_id}."
                )
            )
            return

        old_status = speaker_badge.status
        old_tx = speaker_badge.tx_hash

        speaker_badge.status = (
            BadgeStatusChoices.ELIGIBLE
            if target_status == "eligible"
            else BadgeStatusChoices.LOCKED
        )
        speaker_badge.tx_hash = None
        speaker_badge.recipient_address = None
        speaker_badge.claimed_at = None
        speaker_badge.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Revoked badge '{badge_def.name}' (#{token_id}) for {speaker.user_account.username}.\n"
                f"   Previous status: {old_status} (tx: {old_tx or 'None'})\n"
                f"   New status: {speaker_badge.status} (ready to test claiming again!)"
            )
        )
