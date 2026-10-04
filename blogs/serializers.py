"""Serializers for the blogs app."""

from rest_framework import serializers

from blogs.models import Blog


class BlogSerializer(serializers.ModelSerializer):
    """Serializer for the Blog model."""

    created_by_name = serializers.SerializerMethodField()

    class Meta:
        """Meta class for the BlogSerializer."""

        model = Blog
        exclude = ["created_at", "updated_at"]

    def get_created_by_name(self, obj) -> str | None:
        """Return the full name of the user who created the blog post."""
        user = obj.created_by
        if not user:
            return None
        name = " ".join(filter(None, [user.first_name, user.last_name]))
        return name or user.username
