"""Blogs views."""

from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from blogs.models import Blog
from blogs.serializers import BlogSerializer


class BlogListView(APIView):
    """List and create blog posts."""

    def get_permissions(self):
        """GET is public; POST requires an authenticated user."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(tags=["Blogs"], responses={200: BlogSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """List all blog posts."""
        blogs = Blog.objects.select_related("created_by")
        serializer = BlogSerializer(blogs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Blogs"], request=BlogSerializer, responses={201: BlogSerializer}
    )
    def post(self, request, *args, **kwargs):
        """Create a new blog post."""
        serializer = BlogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save(created_by=request.user)
        except IntegrityError as err:
            return Response({"exception": str(err)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BlogDetailView(APIView):
    """Retrieve, update and delete a single blog post."""

    def get_permissions(self):
        """GET is public; PATCH/DELETE require an authenticated user."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(tags=["Blogs"], responses={200: BlogSerializer})
    def get(self, request, pk, *args, **kwargs):
        """Retrieve a single blog post."""
        blog = get_object_or_404(Blog, pk=pk)
        serializer = BlogSerializer(blog)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Blogs"], request=BlogSerializer, responses={200: BlogSerializer}
    )
    def patch(self, request, pk, *args, **kwargs):
        """Partially update a blog post."""
        blog = get_object_or_404(Blog, pk=pk)
        serializer = BlogSerializer(blog, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=["Blogs"], responses={204: None})
    def delete(self, request, pk, *args, **kwargs):
        """Delete a blog post."""
        blog = get_object_or_404(Blog, pk=pk)
        blog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
