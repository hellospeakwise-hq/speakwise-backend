"""Tests for event import extraction, preview, and image attachment."""

import io
import json
import socket
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Event
from events.services.event_import.exceptions import (
    EventFetchError,
    ImageImportError,
    ResponseTooLarge,
    UnsafeImportURL,
    UnsupportedContentType,
)
from events.services.event_import.extract.base import ExtractionContext, ImageCandidate
from events.services.event_import.extract.json_ld import extract as extract_json_ld
from events.services.event_import.extract.microdata import extract as extract_microdata
from events.services.event_import.extract.open_graph import (
    extract as extract_open_graph,
)
from events.services.event_import.extract.platform import (
    detect_platform,
    extract_platform,
)
from events.services.event_import.fetcher import (
    FetchedDocument,
    fetch_html,
    validate_public_url,
)
from events.services.event_import.images import (
    download_import_image,
    resolve_image_token,
    select_image_candidate,
    sign_image_token,
)
from events.services.event_import.service import build_event_import_preview
from users.models import User

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "event_import"
PUBLIC_ADDRINFO = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]
LOOPBACK_ADDRINFO = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]


def load_fixture(name: str) -> str:
    """Return the saved HTML fixture text."""
    return (FIXTURE_DIR / name).read_text()


def fixture_context(name: str, url: str) -> ExtractionContext:
    """Build an extraction context from a saved HTML fixture."""
    html = load_fixture(name)
    return ExtractionContext(url=url, soup=BeautifulSoup(html, "html.parser"))


def mock_response(
    *, status_code: int = 200, headers: dict | None = None, body: bytes = b""
) -> Mock:
    """Build a streaming requests response mock."""
    response = Mock()
    response.status_code = status_code
    response.headers = headers or {}
    response.is_redirect = status_code in {301, 302, 303, 307, 308}
    response.iter_content.return_value = [body] if body else []
    return response


def make_png_bytes() -> bytes:
    """Return a small valid PNG image."""
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16), "red").save(buffer, format="PNG")
    return buffer.getvalue()


