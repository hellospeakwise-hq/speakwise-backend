"""Service layer for feedback business logic.

Keeps the views and serializers thin by owning the domain rules around
experience resolution, the date gate, per-IP submission cooldowns, QR payload
building, and the aggregate summary shown on speaker profiles.
"""

import hashlib
import hmac
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from feedbacks.models import RATING_FIELDS, Feedback
from profiles.models.speaker_models import SpeakerExperiences, SpeakerProfile

RATING_BUCKETS = 10


def resolve_feedback_experience(feedback_slug: str):
    """Return the experience matching ``feedback_slug``, or None.

    Selects the linked event and the owning speaker so date gating and owner
    checks do not trigger extra queries.
    """
    try:
        return SpeakerExperiences.objects.select_related(
            "event", "speaker__user_account"
        ).get(feedback_slug=feedback_slug)
    except SpeakerExperiences.DoesNotExist:
        return None


def is_feedback_open(experience, now=None) -> bool:
    """Return whether feedback may be submitted for an experience right now.

    Feedback opens on the day the presentation happened. When the experience
    links to an event listed on this platform, its start time is authoritative;
    otherwise the experience's own event date is used.
    """
    now = now or timezone.now()
    if experience.event_id and experience.event.start_date_time is not None:
        return now >= experience.event.start_date_time
    return timezone.localdate() >= experience.event_date


def submitted_recently_by_ip(experience, submitter_ip_hash: str, now=None) -> bool:
    """Return whether this IP already gave feedback for the experience recently.

    Prevents the same attendee from repeatedly re-submitting for the same
    presentation within ``FEEDBACK_IP_COOLDOWN_MINUTES``. Only a hash of the IP
    is compared; the raw IP is never stored or logged.
    """
    now = now or timezone.now()
    cutoff = now - timedelta(minutes=settings.FEEDBACK_IP_COOLDOWN_MINUTES)
    return Feedback.objects.filter(
        experience=experience,
        submitter_ip_hash=submitter_ip_hash,
        created_at__gte=cutoff,
    ).exists()


def hash_submitter_ip(ip: str) -> str:
    """Return a salted SHA-256 hash of the submitter's IP address."""
    return hmac.new(
        settings.SECRET_KEY.encode(), ip.encode(), hashlib.sha256
    ).hexdigest()


def build_feedback_qr_payload(feedback_slug: str) -> str:
    """Return the audience-facing URL the QR code should encode."""
    host = settings.FRONTEND_URL.rstrip("/")
    return f"{host}/feedback/{feedback_slug}"


def build_feedback_summary(speaker: SpeakerProfile) -> dict:
    """Return aggregate ratings for a speaker across all their feedback.

    Produces ``total_count`` and, for every rating criterion, a rounded average
    plus a 1..10 count distribution, from a single database query.
    """
    rows = Feedback.objects.filter(speaker=speaker).values_list(*RATING_FIELDS)
    summary = {"total_count": len(rows)}
    for field in RATING_FIELDS:
        distribution = {str(i): 0 for i in range(1, RATING_BUCKETS + 1)}
        total = 0
        for row in rows:
            value = row[RATING_FIELDS.index(field)]
            distribution[str(value)] += 1
            total += value
        average = round(total / len(rows), 1) if rows else None
        summary[field] = {"average": average, "distribution": distribution}
    return summary
