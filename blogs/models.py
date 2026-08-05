"""Blogs app models."""

import uuid

from django.conf import settings
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

from base.models import TimeStampedModel

BLOG_IMAGE_UPLOAD = "blog_images/"


class Blog(TimeStampedModel):
    """A blog post in the SpeakWise application."""

    class Status(models.TextChoices):
        """Blog status choices."""

        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to=BLOG_IMAGE_UPLOAD, null=True, blank=True)
    title = models.CharField(max_length=255)
    short_description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Short summary shown on cards.",
    )
    full_description = CKEditor5Field(
        blank=True,
        default="",
        help_text="Full blog content. Rich text (HTML) supported.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blogs",
        help_text="The user who created the blog post.",
    )
    published_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    class Meta:
        """Meta options for the Blog model."""

        verbose_name = "Blog"
        verbose_name_plural = "Blogs"
        ordering = ["-published_date", "-created_at"]
        unique_together = (("created_by", "title"),)

    def __str__(self):
        """Return a string representation of the model."""
        return self.title