class SafeFetcherTests(SimpleTestCase):
    """URL validation and outbound fetching safety checks."""

    def test_rejects_non_http_schemes(self):
        """Non-web schemes are rejected before any request is made."""
        for url in ("ftp://example.com/e", "file:///etc/passwd", "javascript:alert(1)"):
            with self.subTest(url=url), self.assertRaises(UnsafeImportURL):
                validate_public_url(url)

    def test_rejects_credentials_and_nonstandard_ports(self):
        """Credentials and non-standard ports are not fetchable."""
        for url in (
            "https://user:secret@example.com/e",
            "https://example.com:8080/e",
        ):
            with self.subTest(url=url), self.assertRaises(UnsafeImportURL):
                validate_public_url(url)

    @patch("events.services.event_import.fetcher.socket.getaddrinfo")
    def test_rejects_private_and_link_local_addresses(self, getaddrinfo):
        """Private, link-local, and loopback addresses are rejected."""
        for address in ("192.168.1.10", "10.0.0.5", "169.254.169.254", "::1"):
            with self.subTest(address=address):
                getaddrinfo.return_value = [
                    (socket.AF_INET6, socket.SOCK_STREAM, 6, "", (address, 80, 0, 0))
                ]
                with self.assertRaises(UnsafeImportURL):
                    validate_public_url("https://internal.example/e")

    @patch("events.services.event_import.fetcher.socket.getaddrinfo")
    def test_accepts_public_addresses(self, getaddrinfo):
        """A public hostname is accepted and whitespace is trimmed."""
        getaddrinfo.return_value = PUBLIC_ADDRINFO
        self.assertEqual(
            validate_public_url(" https://example.com/event "),
            "https://example.com/event",
        )

    @patch("events.services.event_import.fetcher.socket.getaddrinfo")
    def test_fetch_html_returns_page(self, getaddrinfo):
        """A successful fetch returns the body and final URL."""
        getaddrinfo.return_value = PUBLIC_ADDRINFO
        response = mock_response(
            headers={"Content-Type": "text/html; charset=utf-8"},
            body=b"<html><body>event</body></html>",
        )
        with patch(
            "events.services.event_import.fetcher._build_session"
        ) as build_session:
            build_session.return_value.get.return_value = response
            document = fetch_html("https://example.com/event")
        self.assertEqual(document.url, "https://example.com/event")
        self.assertEqual(document.content, b"<html><body>event</body></html>")

    @patch("events.services.event_import.fetcher.socket.getaddrinfo")
    def test_rejects_non_html_response(self, getaddrinfo):
        """Non-HTML responses are rejected as unsupported."""
        getaddrinfo.return_value = PUBLIC_ADDRINFO
        response = mock_response(
            headers={"Content-Type": "application/json"}, body=b"{}"
        )
        with patch(
            "events.services.event_import.fetcher._build_session"
        ) as build_session:
            build_session.return_value.get.return_value = response
            with self.assertRaises(UnsupportedContentType):
                fetch_html("https://example.com/event")

    @patch("events.services.event_import.fetcher.socket.getaddrinfo")
    def test_rejects_declared_oversized_response(self, getaddrinfo):
        """A declared Content-Length above the limit is rejected early."""
        getaddrinfo.return_value = PUBLIC_ADDRINFO
        response = mock_response(
            headers={
                "Content-Type": "text/html",
                "Content-Length": str(3 * 1024 * 1024),
            }
        )
        with patch(
            "events.services.event_import.fetcher._build_session"
        ) as build_session:
            build_session.return_value.get.return_value = response
            with self.assertRaises(ResponseTooLarge):
                fetch_html("https://example.com/event")

    def test_rejects_redirect_to_private_address(self):
        """Redirect targets are re-validated before being followed."""

        def dns(host, port, **kwargs):
            if host == "127.0.0.1":
                return LOOPBACK_ADDRINFO
            return PUBLIC_ADDRINFO

        redirect = mock_response(
            status_code=302, headers={"Location": "http://127.0.0.1/admin"}
        )
        with (
            patch(
                "events.services.event_import.fetcher.socket.getaddrinfo",
                side_effect=dns,
            ),
            patch(
                "events.services.event_import.fetcher._build_session"
            ) as build_session,
        ):
            build_session.return_value.get.return_value = redirect
            with self.assertRaises(UnsafeImportURL):
                fetch_html("https://example.com/event")

    @patch("events.services.event_import.fetcher.socket.getaddrinfo")
    def test_network_errors_become_fetch_errors(self, getaddrinfo):
        """Requests transport errors are wrapped in EventFetchError."""
        getaddrinfo.return_value = PUBLIC_ADDRINFO
        with patch(
            "events.services.event_import.fetcher._build_session"
        ) as build_session:
            build_session.return_value.get.side_effect = requests.ConnectionError(
                "down"
            )
            with self.assertRaises(EventFetchError):
                fetch_html("https://example.com/event")


