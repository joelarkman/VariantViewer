from rest_framework import permissions
from rest_framework import viewsets

from db.models import Sample
from web.serializers import SampleListSerializer


class SampleListView(viewsets.ModelViewSet):
    queryset = Sample.objects.all()
    serializer_class = SampleListSerializer
    permission_classes = [permissions.AllowAny]
