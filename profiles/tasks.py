"""Organization background tasks."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django_tasks import task

from profiles.choices import OrganizationStatusChoices

logger = logging.getLogger(__name__)


@task()
def send_organization_status_email_task(organization_id) -> None:
    """Email the organization when it is approved or rejected."""
    from profiles.models.organization_models import OrganizationProfile

    try:
        org = OrganizationProfile.objects.select_related("owner").get(
            id=organization_id
        )
    except OrganizationProfile.DoesNotExist:
        logger.error("Organization with id %s not found", organization_id)
        return

    recipient = org.contact_email or (org.owner.email if org.owner else None)
    if not recipient:
        logger.error("No contact email for organization %s", org.id)
        return

    approved = org.status == OrganizationStatusChoices.ACTIVE
    dashboard_url = f"{settings.FRONTEND_URL}/dashboard/organizer"
    html_message = render_to_string(
        "emails/organization_status_update.html",
        {
            "organization_name": org.name,
            "approved": approved,
            "status": org.get_status_display(),
            "admin_notes": org.admin_notes,
            "dashboard_url": dashboard_url,
        },
    )

    if approved:
        subject = f"Congratulations! {org.name} has been approved"
        message = (
            f"Congratulations! Your organization {org.name} has been approved.\n\n"
            f"Go ahead and add events and CFPs: {dashboard_url}"
        )
    else:
        subject = f"Update on your organization application - {org.name}"
        message = (
            f"Your organization {org.name} was not approved.\n\n"
            f"{org.admin_notes or 'Please contact support for more information.'}"
        )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Status update email sent to organization: %s", org.id)
    except Exception as e:
        logger.error("Failed to send status update email to %s: %s", recipient, e)


@task()
def send_organization_submitted_admin_email_task(organization_id) -> None:
    """Tell the admins a new organization is waiting for review."""
    from profiles.models.organization_models import OrganizationProfile

    recipients = list(getattr(settings, "ADMIN_NOTIFICATION_EMAILS", []))
    if not recipients:
        logger.warning("ADMIN_NOTIFICATION_EMAILS is empty; skipping admin alert")
        return

    try:
        org = OrganizationProfile.objects.select_related("owner").get(
            id=organization_id
        )
    except OrganizationProfile.DoesNotExist:
        logger.error("Organization with id %s not found", organization_id)
        return

    review_url = settings.BACKEND_URL + reverse(
        "admin:profiles_organizationprofile_change", args=[org.pk]
    )
    html_message = render_to_string(
        "emails/organization_admin_alert.html",
        {
            "organization_name": org.name,
            "website": org.website,
            "contact_email": org.contact_email
            or (org.owner.email if org.owner else ""),
            "description": org.description,
            "review_url": review_url,
        },
    )

    try:
        send_mail(
            subject=f"New organization awaiting approval: {org.name}",
            message=(
                f"{org.name} has registered and needs approval.\n\n"
                f"Review it here: {review_url}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Admin alert sent for organization: %s", org.id)
    except Exception as e:
        logger.error("Failed to send admin alert for organization %s: %s", org.id, e)
