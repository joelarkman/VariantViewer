from rest_framework import serializers

from db.models import Sample, Samplesheet, Run


class SampleListSerializer(serializers.ModelSerializer):
    samplesheets = serializers.SerializerMethodField()
    panel = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()
    qc_status = serializers.SerializerMethodField()

    def get_samplesheets(self, sample):
        return sample.samplesheets.last().run.worksheet

    def get_panel(self, sample):
        return sample.samplesheets.last().run.pipeline_version.pipeline.name

    def get_completed_at(self, sample):
        date = sample.samplesheets.last().run.completed_at
        return date.strftime("%Y-%m-%d")

    def get_qc_status(self, sample):
        return sample.samplesheets.last().run.get_qc_status_display()

    class Meta:
        model = Sample
        fields = '__all__'
