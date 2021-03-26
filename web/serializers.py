from rest_framework import serializers

from db.models import Sample, Samplesheet, Run


class SampleListSerializer(serializers.ModelSerializer):
    samplesheets = serializers.SerializerMethodField()

    def get_samplesheets(self, sample):
        return sample.samplesheets.last().run.worksheet

    class Meta:
        model = Sample
        fields = '__all__'
