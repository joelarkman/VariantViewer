from rest_framework import filters
from rest_framework import permissions
from rest_framework import viewsets

from db.models import Sample, Samplesheet
from web.serializers import SampleListSerializer


class SampleListView(viewsets.ModelViewSet):
    # search_fields = ('sample_id',)
    # filter_backends = (filters.SearchFilter,)
    queryset = Sample.objects.all()
    serializer_class = SampleListSerializer
    permission_classes = [permissions.AllowAny]

    # def get_options(self):
    #     return "options", {
    #         "samplesheet": [{'label': obj.pk, 'value': obj.run.worksheet} for obj in Samplesheet.objects.all()]
    #     }

    # class Meta:
    #     datatables_extra_json = ('get_options', )
