"""Tests for the OTP email verification flow."""

import re
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from users.models import OAuthExchangeCode, OtpCode, User
from users.services.otp_services import purge_expired_auth_tokens


class OtpFlowTestBase(TestCase):
    """Shared setup and helpers for OTP flow tests."""

    def setUp(self):
        """Configure the email backend, client, and common URLs."""
        # DRF caches throttle hit-counters in the shared locmem cache, which
        # survives between tests; reset it so global anon-throttle state from
        # earlier tests cannot make these assertions flaky.
        cache.clear()
        self.client = APIClient()
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        settings.DEFAULT_FROM_EMAIL = "no-reply@speakwise.test"
        self.register_url = reverse("users:register")
        self.verify_url = reverse("users:verify-otp")
        self.resend_url = reverse("users:resend-otp")
        self.speakers_create_url = reverse("speakers:speakers_list_create")

    def _register(self, email="reg@example.com", username="reguser") -> dict:
        """Register a new user and return the response data."""
        response = self.client.post(
            self.register_url,
            {"email": email, "username": username, "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data

    def _otp_email(self):
        """Return the most recently delivered OTP email."""
        matching = [m for m in mail.outbox if "verification code" in m.subject]
        self.assertTrue(matching, "No OTP email was sent")
        return matching[-1]

    def _code_from_email(self) -> str:
        """Extract the 6-digit code from the OTP email body."""
        match = re.search(r"\b\d{6}\b", self._otp_email().body)
        self.assertIsNotNone(match, "No 6-digit code found in the email body")
        return match.group(0)

    def _verify(self, email="reg@example.com", otp="000000"):
        """POST /verify-otp/ and return the response."""
        return self.client.post(
            self.verify_url, {"email": email, "otp": otp}, format="json"
        )

    def _wrong_code(self, actual: str) -> str:
        """Return a 6-digit code guaranteed to differ from ``actual``."""
        return "0" * 6 if actual != "0" * 6 else "1" * 6


class RegistrationOtpTests(OtpFlowTestBase):
    """Registering issues an OTP and leaves the user unverified."""

    def test_register_creates_unverified_user_and_sends_otp(self):
        """A new email/password user starts unverified and gets an OTP email."""
        data = self._register()
        self.assertFalse(data["is_email_verified"])

        user = User.objects.get(email="reg@example.com")
        self.assertFalse(user.is_email_verified)

        otp = OtpCode.objects.get(user=user)
        self.assertFalse(otp.is_used)
        self.assertFalse(otp.is_expired)
        self.assertEqual(otp.attempt_count, 0)
        self.assertEqual(len(otp.code_hash), 64)

        code = self._code_from_email()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        # Only the hash is stored, never the plaintext code.
        self.assertNotEqual(otp.code_hash, code)

    def test_otp_code_is_not_leaked_in_register_response(self):
        """The plaintext OTP never appears in any API response."""
        data = self._register()
        code = self._code_from_email()
        self.assertNotIn(code, str(data))
        self.assertNotIn("otp", data)


class VerifyOtpTests(OtpFlowTestBase):
    """Verifying the correct code marks the email as verified."""

    def test_verify_marks_email_verified(self):
        """Submitting the correct OTP verifies the user and consumes the code."""
        self._register()
        code = self._code_from_email()
        response = self._verify(otp=code)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Email verified successfully.")

        user = User.objects.get(email="reg@example.com")
        self.assertTrue(user.is_email_verified)
        self.assertTrue(OtpCode.objects.get(user=user).is_used)

    def test_verify_with_wrong_code_rejects_and_counts_attempts(self):
        """An incorrect code is rejected and increments the attempt counter."""
        self._register()
        code = self._code_from_email()
        response = self._verify(otp=self._wrong_code(code))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid OTP code.", str(response.data))

        otp = OtpCode.objects.get(user=User.objects.get(email="reg@example.com"))
        self.assertEqual(otp.attempt_count, 1)
        user = User.objects.get(email="reg@example.com")
        self.assertFalse(user.is_email_verified)

    def test_verify_invalid_email_returns_generic_error(self):
        """Unknown emails get the same response as a bad code."""
        response = self._verify(email="nobody@example.com")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid email or OTP code.", str(response.data))

    def test_verify_already_verified_user_is_rejected(self):
        """Verifying an account that is already verified is rejected."""
        self._register()
        code = self._code_from_email()
        self._verify(otp=code)
        response = self._verify(otp=code)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already verified", str(response.data))

    def test_verify_code_is_single_use(self):
        """A consumed code cannot be reused to verify again."""
        self._register()
        code = self._code_from_email()
        self.assertEqual(self._verify(otp=code).status_code, status.HTTP_200_OK)
        response = self._verify(otp=code)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already verified", str(response.data))

    def test_verify_expired_code_is_rejected(self):
        """An expired OTP is rejected and marked used."""
        self._register()
        code = self._code_from_email()
        user = User.objects.get(email="reg@example.com")
        OtpCode.objects.filter(user=user).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        response = self._verify(otp=code)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", str(response.data))
        self.assertTrue(OtpCode.objects.get(user=user).is_used)

    def test_verify_locks_after_max_attempts(self):
        """After OTP_MAX_ATTEMPTS failures even the correct code is rejected."""
        self._register()
        code = self._code_from_email()
        wrong = self._wrong_code(code)

        last_status = None
        last_body = None
        for _ in range(settings.OTP_MAX_ATTEMPTS):
            response = self._verify(otp=wrong)
            last_status = response.status_code
            last_body = str(response.data)

        self.assertEqual(last_status, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Too many attempts", last_body)

        locked = self._verify(otp=code)
        self.assertEqual(locked.status_code, status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(email="reg@example.com")
        self.assertFalse(user.is_email_verified)

    def test_verify_rejects_malformed_otp(self):
        """Non-numeric or wrongly sized codes fail serializer validation."""
        self._register()
        for bad in ["abc", "12345", "1234567", "abcdef"]:
            response = self._verify(otp=bad)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, bad)


class ResendOtpTests(OtpFlowTestBase):
    """Resending enforces a cooldown and issues a fresh code."""

    def test_resend_within_cooldown_returns_generic_response(self):
        """A resend inside the cooldown is not distinguishable from a success.

        The endpoint always answers 200 with the same message; the underlying
        cooldown rule still prevents another email from being dispatched.
        """
        self._register()
        initial_outbox = len(mail.outbox)
        response = self.client.post(
            self.resend_url, {"email": "reg@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"], "A new verification code has been sent."
        )
        self.assertEqual(len(mail.outbox), initial_outbox)

    def test_resend_after_cooldown_issues_new_code(self):
        """After the cooldown a new, distinct OTP is emailed and the old one dies."""
        self._register()
        old_code = self._code_from_email()
        user = User.objects.get(email="reg@example.com")
        old_otp = OtpCode.objects.get(user=user)

        OtpCode.objects.filter(user=user).update(
            created_at=timezone.now() - timedelta(minutes=3)
        )
        old_otp.refresh_from_db()

        response = self.client.post(
            self.resend_url, {"email": "reg@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        old_otp.refresh_from_db()

        new_code = self._code_from_email()
        new_otp = OtpCode.objects.get(user=user, is_used=False)
        self.assertNotEqual(new_code, old_code)
        self.assertTrue(old_otp.is_used)
        self.assertNotEqual(new_otp.pk, old_otp.pk)

    def test_resend_for_verified_user_returns_generic_response(self):
        """A verified account gets the generic response and no further email."""
        self._register()
        initial_outbox = len(mail.outbox)
        self._code_from_email()
        code = self._code_from_email()
        self._verify(otp=code)
        response = self.client.post(
            self.resend_url, {"email": "reg@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"], "A new verification code has been sent."
        )
        self.assertEqual(len(mail.outbox), initial_outbox)

    def test_resend_unknown_email_returns_generic_response(self):
        """An unregistered email is answered like a genuine resend, silently."""
        response = self.client.post(
            self.resend_url, {"email": "nobody@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"], "A new verification code has been sent."
        )
        self.assertEqual(len(mail.outbox), 0)


class ProfileVerificationGateTests(OtpFlowTestBase):
    """Profile completion is blocked until the OTP is verified."""

    def test_unverified_user_cannot_create_speaker_profile(self):
        """An unverified user gets 403 when creating a speaker profile."""
        data = self._register()
        user = User.objects.get(id=data["id"])
        self.client.force_authenticate(user)
        response = self.client.post(
            self.speakers_create_url, {"short_bio": "Hi"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Email verification", str(response.data))

    def test_verified_user_can_create_speaker_profile(self):
        """After verification the same request succeeds."""
        self._register()
        code = self._code_from_email()
        self._verify(otp=code)
        user = User.objects.get(email="reg@example.com")
        self.client.force_authenticate(user)
        response = self.client.post(
            self.speakers_create_url, {"short_bio": "Hi"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user_account"], user.id)

    def test_unverified_user_cannot_create_organization_profile(self):
        """An unverified user gets 403 when creating an organization profile."""
        data = self._register()
        user = User.objects.get(id=data["id"])
        self.client.force_authenticate(user)
        url = reverse("organizations:organization-list-create")
        response = self.client.post(url, {"name": "Acme"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unverified_user_cannot_update_own_profile(self):
        """An unverified user cannot PATCH /users/me/ with nested profile data."""
        data = self._register()
        user = User.objects.get(id=data["id"])
        self.client.force_authenticate(user)
        url = reverse("users:retrieve_update_authenticated_user")
        response = self.client.patch(url, {"first_name": "X"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PurgeExpiredAuthTokensTests(TestCase):
    """The purge routine removes used and expired OTP/exchange codes."""

    def setUp(self):
        """Create a user and a batch of auth codes in varied states."""
        self.user = User.objects.create(username="purgeuser", email="purge@example.com")

    def _otp(self, *, is_used=False, is_expired=False, salt="salt"):
        """Create an OTP row for the test user."""
        return OtpCode.objects.create(
            user=self.user,
            code_hash="a" * 64,
            salt=salt,
            expires_at=(
                timezone.now() - timedelta(minutes=1)
                if is_expired
                else timezone.now() + timedelta(minutes=5)
            ),
            is_used=is_used,
        )

    def test_purge_removes_used_expired_and_keeps_active(self):
        """Only used or expired codes are deleted."""
        self._otp(is_used=True)
        self._otp(is_expired=True)
        active = self._otp()
        exchange = OAuthExchangeCode.objects.create(
            user=self.user,
            code_hash="b" * 64,
            expires_at=timezone.now() + timedelta(minutes=5),
            is_used=True,
        )

        purged = purge_expired_auth_tokens()

        self.assertEqual(purged, 3)
        self.assertTrue(OtpCode.objects.filter(pk=active.pk).exists())
        self.assertEqual(OtpCode.objects.count(), 1)
        self.assertFalse(OAuthExchangeCode.objects.filter(pk=exchange.pk).exists())

    def test_purge_on_empty_tables_returns_zero(self):
        """An empty table purges cleanly."""
        self.assertEqual(purge_expired_auth_tokens(), 0)
