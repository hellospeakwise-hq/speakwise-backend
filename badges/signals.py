"""Signals for automatically evaluating speaker badges upon platform activity."""

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from feedbacks.models import Feedback
from profiles.models.speaker_models import SpeakerExperiences
from speakerrequests.models import SpeakerRequest


@receiver(post_save, sender=SpeakerExperiences)
def evaluate_badges_on_experience_save(sender, instance, created, **kwargs):
    """Re-evaluate speaker badges when an experience/talk is added or updated."""
    if not instance.speaker:
        return
    from badges.services import evaluate_speaker_badges

    transaction.on_commit(lambda: evaluate_speaker_badges(instance.speaker))


@receiver(post_delete, sender=SpeakerExperiences)
def evaluate_badges_on_experience_delete(sender, instance, **kwargs):
    """Re-evaluate speaker badges when an experience/talk is deleted."""
    if not instance.speaker:
        return
    from badges.services import evaluate_speaker_badges

    transaction.on_commit(lambda: evaluate_speaker_badges(instance.speaker))


@receiver(post_save, sender=Feedback)
def evaluate_badges_on_feedback_save(sender, instance, created, **kwargs):
    """Re-evaluate speaker badges when new attendee feedback arrives."""
    if not instance.speaker:
        return
    from badges.services import evaluate_speaker_badges

    transaction.on_commit(lambda: evaluate_speaker_badges(instance.speaker))


@receiver(post_save, sender=SpeakerRequest)
def evaluate_badges_on_request_save(sender, instance, created, **kwargs):
    """Re-evaluate speaker badges when a speaker request is updated."""
    if not instance.speaker:
        return
    from badges.services import evaluate_speaker_badges

    transaction.on_commit(lambda: evaluate_speaker_badges(instance.speaker))
