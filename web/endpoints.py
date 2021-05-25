from rest_framework import viewsets, permissions

from db.models import PipelineVersion, Run, SampleTranscriptVariant, SamplesheetSample
from web.serializers import RunSerializer, SampleListSerializer, SampleTranscriptVariantSerializer


class SampleListView(viewsets.ModelViewSet):
    serializer_class = SampleListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        section = self.kwargs['section']
        return SamplesheetSample.objects.filter(sample__section__slug=section, samplesheet__latest_run__checked=True).prefetch_related(
            *['samplesheet', 'samplesheet__runs', 'samplesheet__runs__pipeline_version']).order_by('-samplesheet__latest_run__completed_at')


class RunsAwaitingFirstCheckListView(viewsets.ModelViewSet):
    serializer_class = RunSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        section = self.kwargs['section']
        return Run.objects.filter(qc_status=0, checked=False, samplesheet__sample__section__slug=section).distinct()


class RunsAwaitingSecondCheckListView(viewsets.ModelViewSet):
    serializer_class = RunSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        section = self.kwargs['section']
        return Run.objects.filter(checked=False, samplesheet__sample__section__slug=section).exclude(qc_status=0).distinct()


class PreviousClassificationsListView(viewsets.ModelViewSet):
    serializer_class = SampleTranscriptVariantSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        stv = SampleTranscriptVariant.objects.get(id=self.kwargs['stv'])
        return SampleTranscriptVariant.objects.filter(
            sample_variant__variant=stv.sample_variant.variant).exclude(id=stv.id).exclude(comments__classification__isnull=True).order_by("comments__classification")