class JsonLdExtractionTests(SimpleTestCase):
    """schema.org Event JSON-LD extraction."""

    def _extract(self, payload, url="https://example.com/event"):
        html = (
            "<html><head><script type='application/ld+json'>"
            + json.dumps(payload)
            + "</script></head></html>"
        )
        return extract_json_ld(fixture_context_from_html(html, url))

    def test_extracts_core_event_fields(self):
        """Nested Event fields, offers, location, and images are mapped."""
        extraction = self._extract(
            {
                "@context": "https://schema.org",
                "@type": "Event",
                "name": "Test Conf",
                "startDate": "2026-05-12T09:00:00+02:00",
                "endDate": "2026-05-13T18:00:00+02:00",
                "description": "<p>Hello</p>",
                "image": [
                    {
                        "@type": "ImageObject",
                        "url": "https://cdn.example.com/card.jpg",
                        "width": 1200,
                        "height": 630,
                    }
                ],
                "location": {
                    "@type": "Place",
                    "name": "Kosmos",
                    "address": {
                        "addressLocality": "Berlin",
                        "addressCountry": "DE",
                    },
                },
                "offers": {"price": "0", "priceCurrency": "EUR"},
                "url": "https://example.com/event",
            }
        )
        self.assertEqual(extraction.fields["title"], "Test Conf")
        self.assertEqual(extraction.fields["location"], "Kosmos, Berlin")
        self.assertEqual(extraction.fields["country"], "Germany")
        self.assertTrue(extraction.fields["is_free"])
        candidate = extraction.fields["event_image_candidates"][0]
        self.assertEqual(candidate.width, 1200)
        self.assertEqual(candidate.height, 630)

    def test_accepts_event_subtypes(self):
        """Event subtypes such as EducationEvent are accepted."""
        extraction = self._extract(
            {
                "@type": "EducationEvent",
                "name": "Workshop",
                "startDate": "2026-05-12T09:00:00Z",
            }
        )
        self.assertEqual(extraction.fields["title"], "Workshop")

    def test_selects_event_matching_page_url(self):
        """When several events exist, the URL-matching event wins."""
        extraction = self._extract(
            [
                {
                    "@type": "Event",
                    "name": "Other Event",
                    "url": "https://example.com/other",
                    "startDate": "2026-05-12T09:00:00Z",
                },
                {
                    "@type": "Event",
                    "name": "This Event",
                    "url": "https://www.example.com/event/",
                    "startDate": "2026-05-12T09:00:00Z",
                },
            ]
        )
        self.assertEqual(extraction.fields["title"], "This Event")
        self.assertEqual(extraction.warnings[0]["code"], "multiple_events")

    def test_selects_next_upcoming_event(self):
        """Without a URL match, the earliest upcoming event is selected."""
        extraction = self._extract(
            [
                {
                    "@type": "Event",
                    "name": "Past Event",
                    "startDate": "2020-01-01T09:00:00Z",
                },
                {
                    "@type": "Event",
                    "name": "Future Event",
                    "startDate": "2099-01-01T09:00:00Z",
                },
            ]
        )
        self.assertEqual(extraction.fields["title"], "Future Event")

    def test_handles_graph_and_virtual_location(self):
        """Top-level @graph nodes are flattened and virtual locations become Online."""
        extraction = self._extract(
            {
                "@graph": [
                    {"@type": "Organization", "name": "Host"},
                    {
                        "@type": "Event",
                        "name": "Online Conf",
                        "eventAttendanceMode": (
                            "https://schema.org/OnlineEventAttendanceMode"
                        ),
                        "location": {"@type": "VirtualLocation"},
                    },
                ]
            }
        )
        self.assertEqual(extraction.fields["title"], "Online Conf")
        self.assertEqual(extraction.fields["location"], "Online")

    def test_paid_aggregate_offer_is_not_free(self):
        """An aggregate offer with a positive low price is not free."""
        extraction = self._extract(
            {
                "@type": "Event",
                "name": "Paid Conf",
                "offers": [
                    {
                        "@type": "AggregateOffer",
                        "lowPrice": "273.95",
                        "priceCurrency": "USD",
                    }
                ],
            }
        )
        self.assertFalse(extraction.fields["is_free"])

    def test_cancelled_event_warns(self):
        """A cancelled event status produces a warning."""
        extraction = self._extract(
            {
                "@type": "Event",
                "name": "Cancelled Conf",
                "eventStatus": "https://schema.org/EventCancelled",
            }
        )
        self.assertIn("event_cancelled", [item["code"] for item in extraction.warnings])

    def test_malformed_json_is_ignored(self):
        """Malformed JSON-LD is ignored without failing extraction."""
        html = (
            "<html><head><script type='application/ld+json'>{not json}</script>"
            "</head></html>"
        )
        extraction = extract_json_ld(fixture_context_from_html(html, "https://x.test"))
        self.assertEqual(extraction.fields, {})


