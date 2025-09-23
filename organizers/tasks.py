"""organizer tasks."""

from celery import shared_task

from base.utils import FileHandler


@shared_task
def create_attendance_task(file, event: int = None):
    """Create attendance task."""
    FileHandler.clean_file(file, event)
