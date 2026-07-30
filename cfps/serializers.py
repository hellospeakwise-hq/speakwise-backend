"""CFP serializers."""

from rest_framework import serializers

from cfps.choices import CFPStatusChoices
from cfps.models import CFPReview, CFPSubmission
from speakers.models import SpeakerProfile


class CoSpeakerSerializer(serializers.ModelSerializer):
    """Minimal read-only representation of a co-speaker."""

    name = serializers.SerializerMethodField()

    class Meta:
        """Meta options for CoSpeakerSerializer."""

        model = SpeakerProfile
        fields = ["id", "slug", "name"]

    def get_name(self, obj):
        """Return the co-speaker's full name or username."""
        return (
            f"{obj.user_account.first_name} {obj.user_account.last_name}".strip()
            or obj.user_account.username
        )


class CFPSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for creating and reading CFP submissions."""

    co_speakers = serializers.PrimaryKeyRelatedField(
        queryset=SpeakerProfile.objects.all(), many=True, required=False
    )
    co_speakers_detail = CoSpeakerSerializer(
        source="co_speakers", many=True, read_only=True
    )
    submitter_email = serializers.EmailField(source="submitter.email", read_only=True)
    event_slug = serializers.CharField(source="event.slug", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)

    class Meta:
        """Meta options for CFPSubmissionSerializer."""

        model = CFPSubmission
        exclude = ["created_at", "updated_at"]
        read_only_fields = [
            "id",
            "submitter",
            "submitter_email",
            "status",
            "event",
            "event_slug",
            "event_title",
        ]

    def validate_title(self, value):
        """Strip whitespace from title."""
        return value.strip()

    def update(self, instance, validated_data):
        """Update a CFP submission, only allowed while pending."""
        if instance.status != CFPStatusChoices.PENDING:
            raise serializers.ValidationError(
                "Submissions can only be edited while they are pending review."
            )
        return super().update(instance, validated_data)


class CFPStatusUpdateSerializer(serializers.ModelSerializer):
    """Organizer-only serializer for updating submission status."""

    class Meta:
        """Meta options for CFPStatusUpdateSerializer."""

        model = CFPSubmission
        fields = ["status"]


class CFPReviewSerializer(serializers.ModelSerializer):
    """Serializer for submitting and reading a CFP review."""

    reviewer_email = serializers.EmailField(source="reviewer.email", read_only=True)

    class Meta:
        """Meta options."""

        model = CFPReview
        fields = [
            "id",
            "submission",
            "reviewer",
            "reviewer_email",
            "score",
            "notes",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "reviewer",
            "reviewer_email",
            "submission",
            "created_at",
        ]


class CFPReviewDetailSerializer(serializers.ModelSerializer):
    """Read-only serializer that includes reviewer display info."""

    reviewer_email = serializers.EmailField(source="reviewer.email", read_only=True)
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        """Meta options for CFPReviewDetailSerializer."""

        model = CFPReview
        fields = [
            "id",
            "reviewer",
            "reviewer_email",
            "reviewer_name",
            "score",
            "notes",
            "created_at",
        ]
        read_only_fields = fields

    def get_reviewer_name(self, obj):
        """Return reviewer display name, falling back to username or email."""
        u = obj.reviewer
        return f"{u.first_name} {u.last_name}".strip() or u.username or u.email


class CFPSubmissionWithScoreSerializer(CFPSubmissionSerializer):
    """Extends CFPSubmissionSerializer with review aggregate + individual reviewer data."""

    avg_score = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    my_score = serializers.SerializerMethodField()
    reviews_detail = serializers.SerializerMethodField()

    class Meta(CFPSubmissionSerializer.Meta):
        """Meta options for CFPSubmissionWithScoreSerializer."""

        exclude = ["created_at", "updated_at"]

    def _get_reviews(self, obj):
        if not hasattr(obj, "_cached_reviews"):
            obj._cached_reviews = list(obj.reviews.select_related("reviewer").all())
        return obj._cached_reviews

    def get_avg_score(self, obj):
        """Return average review score, or None if no reviews exist."""
        reviews = self._get_reviews(obj)
        if not reviews:
            return None
        return round(sum(r.score for r in reviews) / len(reviews), 1)

    def get_review_count(self, obj):
        """Return total number of reviews for this submission."""
        return len(self._get_reviews(obj))

    def get_my_score(self, obj):
        """Return the current reviewer's score, or None if not yet reviewed."""
        request = self.context.get("request")
        if not request:
            return None
        for r in self._get_reviews(obj):
            if r.reviewer_id == request.user.pk:
                return r.score
        return None

    def get_reviews_detail(self, obj):
        """Return full review detail for all reviewers."""
        reviews = self._get_reviews(obj)
        return CFPReviewDetailSerializer(reviews, many=True).data
