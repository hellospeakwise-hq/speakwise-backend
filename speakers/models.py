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


class SpeakerExperiences(TimeStampedModel):
    """speaker experience model.
    This model holds speaker's presentation or speaking experiences.
    """

    event_name = models.CharField(max_length=255, null=True,help_text="Name of the event")
    event_date = models.DateField(help_text="Date of the event", auto_now=True)
    topic = models.CharField(max_length=255, null=True,help_text="Topic presented")
    description = models.TextField(
        null=True, help_text="A brief description of the experience"
    )
    presentation_link = models.URLField(
        null=True, help_text="Link to slides of the presentation or talk"
    )
    video_recording_link = models.URLField(
        null=True, help_text="Link to the video recording of the talk"
    )

    def __str__(self):
        """String representation of the speaker experience."""
        return f"{self.event_name} - {self.topic}"


class SpeakerProfile(TimeStampedModel):
    """speakers model."""

    user_account = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="speakers_profile_user"
    )
    events_spoken = models.ForeignKey("events.Event", on_delete=models.DO_NOTHING,null=True, related_name="speakers")
    organization = models.CharField(max_length=255, blank=True)
    short_bio = models.CharField(max_length=255, blank=True)
    long_bio = models.TextField(null=True)
    country = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to=SPEAKERS_UPLOAD_DIR, blank=True)
    skill_tag = models.ManyToManyField(
        SpeakerSkillTag, blank=True, related_name="speakers_profile_skill_tags"
    )
    experiences = models.ManyToManyField(
        SpeakerExperiences, blank=True, related_name="speakers_profile_experiences"
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
