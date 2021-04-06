from rest_framework import serializers

from db.models import Sample, Samplesheet, Run, SamplesheetSample


class RunSerializer(serializers.ModelSerializer):
    pipeline_name = serializers.SerializerMethodField()
    qc_status_display = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()

    def get_pipeline_name(self, run):
        return run.pipeline_version.pipeline.name

    def get_qc_status_display(self, run):
        return run.get_qc_status_display()

    def get_completed_at(self, run):
        return run.completed_at.strftime("%Y-%m-%d")

    class Meta:
        model = Run
        fields = '__all__'


class SampleListSerializer(serializers.ModelSerializer):
    lab_no = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()

    DT_Rowruns = serializers.SerializerMethodField()

    def get_lab_no(self, samplesheetsample):
        return samplesheetsample.sample.lab_no

    def get_slug(self, samplesheetsample):
        return samplesheetsample.sample.slug

    def get_DT_Rowruns(self, samplesheetsample):
        return RunSerializer(samplesheetsample.samplesheet.runs.all().order_by('-completed_at'), many=True).data

    class Meta:
        model = SamplesheetSample
        fields = '__all__'
