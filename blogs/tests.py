"""Blogs app tests."""

import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

from blogs.models import Blog


def _make_image_file() -> SimpleUploadedFile:
    """Return a valid JPEG upload for testing image fields."""
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format="JPEG")
    return SimpleUploadedFile(
        name="blog.jpg",
        content=buffer.getvalue(),
        content_type="image/jpeg",
    )


class BlogAPITests(APITestCase):
    """Test the blogs list/create and detail endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            username="blogger",
            email="blogger@mail.com",
            password="testpass123",
        )
        self.other_user = get_user_model().objects.create(
            username="other",
            email="other@mail.com",
            password="testpass123",
        )
        self.blog = Blog.objects.create(
            title="First Post",
            short_description="A short summary.",
            full_description="<p>Full <strong>rich text</strong> content.</p>",
            created_by=self.user,
            published_date="2026-08-01",
        )

    def test_list_blogs_is_public(self):
        """Blog list should be readable without authentication."""
        response = self.client.get(reverse("blogs:blog-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "First Post")

    def test_list_returns_all_blog_fields(self):
        """Blog list should include every requested field."""
        response = self.client.get(reverse("blogs:blog-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data[0]
        self.assertIn("image", item)
        self.assertIn("title", item)
        self.assertIn("short_description", item)
        self.assertIn("full_description", item)
        self.assertIn("created_by", item)
        self.assertIn("published_date", item)
        self.assertEqual(
            item["full_description"], "<p>Full <strong>rich text</strong> content.</p>"
        )

    def test_create_blog_requires_authentication(self):
        """Creating a blog should reject anonymous users."""
        response = self.client.post(
            reverse("blogs:blog-list-create"), {"title": "Unauth Post"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_blog(self):
        """An authenticated user should be able to create a blog post."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("blogs:blog-list-create"),
            {
                "title": "Second Post",
                "short_description": "Another summary.",
                "full_description": "<p>More <em>content</em>.</p>",
                "published_date": "2026-08-02",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Second Post")
        self.assertEqual(str(response.data["created_by"]), str(self.user.id))

    def test_create_blog_assigns_current_user_as_creator(self):
        """The authenticated user should be recorded as the blog creator."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            reverse("blogs:blog-list-create"), {"title": "Third Post"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["created_by"]), str(self.other_user.id))
        blog = Blog.objects.get(title="Third Post")
        self.assertEqual(blog.created_by, self.other_user)

    def test_create_blog_with_image(self):
        """A blog should accept an image upload."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("blogs:blog-list-create"),
            {"title": "With Image", "image": _make_image_file()},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("image", response.data)
        self.assertNotEqual(response.data["image"], "")

    def test_create_blog_invalid_data_returns_400(self):
        """Creating a blog without a title should return 400."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("blogs:blog-list-create"), {"short_description": "No title"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_get_blog_detail_is_public(self):
        """Blog detail should be readable without authentication."""
        response = self.client.get(reverse("blogs:blog-detail", args=[self.blog.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "First Post")

    def test_get_nonexistent_blog_returns_404(self):
        """Requesting a blog that does not exist should return 404."""
        response = self.client.get(
            reverse("blogs:blog-detail", args=["00000000-0000-0000-0000-000000000000"])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_blog_requires_authentication(self):
        """Updating a blog should reject anonymous users."""
        response = self.client.patch(
            reverse("blogs:blog-detail", args=[self.blog.id]),
            {"title": "Hacked"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_update_blog(self):
        """An authenticated user should be able to update a blog post."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse("blogs:blog-detail", args=[self.blog.id]),
            {"title": "Updated Title"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Title")

    def test_delete_blog_requires_authentication(self):
        """Deleting a blog should reject anonymous users."""
        response = self.client.delete(reverse("blogs:blog-detail", args=[self.blog.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_delete_blog(self):
        """An authenticated user should be able to delete a blog post."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(reverse("blogs:blog-detail", args=[self.blog.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Blog.objects.filter(pk=self.blog.id).exists())

    def test_creator_name_is_returned(self):
        """The creator's display name should be included in the response."""
        self.user.first_name = "Ada"
        self.user.last_name = "Lovelace"
        self.user.save()
        response = self.client.get(reverse("blogs:blog-detail", args=[self.blog.id]))
        self.assertEqual(response.data["created_by_name"], "Ada Lovelace")
