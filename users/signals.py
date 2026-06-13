"""Signal handlers for the users app."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import User


@receiver(post_save, sender=User)
def create_speaker_profile_for_new_user(sender, instance, created, **kwargs):
    """Create a SpeakerProfile automatically when a new User is created."""
    if created:
        from speakers.models import SpeakerProfile

        SpeakerProfile.objects.get_or_create(user_account=instance)
