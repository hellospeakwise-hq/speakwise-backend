"""Migration tests for the profile ownership de-duplication."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader
from django.test import TransactionTestCase
from django.utils import timezone

from profiles.models.organization_models import OrganizationProfile
from profiles.models.speaker_models import SpeakerFollow, SpeakerProfile


class ProfileDeDuplicationMigrationTests(TransactionTestCase):
    """Seed duplicate profiles, then verify the de-dup migration handles them."""

    migrate_from = [("profiles", "0021_alter_organizationprofile_cfps_and_more")]
    migrate_to = [("profiles", "0023_alter_organizationprofile_owner_and_more")]

    def test_duplicate_profiles_are_collapsed_to_the_latest_one(self):
        """Rolling to 0021, seeding duplicates, then migrating up de-dupes."""
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)

        old_apps = executor.loader.project_state(self.migrate_from).apps
        OldOrganizationProfile = old_apps.get_model("profiles", "OrganizationProfile")
        OldSpeakerProfile = old_apps.get_model("profiles", "SpeakerProfile")
        OldSpeakerFollow = old_apps.get_model("profiles", "SpeakerFollow")

        self.user = get_user_model().objects.create(
            username="dupe_user", email="dupe@example.com", password="password123"
        )
        self.follower = get_user_model().objects.create(
            username="follower", email="f@example.com", password="password123"
        )

        OldOrganizationProfile.objects.create(name="Old Org", owner_id=self.user.pk)
        OldOrganizationProfile.objects.create(name="New Org", owner_id=self.user.pk)
        OldOrganizationProfile.objects.filter(name="Old Org").update(
            updated_at=timezone.now() - timezone.timedelta(days=1)
        )
        OldSpeakerProfile.objects.create(
            user_account_id=self.user.pk,
            short_bio="keep me",
            slug="survivor-speaker",
        )
        loser_speaker = OldSpeakerProfile.objects.create(
            user_account_id=self.user.pk,
            short_bio="drop me",
            slug="loser-speaker",
        )
        OldSpeakerProfile.objects.filter(pk=loser_speaker.pk).update(
            updated_at=timezone.now() - timezone.timedelta(days=1)
        )
        OldSpeakerFollow.objects.create(
            follower_id=self.follower.pk, speaker_id=loser_speaker.pk
        )

        executor.loader = MigrationLoader(connection, ignore_no_migrations=True)
        executor.migrate(self.migrate_to)

        self._assert_single_survivor()

    def _assert_single_survivor(self):
        """Assert the post-migration state: one profile each, survivors intact."""
        remaining_speakers = SpeakerProfile.objects.filter(user_account=self.user)
        self.assertEqual(remaining_speakers.count(), 1)
        self.assertEqual(remaining_speakers.first().short_bio, "keep me")

        remaining_orgs = OrganizationProfile.objects.filter(owner=self.user)
        self.assertEqual(remaining_orgs.count(), 1)
        self.assertEqual(remaining_orgs.first().name, "New Org")

        profile = SpeakerProfile.objects.get(user_account=self.user)
        self.assertTrue(
            SpeakerFollow.objects.filter(
                follower=self.follower, speaker=profile
            ).exists()
        )

        with self.assertRaises(IntegrityError):
            SpeakerProfile.objects.create(user_account=self.user)
        with self.assertRaises(IntegrityError):
            OrganizationProfile.objects.create(name="Third Org", owner=self.user)
