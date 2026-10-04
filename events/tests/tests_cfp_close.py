"""Tests for the periodic close-expired-CFP routine."""

from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from events.models import Event
from events.tasks import close_expired_cfp_events, close_expired_cfp_events_task


class CloseExpiredCfpEventsTests(TestCase):
    """Tests for close_expired_cfp_events and its task wrapper."""

    def setUp(self):
        """Create events spanning open, closed, and deadline-less CFP states."""
        now = timezone.now()
        self.expired_open = self._create_event(
            "Expired Open",
            cfp_open=True,
            cfp_deadline=now + timedelta(hours=12),
        )
        # Simulate the deadline passing while cfp_open stayed True, as happens
        # when an event is not saved again after its CFP deadline.
        Event.objects.filter(pk=self.expired_open.pk).update(
            cfp_deadline=now - timedelta(hours=1)
        )
        self.open_future = self._create_event(
            "Open Future",
            cfp_open=True,
            cfp_deadline=now + timedelta(hours=12),
        )
        self.already_closed = self._create_event(
            "Already Closed",
            cfp_open=False,
            cfp_deadline=now - timedelta(hours=1),
        )
        self.no_deadline = self._create_event(
            "No Deadline",
            cfp_open=True,
            cfp_deadline=None,
        )

    def _create_event(self, title, **kwargs):
        """Create a minimal event with a unique website."""
        return Event.objects.create(
            title=title,
            website=f"https://example.com/{title.lower().replace(' ', '-')}",
            **kwargs,
        )

    def test_closes_only_open_events_with_passed_deadline(self):
        """cfp_open is flipped to False only for open events past their deadline."""
        closed = close_expired_cfp_events()
        self.assertEqual(closed, 1)
        self.expired_open.refresh_from_db()
        self.assertFalse(self.expired_open.cfp_open)

    def test_leaves_open_events_with_future_deadline_untouched(self):
        """Open events whose deadline has not yet passed stay open."""
        close_expired_cfp_events()
        self.open_future.refresh_from_db()
        self.assertTrue(self.open_future.cfp_open)

    def test_leaves_already_closed_events_untouched(self):
        """Events already closed are not touched again."""
        close_expired_cfp_events()
        self.already_closed.refresh_from_db()
        self.assertFalse(self.already_closed.cfp_open)

    def test_leaves_open_events_without_deadline_untouched(self):
        """Open events with no deadline are never auto-closed."""
        close_expired_cfp_events()
        self.no_deadline.refresh_from_db()
        self.assertTrue(self.no_deadline.cfp_open)

    def test_second_run_closes_nothing(self):
        """The routine is idempotent."""
        close_expired_cfp_events()
        self.assertEqual(close_expired_cfp_events(), 0)

    def test_task_wrapper_uses_the_same_logic(self):
        """The background task delegates to the shared implementation."""
        closed = close_expired_cfp_events_task.call()
        self.assertEqual(closed, 1)
        self.expired_open.refresh_from_db()
        self.assertFalse(self.expired_open.cfp_open)

    def test_management_command_closes_expired_cfps(self):
        """close_expired_cfps closes the same set and reports the count."""
        out = StringIO()
        call_command("close_expired_cfps", stdout=out)
        self.expired_open.refresh_from_db()
        self.assertFalse(self.expired_open.cfp_open)
        self.open_future.refresh_from_db()
        self.assertTrue(self.open_future.cfp_open)
        self.assertIn("Closed 1 expired CFP(s).", out.getvalue())
