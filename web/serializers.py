from rest_framework import serializers

from db.models import CoverageInfo, SampleTranscriptVariant, Run, SamplesheetSample, GeneReport, ExonReport


class RunSerializer(serializers.ModelSerializer):
    pipeline_name = serializers.SerializerMethodField()
    pipeline_version = serializers.SerializerMethodField()
    qc_status_display = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()

    def get_pipeline_name(self, run):
        return str(run.pipeline_version)

    def get_pipeline_version(self, run):
        return run.pipeline_version.version

    def get_qc_status_display(self, run):
        return run.get_qc_status_display()

    def get_completed_at(self, run):
        return run.completed_at.strftime("%Y-%m-%d")

    class Meta:
        model = Run
        fields = '__all__'
        datatables_always_serialize = ('id', 'qc_status_display',)


class SampleListSerializer(serializers.ModelSerializer):
    # first_name = serializers.SerializerMethodField()
    # last_name = serializers.SerializerMethodField()
    lab_no = serializers.SerializerMethodField()

    runs = serializers.SerializerMethodField()

    # def get_first_name(self, samplesheetsample):
    #     return samplesheetsample.sample.patient.first_name

    # def get_last_name(self, samplesheetsample):
    #     return samplesheetsample.sample.patient.last_name

    def get_lab_no(self, samplesheetsample):
        return samplesheetsample.sample.lab_no

    def get_runs(self, samplesheetsample):
        return RunSerializer(samplesheetsample.samplesheet.runs.all().order_by('-completed_at'), many=True).data

    class Meta:
        model = SamplesheetSample
        fields = '__all__'
        datatables_always_serialize = ('id', 'runs',)


class GeneReportSerializer(serializers.ModelSerializer):
    gene_name = serializers.SerializerMethodField()

    def get_gene_name(self, gr):
        return gr.gene.hgnc_name

    class Meta:
        model = GeneReport
        fields = '__all__'
        datatables_always_serialize = ('id',)


class ExonReportSerializer(serializers.ModelSerializer):
    gene_name = serializers.SerializerMethodField()
    exon_number = serializers.SerializerMethodField()

    def get_gene_name(self, er):
        return er.exon.transcript.gene.hgnc_name

    def get_exon_number(self, er):
        return er.exon.number

    class Meta:
        model = ExonReport
        fields = '__all__'
        datatables_always_serialize = ('id',)


class SampleTranscriptVariantSerializer(serializers.ModelSerializer):
    date_classified = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    evidence_file_count = serializers.SerializerMethodField()
    classification = serializers.SerializerMethodField()
    classification_colour = serializers.SerializerMethodField()
    ss_samples = serializers.SerializerMethodField()

    def get_date_classified(self, stv):
        return stv.comments.last().get_last_modified()['classification'].datetime.strftime("%Y-%m-%d")

    def get_comment(self, stv):
        return stv.comments.last().comment

    def get_evidence_file_count(self, stv):
        return stv.evidence_files.exclude(archived=True).count()

    def get_classification(self, stv):
        return stv.comments.last().get_classification_display()

    def get_classification_colour(self, stv):
        return stv.comments.last().classification_colour

    def get_ss_samples(self, stv):
        vcfs = stv.sample_variant.variant.variantreport_set.filter(
            vcf__sample=stv.sample_variant.sample).values_list('vcf', flat=True)
        return SampleListSerializer(SamplesheetSample.objects.filter(samplesheet__runs__vcf__in=vcfs, sample=stv.sample_variant.sample), many=True).data

    class Meta:
        model = SampleTranscriptVariant
        fields = '__all__'
        datatables_always_serialize = ('id', 'classification_colour')
