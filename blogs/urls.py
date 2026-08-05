"""blogs urls."""

from django.urls import path

from blogs import views

app_name = "blogs"

urlpatterns = [
    path("blogs/", views.BlogListView.as_view(), name="blog-list-create"),
    path("blogs/<uuid:pk>/", views.BlogDetailView.as_view(), name="blog-detail"),
]