class OpenGraphExtractionTests(SimpleTestCase):
    """OpenGraph, Twitter, and canonical link extraction."""

    def test_extracts_meta_fields_and_images(self):
        """OpenGraph and Twitter meta tags are mapped with image dimensions."""
        html = """
        <html><head>
          <meta property="og:title" content="OG Conf">
          <meta property="og:description" content="OG description">
          <meta property="og:url" content="https://example.com/og">
          <meta property="event:start_time" content="2026-05-12T09:00:00Z">
          <meta property="event:end_time" content="2026-05-12T18:00:00Z">
          <meta property="og:image" content="https://cdn.example.com/a.jpg">
          <meta property="og:image:width" content="1200">
          <meta property="og:image:height" content="630">
          <meta property="og:image" content="https://cdn.example.com/b.jpg">
          <meta name="twitter:image" content="https://cdn.example.com/c.jpg">
        </head></html>
        """
        extraction = extract_open_graph(
            fixture_context_from_html(html, "https://example.com/og")
        )
        self.assertEqual(extraction.fields["title"], "OG Conf")
        self.assertEqual(extraction.fields["website"], "https://example.com/og")
        self.assertEqual(extraction.fields["start_date_time"], "2026-05-12T09:00:00Z")
        candidates = extraction.fields["event_image_candidates"]
        self.assertEqual(len(candidates), 3)
        self.assertEqual(candidates[0].width, 1200)

    def test_uses_canonical_link_when_og_url_is_absent(self):
        """The canonical link is used when og:url is missing."""
        html = '<html><head><link rel="canonical" href="https://example.com/canonical"></head></html>'
        extraction = extract_open_graph(
            fixture_context_from_html(html, "https://example.com/event")
        )
        self.assertEqual(extraction.fields["website"], "https://example.com/canonical")


class MicrodataExtractionTests(SimpleTestCase):
    """schema.org Event microdata extraction."""

    def test_extracts_event_microdata(self):
        """Event, location, offers, and image microdata are mapped."""
        html = """
        <div itemscope itemtype="https://schema.org/Event">
          <span itemprop="name">Micro Conf</span>
          <time itemprop="startDate" datetime="2026-05-12T09:00:00+02:00"></time>
          <time itemprop="endDate" datetime="2026-05-12T18:00:00+02:00"></time>
          <div itemprop="location" itemscope itemtype="https://schema.org/Place">
            <span itemprop="name">Venue</span>
            <div itemprop="address" itemscope
                 itemtype="https://schema.org/PostalAddress">
              <span itemprop="addressLocality">Berlin</span>
              <meta itemprop="addressCountry" content="DE">
            </div>
          </div>
          <div itemprop="offers" itemscope itemtype="https://schema.org/Offer">
            <meta itemprop="price" content="0">
          </div>
          <img itemprop="image" src="https://cdn.example.com/micro.jpg">
        </div>
        """
        extraction = extract_microdata(
            fixture_context_from_html(html, "https://example.com/micro")
        )
        self.assertEqual(extraction.fields["title"], "Micro Conf")
        self.assertEqual(extraction.fields["location"], "Venue, Berlin")
        self.assertEqual(extraction.fields["country"], "Germany")
        self.assertTrue(extraction.fields["is_free"])
        self.assertEqual(
            extraction.fields["event_image_candidates"][0].url,
            "https://cdn.example.com/micro.jpg",
        )


