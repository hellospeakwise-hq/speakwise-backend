"""Signal definitions for the profile app."""

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from profiles.choices import OrganizationStatusChoices
from profiles.models.organization_models import OrganizationProfile
from profiles.tasks import (
    send_organization_status_email_task,
    send_organization_submitted_admin_email_task,
)


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
