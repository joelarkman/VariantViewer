from rest_framework import serializers

from db.models import Sample, SampleTranscriptVariant, Samplesheet, Run, SamplesheetSample


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
        datatables_always_serialize = ('id', 'qc_status_display',)


class SampleListSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    lab_no = serializers.SerializerMethodField()

    runs = serializers.SerializerMethodField()

    def get_first_name(self, samplesheetsample):
        return samplesheetsample.sample.patient.first_name

    def get_last_name(self, samplesheetsample):
        return samplesheetsample.sample.patient.last_name

    def get_lab_no(self, samplesheetsample):
        return samplesheetsample.sample.lab_no

    def get_runs(self, samplesheetsample):
        return RunSerializer(samplesheetsample.samplesheet.runs.all().order_by('-completed_at'), many=True).data

    class Meta:
        model = SamplesheetSample
        fields = '__all__'
        datatables_always_serialize = ('id', 'runs',)


class SampleTranscriptVariantSerializer(serializers.ModelSerializer):
    # first_name = serializers.SerializerMethodField()
    # last_name = serializers.SerializerMethodField()
    # lab_no = serializers.SerializerMethodField()
    date_classified = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    evidence_file_count = serializers.SerializerMethodField()
    classification = serializers.SerializerMethodField()
    # runs = serializers.SerializerMethodField()
    ss_samples = serializers.SerializerMethodField()

    # def get_first_name(self, stv):
    #     return stv.sample_variant.sample.patient.first_name

    # def get_last_name(self, stv):
    #     return stv.sample_variant.sample.patient.last_name

    # def get_lab_no(self, stv):
    #     return stv.sample_variant.sample.lab_no

    def get_date_classified(self, stv):
        return stv.comments.last().get_last_modified()['classification'].datetime.strftime("%Y-%m-%d")

    def get_comment(self, stv):
        return stv.comments.last().comment

    def get_evidence_file_count(self, stv):
        return stv.evidence_files.count()

    def get_classification(self, stv):
        return stv.comments.last().get_classification_display()

    # def get_runs(self, stv):
    #     vcfs = stv.sample_variant.variant.variantreport_set.filter(
    #         vcf__sample=stv.sample_variant.sample).values_list('vcf', flat=True)
    #     return RunSerializer(Run.objects.filter(vcf__in=vcfs).order_by('-completed_at'), many=True).data

    def get_ss_samples(self, stv):
        vcfs = stv.sample_variant.variant.variantreport_set.filter(
            vcf__sample=stv.sample_variant.sample).values_list('vcf', flat=True)
        return SampleListSerializer(SamplesheetSample.objects.filter(samplesheet__runs__vcf__in=vcfs, sample=stv.sample_variant.sample), many=True).data

    class Meta:
        model = SampleTranscriptVariant
        fields = '__all__'
        datatables_always_serialize = ('id',)
