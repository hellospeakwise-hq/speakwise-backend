"""speakers models."""

from django.db import models

from base.models import SocialLinks, TimeStampedModel
from users.models import User

# Speakers file upload directory
SPEAKERS_UPLOAD_DIR = "speakers/avatars/"


class SpeakerSkillTag(TimeStampedModel):
    """speaker skill tag."""

    name = models.CharField(
        max_length=255, null=True, help_text="name of skill. Eg. Software Engineer"
    )
    description = models.TextField(
        null=True, help_text="A brief description of the skill"
    )
    duration = models.PositiveIntegerField(null=True, help_text="years of experience")

    def __str__(self):
        """String representation of the speaker skill."""
        return self.name


class SpeakerProfile(TimeStampedModel):
    """speakers model."""

    user_account = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="speakers_profile_user"
    )
    # TODO: events_spoken = models.ManyToManyField(Event, blank=True, related_name="speakers")
    organization = models.CharField(max_length=255, blank=True)
    short_bio = models.CharField(max_length=255, blank=True)
    long_bio = models.TextField(null=True)
    country = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to=SPEAKERS_UPLOAD_DIR, blank=True)
    skill_tag = models.ManyToManyField(
        SpeakerSkillTag, blank=True, related_name="speakers_profile_skill_tags"
    )

    def __str__(self):
        """String representation of the speaker profile."""
        return self.user_account.username


class SpeakerSocialLinks(SocialLinks):
    """speaker social link model."""

    speaker = models.ForeignKey(
        SpeakerProfile, on_delete=models.CASCADE, related_name="social_links"
    )

    def __str__(self):
        """String rep of speakwise social."""
        return self.name