class PlatformAdapterTests(SimpleTestCase):
    """Adapters for platforms that do not publish schema.org JSON-LD."""

    def test_luma_adapter(self):
        """The Luma adapter reads the embedded Next.js event payload."""
        extraction = extract_platform(
            fixture_context("luma_event.html", "https://luma.com/july4-brooklyn")
        )
        self.assertEqual(extraction.source, "platform:luma")
        self.assertEqual(
            extraction.fields["title"], "July 4th Fireworks · Brooklyn Viewing"
        )
        self.assertIn("official ticketed viewing", extraction.fields["description"])
        self.assertEqual(
            extraction.fields["location"], "Brooklyn Bridge Park, New York"
        )
        self.assertEqual(extraction.fields["country"], "United States")
        self.assertTrue(extraction.fields["is_free"])
        self.assertEqual(extraction.fields["website"], "https://july4.events.nyc")
        self.assertTrue(extraction.fields["event_image_candidates"])

    def test_devfolio_adapter(self):
        """The Devfolio adapter reads the embedded hackathon payload."""
        extraction = extract_platform(
            fixture_context("devfolio_event.html", "https://biosv2.devfolio.co/")
        )
        self.assertEqual(extraction.source, "platform:devfolio")
        self.assertEqual(extraction.fields["title"], "BIOS V2")
        self.assertIn("BIOS V2", extraction.fields["description"])
        self.assertNotIn("**", extraction.fields["description"])
        self.assertEqual(extraction.fields["country"], "India")
        self.assertTrue(extraction.fields["is_free"])
        self.assertEqual(
            extraction.fields["website"], "https://bios.notyouraverage.xyz/"
        )
        self.assertTrue(extraction.fields["event_image_candidates"])

    def test_detect_platform_labels(self):
        """Hostnames are labelled with their platform or generic."""
        cases = {
            "https://www.eventbrite.com/e/example-tickets-1": "eventbrite",
            "https://lu.ma/example": "luma",
            "https://www.meetup.com/group/events/1": "meetup",
            "https://konfhub.com/example": "konfhub",
            "https://biosv2.devfolio.co/": "devfolio",
            "https://example.com/event": "generic",
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(detect_platform(url), expected)


class EventImportPreviewTests(TestCase):
    """End-to-end preview building with the network mocked out."""

    def setUp(self):
        """Create the user that owns the previews."""
        self.user = User.objects.create(
            username="importer",
            email="importer@example.com",
            password="testpassword",
        )

    def _preview(self, fixture_name: str, url: str):
        document = FetchedDocument(
            url=url,
            content=load_fixture(fixture_name).encode(),
            content_type="text/html",
        )
        with patch(
            "events.services.event_import.service.fetch_html",
            return_value=document,
        ):
            return build_event_import_preview(url, self.user.pk)

    def _preview_html(self, html: str, url: str):
        document = FetchedDocument(
            url=url,
            content=html.encode(),
            content_type="text/html",
        )
        with patch(
            "events.services.event_import.service.fetch_html",
            return_value=document,
        ):
            return build_event_import_preview(url, self.user.pk)

    def test_eventbrite_preview(self):
        """Eventbrite JSON-LD and virtual location produce a review draft."""
        preview = self._preview(
            "eventbrite_event.html",
            "https://www.eventbrite.com/e/ai-workshop-for-business-owners-"
            "no-tech-skills-needed-tickets-1557521291109",
        )
        self.assertEqual(preview.platform, "eventbrite")
        self.assertEqual(preview.field_sources["title"], "json_ld")
        self.assertEqual(
            preview.draft.title,
            "AI Workshop For Business Owners — No Tech Skills Needed!",
        )
        self.assertEqual(preview.draft.location, "Online")
        self.assertFalse(preview.draft.is_free)
        self.assertIsNotNone(preview.draft.start_date_time)
        self.assertIsNotNone(preview.draft.event_image_url)
        self.assertEqual(
            resolve_image_token(preview.event_image_token, self.user.pk),
            preview.draft.event_image_url,
        )

    def test_meetup_preview(self):
        """Meetup JSON-LD is extracted without a platform adapter."""
        preview = self._preview(
            "meetup_event.html",
            "https://www.meetup.com/lfdt-nigeria/events/316360664/",
        )
        self.assertEqual(preview.platform, "meetup")
        self.assertEqual(
            preview.draft.title,
            "What PDPP Unlocks: 4 Builders on What They Built, Why It Was Hard, "
            "What's Next",
        )
        self.assertEqual(preview.draft.location, "Online")
        self.assertIsNone(preview.draft.is_free)
        self.assertEqual(preview.field_sources["start_date_time"], "json_ld")

    def test_konfhub_preview_uses_json_ld_and_og_image(self):
        """Konfhub JSON-LD is merged with its OpenGraph image."""
        preview = self._preview(
            "konfhub_event.html",
            "https://konfhub.com/masterclass-ai-for-social-impact",
        )
        self.assertEqual(preview.platform, "konfhub")
        self.assertEqual(preview.draft.title, "Masterclass on AI for Social Impact")
        self.assertEqual(preview.draft.country, "India")
        self.assertLessEqual(len(preview.draft.location), 150)
        self.assertIsNone(preview.draft.is_free)
        self.assertIsNotNone(preview.draft.event_image_url)
        self.assertEqual(preview.field_sources["event_image_url"], "open_graph")
        self.assertIn("Chennai", preview.draft.location)

    def test_luma_preview(self):
        """The Luma adapter fills fields and keeps its source labels."""
        preview = self._preview("luma_event.html", "https://luma.com/july4-brooklyn")
        self.assertEqual(preview.platform, "luma")
        self.assertEqual(preview.draft.title, "July 4th Fireworks · Brooklyn Viewing")
        self.assertTrue(preview.draft.is_free)
        self.assertEqual(preview.draft.country, "United States")
        self.assertEqual(preview.field_sources["title"], "platform:luma")

    def test_devfolio_preview(self):
        """The Devfolio adapter fills fields and keeps its source label."""
        preview = self._preview("devfolio_event.html", "https://biosv2.devfolio.co/")
        self.assertEqual(preview.platform, "devfolio")
        self.assertEqual(preview.draft.title, "BIOS V2")
        self.assertTrue(preview.draft.is_free)
        self.assertEqual(preview.draft.country, "India")
        self.assertEqual(preview.field_sources["title"], "platform:devfolio")

    def test_empty_page_returns_no_event_data_warning(self):
        """A page with no event data warns instead of failing."""
        preview = self._preview_html(
            "<html><body>nothing here</body></html>",
            "https://example.com/blank",
        )
        self.assertIsNone(preview.draft.title)
        self.assertIn("no_event_data", [item["code"] for item in preview.warnings])
        self.assertIn("title", preview.missing_fields)

    def test_date_only_value_adds_warning(self):
        """Date-only values are kept as wall-clock midnight with a warning."""
        html = """
        <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Event","name":"Date Only",
         "startDate":"2026-05-12"}
        </script>
        """
        preview = self._preview_html(html, "https://example.com/date-only")
        self.assertIsNone(preview.draft.start_date_time.tzinfo)
        self.assertIn("date_only", [item["code"] for item in preview.warnings])

    def test_past_event_adds_warning(self):
        """An event whose end date has passed warns the user."""
        html = """
        <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Event","name":"Past Conf",
         "startDate":"2020-01-01T09:00:00Z",
         "endDate":"2020-01-02T18:00:00Z"}
        </script>
        """
        preview = self._preview_html(html, "https://example.com/past")
        self.assertIn("event_in_past", [item["code"] for item in preview.warnings])

    def test_long_location_is_truncated(self):
        """Locations longer than the model limit are truncated with a warning."""
        payload = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": "Long Location Conf",
            "startDate": "2099-01-01T09:00:00Z",
            "endDate": "2099-01-02T18:00:00Z",
            "location": {"@type": "Place", "name": "A" * 200},
        }
        preview = self._preview_html(
            "<script type='application/ld+json'>" + json.dumps(payload) + "</script>",
            "https://example.com/long-location",
        )
        self.assertEqual(len(preview.draft.location), 150)
        self.assertIn("location_truncated", [item["code"] for item in preview.warnings])

    def test_duplicate_event_warning(self):
        """An existing title and website produce a duplicate warning."""
        Event.objects.create(
            title="AI Workshop For Business Owners — No Tech Skills Needed!",
            website="https://www.eventbrite.com/e/ai-workshop-for-business-owners-"
            "no-tech-skills-needed-tickets-1557521291109",
            is_free=False,
        )
        preview = self._preview(
            "eventbrite_event.html",
            "https://www.eventbrite.com/e/ai-workshop-for-business-owners-"
            "no-tech-skills-needed-tickets-1557521291109",
        )
        self.assertIn("duplicate_event", [item["code"] for item in preview.warnings])

    def test_duplicate_title_warning(self):
        """A reused title produces a duplicate-title warning."""
        Event.objects.create(
            title="Masterclass on AI for Social Impact",
            website="https://other.example.com/masterclass",
            is_free=True,
        )
        preview = self._preview(
            "konfhub_event.html",
            "https://konfhub.com/masterclass-ai-for-social-impact",
        )
        self.assertIn("duplicate_title", [item["code"] for item in preview.warnings])


