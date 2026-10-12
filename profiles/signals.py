"""Signal definitions for the profile app."""

from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from events.models import Event
from profiles.choices import OrganizationStatusChoices
from profiles.models.organization_models import OrganizationProfile
from profiles.models.speaker_models import SpeakerExperiences, SpeakerProfile
from profiles.services.notification_services import (
    notify_followers_of_new_experience,
    notify_followers_of_public_talk,
    notify_followers_of_upcoming_event,
)
from profiles.tasks import (
    send_organization_status_email_task,
    send_organization_submitted_admin_email_task,
)
from talks.models import Talks


@receiver(pre_save, sender=OrganizationProfile)
def save_old_status(sender, instance, **kwargs):
    """Save the old status before the update."""
    if instance.pk:
        try:
            instance.old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            instance.old_status = None
    else:
        instance.old_status = None


@receiver(post_save, sender=OrganizationProfile)
def notify_admins_of_new_organization(sender, instance, created, **kwargs):
    """Alert admins when a new organization is waiting for approval."""
    if created and instance.status == OrganizationStatusChoices.PENDING:
        transaction.on_commit(
            lambda: send_organization_submitted_admin_email_task.enqueue(
                str(instance.id)
            )
        )


@receiver(post_save, sender=OrganizationProfile)
def send_email_if_status_changed(sender, instance, created, **kwargs):
    """Send email if organization status is updated from pending."""
    if (
        not created
        and hasattr(instance, "old_status")
        and (
            instance.old_status == OrganizationStatusChoices.PENDING
            and instance.status
            in [OrganizationStatusChoices.ACTIVE, OrganizationStatusChoices.REJECTED]
        )
    ):
        send_organization_status_email_task.enqueue(str(instance.id))


@receiver(post_save, sender=SpeakerExperiences)
def create_experience_notifications(sender, instance, created, **kwargs):
    """Notify followers when a speaker adds a public speaking experience."""
    if not created or not instance.speaker_id:
        return
    transaction.on_commit(lambda: notify_followers_of_new_experience(str(instance.pk)))


@receiver(m2m_changed, sender=SpeakerProfile.events_spoken.through)
def create_upcoming_event_notifications(
    sender, instance, action, reverse, model, pk_set, **kwargs
):
    """Notify followers when a speaker is added to a public upcoming event."""
    if action != "post_add" or not pk_set:
        return

    if reverse:
        speaker_ids = list(pk_set)
        event_ids = [instance.pk]
    else:
        speaker_ids = [instance.pk]
        event_ids = list(pk_set)

    for event_id in event_ids:
        transaction.on_commit(
            lambda event_id=event_id: notify_followers_of_upcoming_event(
                speaker_ids, str(event_id)
            )
        )


@receiver(pre_save, sender=Event)
def remember_event_publication_status(sender, instance, **kwargs):
    """Capture whether an existing event was already publicly active."""
    if instance.pk:
        instance._was_active = (
            sender.objects.filter(pk=instance.pk)
            .values_list("is_active", flat=True)
            .first()
        )
    else:
        instance._was_active = False


@receiver(post_save, sender=Event)
def notify_followers_when_event_is_published(sender, instance, created, **kwargs):
    """Notify speakers' followers when an event becomes public."""
    if created or instance._was_active or not instance.is_active:
        return

    speaker_ids = list(instance.speakers.values_list("pk", flat=True))
    if speaker_ids:
        transaction.on_commit(
            lambda: notify_followers_of_upcoming_event(speaker_ids, str(instance.pk))
        )


@receiver(pre_save, sender=Talks)
def remember_talk_publication_status(sender, instance, **kwargs):
    """Capture whether an existing talk was already public."""
    if instance.pk:
        instance._was_public = (
            sender.objects.filter(pk=instance.pk)
            .values_list("is_public", flat=True)
            .first()
        )
    else:
        instance._was_public = False


@receiver(post_save, sender=Talks)
def notify_followers_when_talk_is_published(sender, instance, created, **kwargs):
    """Notify followers when a speaker's talk becomes public."""
    if not instance.is_public or (not created and instance._was_public):
        return
    transaction.on_commit(lambda: notify_followers_of_public_talk(str(instance.pk)))
