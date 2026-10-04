"""Organization background tasks."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_tasks import task

logger = logging.getLogger(__name__)


@task()
def send_organization_status_email_task(organization_id) -> None:
    """Send email when organization status is updated."""
    from profiles.models.organization_models import OrganizationProfile

    try:
        org = OrganizationProfile.objects.get(id=organization_id)
    except OrganizationProfile.DoesNotExist:
        logger.error("Organization with id %s not found", organization_id)
        return

    if not org.contact_email:
        logger.error("No contact email for organization %s", org.id)
        return

    html_message = render_to_string(
        "emails/organization_status_update.html",
        {
            "organization_name": org.name,
            "status": org.get_status_display(),
            "admin_notes": org.admin_notes,
        },
    )

    try:
        send_mail(
            subject=f"Organization Status Updated - {org.name}",
            message=f"Your organization {org.name} status is now {org.get_status_display()}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[org.contact_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Status update email sent to organization: %s", org.id)
    except Exception as e:
        logger.error(
            "Failed to send status update email to %s: %s", org.contact_email, e
        )
