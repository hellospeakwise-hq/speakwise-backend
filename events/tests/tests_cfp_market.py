"""Tests for the public CFP Market endpoint."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from events.models import Event


class CFPMarketTests(TestCase):
    """Tests for the CFP Market listing rules."""

    def setUp(self):
        """Create events covering the CFP market inclusion rules."""
        self.client = APIClient()
        self.market_url = reverse("events:cfp-market")
        now = timezone.now()

        self.open_event = self._create_event(
            "Open CFP",
            is_active=True,
            cfp_open=True,
            cfp_open_date=now - timedelta(days=1),
            cfp_deadline=now + timedelta(days=30),
        )
        self.closed_event = self._create_event(
            "Closed CFP",
            is_active=True,
            cfp_open=False,
            cfp_deadline=now + timedelta(days=30),
        )
        self.expired_event = self._create_event(
            "Expired CFP",
            is_active=True,
            cfp_open=True,
            cfp_deadline=now + timedelta(days=30),
        )
        # Simulate the deadline passing while cfp_open stayed True.
        Event.objects.filter(pk=self.expired_event.pk).update(
            cfp_deadline=now - timedelta(days=1)
        )
        self.draft_event = self._create_event(
            "Draft CFP",
            is_active=False,
            cfp_open=True,
            cfp_deadline=now + timedelta(days=30),
        )

    def _create_event(self, title, **kwargs):
        """Create a minimal event with a unique title/website."""
        return Event.objects.create(
            title=title,
            website=f"https://example.com/{title.lower().replace(' ', '-')}",
            slug=title.lower().replace(" ", "-"),
            **kwargs,
        )

    def test_market_returns_only_open_active_events(self):
        """Only active, manual-open CFPs within their date window appear."""
        res = self.client.get(self.market_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        titles = {item["title"] for item in res.data}
        self.assertIn("Open CFP", titles)
        self.assertNotIn("Closed CFP", titles)
        self.assertNotIn("Expired CFP", titles)
        self.assertNotIn("Draft CFP", titles)

    def test_market_items_expose_is_cfp_currently_open(self):
        """Returned cards include the computed open flag."""
        res = self.client.get(self.market_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        open_items = [item for item in res.data if item["title"] == "Open CFP"]
        self.assertEqual(len(open_items), 1)
        self.assertTrue(open_items[0]["is_cfp_currently_open"])

    def test_market_requires_no_authentication(self):
        """The CFP market is publicly listable."""
        res = self.client.get(self.market_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_market_is_empty_when_nothing_open(self):
        """A market with no open CFPs returns an empty list, not an error."""
        Event.objects.filter(cfp_open=True).update(cfp_open=False)
        res = self.client.get(self.market_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])
