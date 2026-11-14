"""speaker serializers."""

from django.db import transaction
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    BooleanField,
    CharField,
    IntegerField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from profiles.models.speaker_models import (
    Notification,
    SpeakerExperiences,
    SpeakerFollow,
    SpeakerProfile,
    SpeakerSkillTag,
    SpeakerSocialLinks,
    get_speaker_profile,
)


class SpeakerSocialLinksSerializer(ModelSerializer):
    """speaker social links serializers."""

    class Meta:
        """meta options."""

        model = SpeakerSocialLinks
        exclude = ["created_at", "updated_at", "speaker"]


class SpeakerSkillTagSerializer(ModelSerializer):
    """speaker skill tag serializers."""

    class Meta:
        """meta options."""

        model = SpeakerSkillTag
        exclude = ["created_at", "updated_at", "speaker"]


class SpeakerExperiencesSerializer(ModelSerializer):
    """speaker experiences serializer."""

    class Meta:
        """meta options."""

        model = SpeakerExperiences
        exclude = ["created_at", "updated_at"]
        read_only_fields = ["feedback_slug", "speaker"]

    def create(self, validated_data) -> SpeakerExperiences:
        """Create speaker experience with validation."""
        event_date = validated_data.get("event_date")
        if event_date is None:
            raise ValidationError("Event date is required.")
        speaker = get_speaker_profile(self.context["request"].user)
        if speaker is None:
            raise ValidationError(
                {"detail": "Speaker profile not found for this user."}
            )
        validated_data["speaker"] = speaker
        if self.context.get("slug") and speaker.slug != self.context.get("slug"):
            raise ValidationError(
                {"detail": "Speaker profile not found for this user."}
            )
        return super().create(validated_data)


class SpeakerExperiencePublicSerializer(ModelSerializer):
    """Serializer for the SpeakerExperiences model."""

    event_image = SerializerMethodField()
    event_title = SerializerMethodField()

    def get_event_image(self, obj) -> str:
        if obj.event and obj.event.event_image:
            try:
                request = self.context.get("request")
                if request is not None:
                    return request.build_absolute_uri(obj.event.event_image.url)
                return obj.event.event_image.url
            except Exception:
                return obj.event.event_image.url
        return ""

    def get_event_title(self, obj) -> str:
        if obj.event and obj.event.title:
            return obj.event.title
        return obj.event_name or ""

    class Meta:
        """meta options."""

        model = SpeakerExperiences
        exclude = ["created_at", "updated_at", "speaker", "feedback_slug"]


class SpeakerFollowSerializer(ModelSerializer):
    """Serializer for the SpeakerFollow model."""

    follower_username = SerializerMethodField()

    class Meta:
        """meta options."""

        model = SpeakerFollow
        fields = ["id", "follower", "follower_username", "created_at"]
        read_only_fields = ["id", "follower", "follower_username", "created_at"]

    def get_follower_username(self, obj) -> str:
        """Return the username of the follower."""
        return obj.follower.username


class FollowerDetailSerializer(ModelSerializer):
    """Rich serializer returning speaker profile info for followers/following lists."""

    username = SerializerMethodField()
    full_name = SerializerMethodField()
    avatar = SerializerMethodField()
    slug = SerializerMethodField()
    short_bio = SerializerMethodField()
    country = SerializerMethodField()
    organization = SerializerMethodField()

    class Meta:
        """meta options."""

        model = SpeakerFollow
        fields = [
            "id",
            "username",
            "full_name",
            "avatar",
            "slug",
            "short_bio",
            "country",
            "organization",
            "created_at",
        ]

    def __init__(self, *args, **kwargs):
        """Initialize the serializer."""
        super().__init__(*args, **kwargs)
        self._profile_cache = {}

    def _get_profile(self, user):
        """Get the SpeakerProfile for a user, with per-instance caching."""
        user_id = user.id
        if user_id not in self._profile_cache:
            self._profile_cache[user_id] = SpeakerProfile.objects.filter(
                user_account=user
            ).first()
        return self._profile_cache[user_id]

    def _get_user(self, obj):
        """Get the relevant user depending on context (follower or following)."""
        context_type = self.context.get("type", "followers")
        if context_type == "following":
            return obj.speaker.user_account
        return obj.follower

    def get_username(self, obj) -> str:
        """Return the username."""
        return self._get_user(obj).username

    def get_full_name(self, obj) -> str:
        """Return the full name (None-safe)."""
        user = self._get_user(obj)
        first = (user.first_name or "").strip()
        last = (user.last_name or "").strip()
        full = f"{first} {last}".strip()
        return full or user.username

    def get_avatar(self, obj):
        """Return the avatar URL."""
        profile = self._get_profile(self._get_user(obj))
        if profile and profile.avatar:
            return profile.avatar.url
        return None

    def get_slug(self, obj):
        """Return the speaker profile slug."""
        profile = self._get_profile(self._get_user(obj))
        return profile.slug if profile else None

    def get_short_bio(self, obj) -> str:
        """Return the short bio."""
        profile = self._get_profile(self._get_user(obj))
        return profile.short_bio if profile else ""

    def get_country(self, obj) -> str:
        """Return the country."""
        profile = self._get_profile(self._get_user(obj))
        return profile.country if profile else ""

    def get_organization(self, obj) -> str:
        """Return the organization."""
        profile = self._get_profile(self._get_user(obj))
        return profile.organization if profile else ""


