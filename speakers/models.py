"""speakers models."""

from itertools import count

from django.db import models
from django.utils.text import slugify

from base.models import SocialLinks, TimeStampedModel
from users.models import User

# Speakers file upload directory
SPEAKERS_UPLOAD_DIR = "speakers/avatars/"


class SpeakerSkillTag(TimeStampedModel):
    """speaker skill tag."""

    name = models.CharField(
        max_length=255, null=True, help_text="name of skill. Eg. Software Engineer"
    )  # Consider making this non-nullable if a skill must have a name.
    description = models.TextField(
        blank=True, null=True, help_text="A brief description of the skill"
    )
    duration = models.PositiveIntegerField(null=True, help_text="years of experience")
    speaker = models.ForeignKey(
        "speakers.SpeakerProfile",
        on_delete=models.DO_NOTHING,
        related_name="skill_tags",
        null=True,
    )

    def __str__(self):
        """String representation of the speaker skill."""
        return self.name


class SpeakerExperiences(TimeStampedModel):
    """speaker experience model.
    This model holds speaker's presentation or speaking experiences.
    """

    event_name = models.CharField(
        max_length=255, null=True, help_text="Name of the event"
    )
    event_date = models.DateField(help_text="Date of the event")
    topic = models.CharField(max_length=255, null=True, help_text="Topic presented")
    description = models.TextField(
        blank=True, null=True, help_text="A brief description of the experience"
    )
    presentation_link = models.URLField(
        blank=True, null=True, help_text="Link to slides of the presentation or talk"
    )
    video_recording_link = models.URLField(
        blank=True, null=True, help_text="Link to the video recording of the talk"
    )
    speaker = models.ForeignKey(
        "speakers.SpeakerProfile",
        null=True,
        on_delete=models.CASCADE,
        related_name="experiences",
    )

    def __str__(self):
        """String representation of the speaker experience."""
        return f"{self.event_name} - {self.topic}"


class SpeakerProfile(TimeStampedModel):
    """speakers model."""

    user_account = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="speakers_profile_user"
    )
    events_spoken = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="speakers",
    )
    organization = models.CharField(max_length=255, blank=True)
    short_bio = models.CharField(max_length=255, blank=True)
    long_bio = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to=SPEAKERS_UPLOAD_DIR, blank=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        """String representation of the speaker profile."""
        return self.user_account.username

    def _base_slug(self) -> str:
        """Build a base slug from available user info with sensible fallbacks."""
        first = (self.user_account.first_name or "").strip()
        last = (self.user_account.last_name or "").strip()
        name = f"{first} {last}".strip()
        if s := slugify(name):
            return s
        if s := slugify(self.user_account.username):
            return s
        return str(self.user_account.id)

    def _generate_unique_slug(self) -> str:
        """Generate a unique slug, appending numeric suffix when needed."""
        base = self._base_slug()
        candidate = base
        for i in count(2):
            exists = (
                SpeakerProfile.objects.filter(slug=candidate)
                .exclude(pk=self.pk)
                .exists()
            )
            if not exists:
                return candidate
            candidate = f"{base}-{i}"
        return "default-slug"

    def save(self, *args, **kwargs):
        """Set slug once when empty and keep it stable across updates."""
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    @property
    def skill_tag(self):
        """Compatibility alias: access reverse FK manager as `skill_tag`.
        Tests expect `speaker_profile.skill_tag` to behave like a related manager.
        """
        return self.skill_tags


class SpeakerSocialLinks(SocialLinks):
    """speaker social link model."""

    speaker = models.ForeignKey(
        SpeakerProfile, on_delete=models.CASCADE, related_name="social_links"
    )

    def __str__(self):
        """String rep of speakwise social."""
        return self.name
