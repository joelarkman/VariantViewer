from rest_framework import permissions
from rest_framework import viewsets

from db.models import SamplesheetSample
from web.serializers import SampleListSerializer


class SampleListView(viewsets.ModelViewSet):

    # newest = Run.objects.filter(
    #     samplesheet=OuterRef('samplesheet')).order_by('-completed_at')

    # queryset = SamplesheetSample.objects.annotate(
    #     latest_run=Subquery(newest.values('id')[:1])).order_by('-latest_run').prefetch_related(*['samplesheet', 'samplesheet__runs', 'samplesheet__runs__pipeline_version'])

    queryset = SamplesheetSample.objects.prefetch_related(
        *['samplesheet', 'samplesheet__runs', 'samplesheet__runs__pipeline_version']).order_by('-samplesheet__latest_run__completed_at')
    serializer_class = SampleListSerializer
    permission_classes = [permissions.AllowAny]
