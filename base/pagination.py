"""Shared pagination helpers for APIView list endpoints.

DRF's DEFAULT_PAGINATION_CLASS only applies to GenericAPIView subclasses.
Every list endpoint in this project that uses a plain APIView must call
paginate_api_view explicitly, otherwise a single request can pull an
entire table into memory.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """Default paginator: 20 per page, client-overridable up to 100."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def paginate_api_view(request, queryset, serializer_class, context=None):
    """Paginate a queryset and return a DRF paginated Response.

    Keeps the envelope identical to GenericAPIView list endpoints:
    {"count": ..., "next": ..., "previous": ..., "results": [...]}.
    """
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer_context = {"request": request}
    if context:
        serializer_context.update(context)
    if page is not None:
        serializer = serializer_class(page, many=True, context=serializer_context)
        return paginator.get_paginated_response(serializer.data)
    serializer = serializer_class(queryset, many=True, context=serializer_context)
    return Response(serializer.data)
