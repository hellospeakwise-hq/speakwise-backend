"""Organizer views using Generic Views."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import OrganizerProfile, OrganizerSocialLinks
from .serializers import OrganizerProfileSerializer, OrganizerSocialLinksSerializer


class OrganizerProfileListCreateView(generics.ListCreateAPIView):
    """List and create organizer profiles."""
    
    serializer_class = OrganizerProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optimize query with select_related and prefetch_related."""
        return OrganizerProfile.objects.select_related('user_account').prefetch_related('social_links').all()


class OrganizerProfileRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and destroy organizer profiles."""
    
    serializer_class = OrganizerProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optimize query with select_related and prefetch_related."""
        return OrganizerProfile.objects.select_related('user_account').prefetch_related('social_links').all()


class OrganizerSocialLinksListCreateView(generics.ListCreateAPIView):
    """List and create organizer social links."""
    
    serializer_class = OrganizerSocialLinksSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optimize query with select_related."""
        return OrganizerSocialLinks.objects.select_related('organizer').all()
    
    def perform_create(self, serializer):
        """Set organizer from URL parameter."""
        organizer_id = self.kwargs.get('organizer_id')
        if organizer_id:
            serializer.save(organizer_id=organizer_id)
        else:
            serializer.save()


class OrganizerSocialLinksRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and destroy organizer social links."""
    
    serializer_class = OrganizerSocialLinksSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optimize query with select_related."""
        return OrganizerSocialLinks.objects.select_related('organizer').all()