class FollowStatusSerializer(Serializer):
    """Read shape for GET /speakers/<slug>/follow/."""

    is_following = BooleanField(read_only=True)
    followers_count = IntegerField(read_only=True)
    following_count = IntegerField(read_only=True)


class FollowActionSerializer(Serializer):
    """Read shape for POST/DELETE /speakers/<slug>/follow/."""

    detail = CharField(read_only=True)
    followers_count = IntegerField(read_only=True)
    following_count = IntegerField(read_only=True)


class FollowersListResponseSerializer(Serializer):
    """Read shape for the speaker followers list envelope."""

    followers_count = IntegerField(read_only=True)
    followers = FollowerDetailSerializer(many=True, read_only=True)


class FollowingListResponseSerializer(Serializer):
    """Read shape for the speaker following list envelope."""

    following_count = IntegerField(read_only=True)
    following = FollowerDetailSerializer(many=True, read_only=True)


class SpeakerProfileSerializer(WritableNestedModelSerializer):
    """speaker profile serializers."""

    social_links = SpeakerSocialLinksSerializer(many=True, required=False)
    skill_tags = SpeakerSkillTagSerializer(many=True, required=False)
    speaker_name = SerializerMethodField()
    username = SerializerMethodField()
    followers_count = SerializerMethodField()
    following_count = SerializerMethodField()
    is_following = SerializerMethodField()
    total_talks = SerializerMethodField()
    total_reviews = SerializerMethodField()
    badges_count = SerializerMethodField()
    average_rating = SerializerMethodField()
    reputation_score = SerializerMethodField()
    rank_tier = SerializerMethodField()

    class Meta:
        """meta options."""

        model = SpeakerProfile
        exclude = ["created_at", "updated_at"]
        read_only_fields = ("slug", "user_account")

    @transaction.atomic
    def create(self, validated_data):
        """Create the requesting user's speaker profile.

        A user can hold at most one speaker profile. Owning organizations does
        not prevent a user from also becoming a speaker.
        """
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if SpeakerProfile.objects.filter(user_account=request.user).exists():
                raise ValidationError(
                    {"detail": "Speaker profile already exists for this user."}
                )
            validated_data["user_account"] = request.user
        else:
            raise ValidationError(
                {"detail": "Must be authenticated to create a profile."}
            )

        return super().create(validated_data)

    def get_speaker_name(self, obj) -> str:
        """Get speaker name."""
        first = (obj.user_account.first_name or "").strip()
        last = (obj.user_account.last_name or "").strip()
        full = f"{first} {last}".strip()
        return full if full else obj.user_account.username

    def get_username(self, obj) -> str:
        """Return the account username used as the public speaker handle."""
        return obj.user_account.username

    def get_followers_count(self, obj) -> int:
        """Return total number of followers for this speaker."""
        return getattr(obj, "_prefetched_followers_count", obj.followers.count())

    def get_following_count(self, obj) -> int:
        """Return how many speakers this speaker follows (their following count)."""
        return getattr(
            obj,
            "_prefetched_following_count",
            SpeakerFollow.objects.filter(follower=obj.user_account).count(),
        )

    def get_is_following(self, obj) -> bool:
        """Return True if the current authenticated user follows this speaker."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            cache_key = f"is_following_{request.user.id}_{obj.id}"
            if not hasattr(self, "_is_following_cache"):
                self._is_following_cache = {}
            if cache_key not in self._is_following_cache:
                self._is_following_cache[cache_key] = SpeakerFollow.objects.filter(
                    follower=request.user, speaker=obj
                ).exists()
            return self._is_following_cache[cache_key]
        return False

    def get_total_talks(self, obj) -> int:
        """Return total number of speaking experiences."""
        return getattr(obj, "_annotated_total_talks", obj.experiences.count())

    def get_total_reviews(self, obj) -> int:
        """Return total number of feedback reviews received."""
        return getattr(obj, "_annotated_total_reviews", obj.speaker_feedback.count())

    def get_badges_count(self, obj) -> int:
        """Return count of eligible or claimed digital badges."""
        return getattr(
            obj,
            "_annotated_badges_count",
            obj.badges.filter(status__in=["eligible", "claimed"]).count(),
        )

    def get_average_rating(self, obj) -> float | None:
        """Return average overall rating (1-10) or None if no reviews yet."""
        val = getattr(obj, "_annotated_avg_rating", None)
        if val is not None:
            return round(float(val), 2) if float(val) > 0 else None
        from django.db.models import Avg

        avg = obj.speaker_feedback.aggregate(Avg("overall_rating"))[
            "overall_rating__avg"
        ]
        return round(float(avg), 2) if avg is not None else None

    def get_reputation_score(self, obj) -> float:
        """Return the calculated SpeakWise reputation score."""
        val = getattr(obj, "reputation_score", None)
        if val is not None:
            return round(float(val), 2)
        # Fallback calculation if serializer used without view annotations
        total_talks = self.get_total_talks(obj)
        total_reviews = self.get_total_reviews(obj)
        avg_rating = self.get_average_rating(obj) or 0.0

        if total_talks == 0 and total_reviews == 0:
            return 0.0
        if total_reviews == 0:
            return round(min(total_talks * 0.5, 5.0), 2)

        weighted = (total_reviews * avg_rating + 40.0) / (total_reviews + 5.0)
        exp_bonus = min(total_talks * 0.1, 1.0)
        return round(weighted * 0.9 + exp_bonus, 2)

    def get_rank_tier(self, obj) -> str:
        """Return rank tier based on reputation score and experience."""
        score = self.get_reputation_score(obj)
        talks = self.get_total_talks(obj)
        if score >= 9.2 and talks >= 10:
            return "Top 1% Keynote Speaker"
        elif score >= 8.5 and talks >= 5:
            return "Distinguished Speaker"
        elif talks >= 3:
            return "Verified Speaker"
        elif talks >= 1:
            return "Rising Speaker"
        return "New Speaker"

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update speaker profile objects."""
        social_data = validated_data.pop("social_links", None)

        instance = super().update(instance, validated_data)
        # NOTE: skill_tags nested updates are handled automatically by
        # WritableNestedModelSerializer via update_or_create_reverse_relations().
        # No manual loop needed here.

        if social_data is not None:
            self._sync_social_links(instance, social_data)

        return instance

    @staticmethod
    def _sync_social_links(instance, social_data):
        """Make the speaker's social links match the submitted list.

        Links are keyed by platform name: submitted names are created or
        updated, and any existing link not in the list is removed. This lets a
        speaker edit and delete links from one save.
        """
        links = {
            item["name"].strip(): item["link"].strip()
            for item in social_data
            if item.get("name") and item.get("link")
        }
        instance.social_links.exclude(name__in=links).delete()
        for name, link in links.items():
            SpeakerSocialLinks.objects.update_or_create(
                speaker=instance, name=name, defaults={"link": link}
            )


