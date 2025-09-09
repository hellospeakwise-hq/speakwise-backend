"""organizer tasks."""

from attendees.utils import FileHandler


def create_attendance_task(file, event=None):
    """Create attendance task."""
    FileHandler.clean_file(file, event)
