"""Signal definitions for the profile app."""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from profiles.choices import OrganizationStatusChoices
from profiles.models.organization_models import OrganizationProfile
from profiles.tasks import send_organization_status_email_task


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
        send_organization_status_email_task(instance.id)