class SpeakerProfileDetailSerializer(SpeakerProfileSerializer):
    """Public speaker profile for detail views.

    Adds ``feedback_summary``, an aggregate of the speaker's ratings across all
    events they spoke at. List views keep using ``SpeakerProfileSerializer`` so
    the aggregate is never computed for paginated results.
    """

    feedback_summary = SerializerMethodField()
    events_spoken = SerializerMethodField()
    talks = SerializerMethodField()

    def get_feedback_summary(self, obj) -> dict:
        """Return per-criterion averages and distributions for the speaker."""
        from feedbacks.services import build_feedback_summary

        return build_feedback_summary(obj)

    def get_events_spoken(self, obj) -> list:
        """Return list of distinct events/conferences this speaker has spoken at."""
        results = []
        seen_names = set()

        # 1. From SpeakerExperiences
        for exp in obj.experiences.select_related("event").order_by("-event_date"):
            name = exp.event_name or (exp.event.title if exp.event else "")
            if name and name.lower() not in seen_names:
                seen_names.add(name.lower())
                img_url = ""
                evt = exp.event
                if not evt and exp.event_name:
                    from events.models import Event
                    evt = Event.objects.filter(title__icontains=exp.event_name.strip()).first()
                if evt and evt.event_image:
                    try:
                        req = self.context.get("request")
                        img_url = (
                            req.build_absolute_uri(evt.event_image.url)
                            if req
                            else evt.event_image.url
                        )
                    except Exception:
                        img_url = evt.event_image.url
                results.append(
                    {
                        "id": str(evt.id) if evt else str(exp.id),
                        "name": name,
                        "topic": exp.topic or "",
                        "date": exp.event_date.isoformat()
                        if exp.event_date
                        else "",
                        "image": img_url,
                        "event_id": str(evt.id) if evt else None,
                    }
                )

        # 2. From Talks with linked Events
        from talks.models import Talks

        for talk in (
            Talks.objects.filter(speaker=obj)
            .select_related("event")
            .order_by("-created_at")
        ):
            if talk.event:
                name = talk.event.title
                if name and name.lower() not in seen_names:
                    seen_names.add(name.lower())
                    img_url = ""
                    if talk.event.event_image:
                        try:
                            req = self.context.get("request")
                            img_url = (
                                req.build_absolute_uri(
                                    talk.event.event_image.url
                                )
                                if req
                                else talk.event.event_image.url
                            )
                        except Exception:
                            img_url = talk.event.event_image.url
                    results.append(
                        {
                            "id": str(talk.event.id),
                            "name": name,
                            "topic": talk.title,
                            "date": str(talk.event.date)
                            if hasattr(talk.event, "date")
                            else "",
                            "image": img_url,
                            "event_id": str(talk.event.id),
                        }
                    )

        return results

    def get_talks(self, obj) -> list:
        """Return list of talks given by this speaker."""
        from talks.models import Talks

        talks_list = []
        for talk in (
            Talks.objects.filter(speaker=obj)
            .select_related("event")
            .order_by("-created_at")
        ):
            img_url = ""
            if talk.event and talk.event.event_image:
                try:
                    req = self.context.get("request")
                    img_url = (
                        req.build_absolute_uri(talk.event.event_image.url)
                        if req
                        else talk.event.event_image.url
                    )
                except Exception:
                    img_url = talk.event.event_image.url
            talks_list.append(
                {
                    "id": str(talk.id),
                    "title": talk.title,
                    "description": talk.description,
                    "duration": talk.duration,
                    "category": talk.category,
                    "event_title": talk.event.title if talk.event else "",
                    "event_id": str(talk.event.id) if talk.event else None,
                    "event_image": img_url,
                }
            )
        return talks_list

    class Meta:
        """Meta options."""

        model = SpeakerProfile
        fields = [
            "id",
            "slug",
            "user_account",
            "username",
            "avatar",
            "speaker_name",
            "organization",
            "short_bio",
            "long_bio",
            "country",
            "events_spoken",
            "talks",
            "social_links",
            "skill_tags",
            "followers_count",
            "following_count",
            "is_following",
            "total_talks",
            "total_reviews",
            "badges_count",
            "average_rating",
            "reputation_score",
            "rank_tier",
            "feedback_summary",
        ]
        read_only_fields = ("slug", "user_account")


# ---------- Speaker Deck ----------


ALLOWED_DECK_EXTENSIONS = {".pptx", ".pdf", ".key", ".ppt", ".odp", ".zip"}
MAX_DECK_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# ---------- Notification ----------


class NotificationSerializer(ModelSerializer):
    """Read-only serializer for in-app notifications."""

    class Meta:
        """Meta options."""

        model = Notification
        fields = [
            "id",
            "user",
            "message",
            "link",
            "is_read",
            "created_at",
        ]
        read_only_fields = fields