class EventImportPreviewApiTests(TestCase):
    """API-level behaviour for POST /api/events/import/preview/."""

    def setUp(self):
        """Create an authenticated user and the preview route."""
        self.client = APIClient()
        self.user = User.objects.create(
            username="api-importer",
            email="api-importer@example.com",
            password="testpassword",
        )
        self.url = reverse("events:event-import-preview")

    def test_unauthenticated_request_is_rejected(self):
        """Anonymous callers cannot use the import endpoint."""
        response = self.client.post(self.url, {"url": "https://example.com/e"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_url_is_rejected(self):
        """A malformed URL returns a validation error."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"url": "not-a-url"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_local_address_is_rejected(self):
        """Local addresses are rejected before fetching."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url, {"url": "http://localhost/admin"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("url", response.data)

    def test_successful_preview_returns_draft_and_token(self):
        """A successful preview returns the draft, sources, and image token."""
        document = FetchedDocument(
            url="https://luma.com/july4-brooklyn",
            content=load_fixture("luma_event.html").encode(),
            content_type="text/html",
        )
        self.client.force_authenticate(user=self.user)
        with patch(
            "events.services.event_import.service.fetch_html",
            return_value=document,
        ):
            response = self.client.post(
                self.url,
                {"url": "https://luma.com/july4-brooklyn"},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["platform"], "luma")
        self.assertEqual(
            response.data["draft"]["title"], "July 4th Fireworks · Brooklyn Viewing"
        )
        self.assertTrue(response.data["event_image_token"])
        self.assertTrue(response.data["field_sources"])

    def test_upstream_failure_returns_bad_gateway(self):
        """Upstream fetch failures return 502 with a stable code."""
        self.client.force_authenticate(user=self.user)
        with patch(
            "events.services.event_import.service.fetch_html",
            side_effect=EventFetchError("down"),
        ):
            response = self.client.post(
                self.url, {"url": "https://example.com/event"}, format="json"
            )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.data["code"], "event_import_unavailable")


class EventImageTests(TestCase):
    """Image candidate selection, tokens, validation, and create-time attachment."""

    def setUp(self):
        """Create the image owner and an isolated media directory."""
        self.user = User.objects.create(
            username="image-importer",
            email="image-importer@example.com",
            password="testpassword",
        )
        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)

    def test_selects_largest_candidate(self):
        """The largest image candidate wins."""
        candidates = [
            ImageCandidate(url="https://cdn.example.com/small.jpg", source="json_ld"),
            ImageCandidate(
                url="https://cdn.example.com/large.jpg",
                source="open_graph",
                width=1200,
                height=630,
            ),
        ]
        self.assertEqual(
            select_image_candidate(candidates).url,
            "https://cdn.example.com/large.jpg",
        )

    def test_token_roundtrip_and_owner_check(self):
        """A token round-trips and is bound to its owner."""
        token = sign_image_token("https://cdn.example.com/a.jpg", self.user.pk)
        self.assertEqual(
            resolve_image_token(token, self.user.pk),
            "https://cdn.example.com/a.jpg",
        )
        with self.assertRaises(ImageImportError):
            resolve_image_token(token, uuid.uuid4())

    def test_tampered_and_expired_tokens_are_rejected(self):
        """Tampered and expired tokens are rejected."""
        with self.assertRaises(ImageImportError):
            resolve_image_token("not-a-token", self.user.pk)

        with patch("django.core.signing.time.time", return_value=1):
            expired = sign_image_token("https://cdn.example.com/a.jpg", self.user.pk)
        with self.assertRaises(ImageImportError):
            resolve_image_token(expired, self.user.pk)

    def test_download_reencodes_valid_image(self):
        """A valid downloaded image is re-encoded and renamed."""
        png = make_png_bytes()
        token = sign_image_token("https://cdn.example.com/a.jpg", self.user.pk)
        document = FetchedDocument(
            url="https://cdn.example.com/a.jpg",
            content=png,
            content_type="image/png",
        )
        with patch(
            "events.services.event_import.images.fetch_image",
            return_value=document,
        ):
            file = download_import_image(token, self.user.pk)
        self.assertEqual(file.name, "event-import.png")
        self.assertGreater(len(file.read()), 0)

    def test_download_rejects_invalid_image(self):
        """Non-image bytes are rejected."""
        token = sign_image_token("https://cdn.example.com/a.jpg", self.user.pk)
        document = FetchedDocument(
            url="https://cdn.example.com/a.jpg",
            content=b"not an image",
            content_type="image/png",
        )
        with (
            patch(
                "events.services.event_import.images.fetch_image",
                return_value=document,
            ),
            self.assertRaises(ImageImportError),
        ):
            download_import_image(token, self.user.pk)

    def test_create_event_from_signed_image_token(self):
        """Submitting a valid token attaches the imported image."""
        png = make_png_bytes()
        token = sign_image_token("https://cdn.example.com/a.jpg", self.user.pk)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        payload = {
            "title": "Imported Image Event",
            "website": "https://example.com/imported-image",
            "is_free": True,
            "event_image_token": token,
        }
        with (
            patch(
                "events.serializers.download_import_image",
                return_value=ContentFile(png, name="event-import.png"),
            ),
            override_settings(MEDIA_ROOT=self.temp_media.name),
        ):
            response = self.client.post(
                reverse("events:event-list-create"), payload, format="json"
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(title="Imported Image Event")
        self.assertTrue(event.event_image.name.endswith(".png"))

    def test_failed_image_download_returns_400_and_creates_nothing(self):
        """An image failure is a validation error and leaves no event behind."""
        token = sign_image_token("https://cdn.example.com/a.jpg", self.user.pk)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        payload = {
            "title": "Failed Image Event",
            "website": "https://example.com/failed-image",
            "is_free": True,
            "event_image_token": token,
        }
        with (
            patch(
                "events.serializers.download_import_image",
                side_effect=EventFetchError("down"),
            ),
            override_settings(MEDIA_ROOT=self.temp_media.name),
        ):
            response = self.client.post(
                reverse("events:event-list-create"), payload, format="json"
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("event_image_token", response.data)
        self.assertFalse(Event.objects.filter(title="Failed Image Event").exists())

    def test_uploaded_image_wins_over_token(self):
        """An uploaded file takes precedence over the token."""
        png = make_png_bytes()
        token = sign_image_token("https://cdn.example.com/a.jpg", self.user.pk)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        payload = {
            "title": "Uploaded Image Event",
            "website": "https://example.com/uploaded-image",
            "is_free": True,
            "event_image_token": token,
        }
        with (
            patch(
                "events.serializers.download_import_image",
                side_effect=AssertionError("token should not be resolved"),
            ),
            override_settings(MEDIA_ROOT=self.temp_media.name),
        ):
            response = self.client.post(
                reverse("events:event-list-create"),
                {
                    **payload,
                    "event_image": ContentFile(png, name="upload.png"),
                },
                format="multipart",
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(title="Uploaded Image Event")
        self.assertTrue(event.event_image.name.endswith(".png"))


def fixture_context_from_html(html: str, url: str) -> ExtractionContext:
    """Build an extraction context from an inline HTML string."""
    return ExtractionContext(url=url, soup=BeautifulSoup(html, "html.parser"))
