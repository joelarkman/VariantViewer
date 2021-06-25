from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from django.template.defaultfilters import slugify

from db.utils.model_utils import BaseModel
from db.utils.model_utils import PipelineOutputFileModel
from db.utils.model_utils import mode


class Section(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=50, unique=True, null=True)

    def __str__(self):
        return self.name


@receiver(pre_save, sender=Section)
def set_section_slug(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)


class Pipeline(BaseModel):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class PipelineSection(BaseModel):
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE
    )
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE
    )
    default = models.BooleanField(default=False)


class Samplesheet(BaseModel):
    path = models.CharField(max_length=255, unique=True)

    latest_run = models.ForeignKey(
        'Run',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='latest')

    def __str__(self):
        return self.path


class PipelineVersion(BaseModel):
    version = models.CharField(max_length=255)
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE
    )
    updates = models.OneToOneField(
        "PipelineVersion",
        null=True,
        on_delete=models.SET_NULL,
        related_name='updated_by'
    )

    default_filter = models.ForeignKey(
        'web.Filter',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.pipeline} {self.version}"

    class Meta:
        unique_together = ['version', 'pipeline']


class Run(BaseModel):
    # Choice field for run QC status
    class Status(models.IntegerChoices):
        PENDING = 0
        PASS = 1
        FAIL = 2

    worksheet = models.CharField(max_length=255)
    command_line_usage = models.TextField()
    completed_at = models.DateTimeField()
    samplesheet = models.ForeignKey(
        Samplesheet,
        on_delete=models.PROTECT,
        related_name='runs'
    )
    config_file = models.CharField(max_length=255)
    output_dir = models.CharField(max_length=255)
    fastq_dir = models.CharField(max_length=255)
    interop_dir = models.CharField(max_length=255)
    pipeline_version = models.ForeignKey(
        PipelineVersion,
        on_delete=models.PROTECT,
        related_name='pipeline_version'
    )
    qc_status = models.IntegerField(
        choices=Status.choices,
        default=0,
    )

    # whether run qc_status has been checked by a second user.
    checked = models.BooleanField(default=False)

    # Method to retrieve all samples associated with a run
    def get_samples(self):
        return SamplesheetSample.objects.filter(samplesheet__runs__id=self.id)

    def __str__(self):
        return f"{self.worksheet}"


# noinspection PyUnusedLocal
@receiver(post_save, sender=Run)
def set_latest_run(sender, instance, *args, **kwargs):
    # Ensure latest run is always set to the most recently completed run associated with a given samplesheet.
    instance.samplesheet.latest_run = Run.objects.filter(
        samplesheet=instance.samplesheet).order_by('-completed_at')[0]
    instance.samplesheet.save()


# noinspection PyAbstractClass
class BAM(PipelineOutputFileModel):
    pass


# noinspection PyAbstractClass
class VCF(PipelineOutputFileModel):
    filters = models.ManyToManyField(
        'web.Filter',
        through="VCFFilter"
    )


class VCFFilter(BaseModel):
    """
    Representation of filter associated with a particular VCF file.
    """
    vcf = models.ForeignKey(
        VCF,
        on_delete=models.CASCADE
    )
    filter = models.ForeignKey(
        'web.Filter',
        on_delete=models.CASCADE
    )


class GenomeBuild(BaseModel):
    name = models.CharField(max_length=255)
    path = models.TextField(unique=True, null=True)
    url = models.URLField(null=True)

    def __str__(self):
        return self.name


class Patient(BaseModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Sample(BaseModel):
    lab_no = models.CharField(max_length=50, unique=True)
    section = models.ForeignKey(
        Section,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='samples'
    )
    patient = models.ForeignKey(
        Patient,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='samples'
    )
    samplesheets = models.ManyToManyField(
        Samplesheet,
        through="SamplesheetSample"
    )
    bams = models.ManyToManyField(
        BAM,
        through="SampleBAM"
    )
    vcfs = models.ManyToManyField(
        VCF,
        through="SampleVCF"
    )

    @classmethod
    def SetSampleSection(self, sample):
        # Retrieve the set of pipelines associated with any of the sample's runs across any samplesheet the sample appears in.
        sample_pipelines = [run.pipeline_version.pipeline for samplesheet in sample.samplesheets.all(
        ) for run in samplesheet.runs.all()]

        # Retrieve the sections that have been associated with these pipelines.
        valid_pipeline_sections = PipelineSection.objects.filter(
            pipeline__in=sample_pipelines)

        if sample_pipelines and sample.section not in [pipeline_section.section for pipeline_section in valid_pipeline_sections]:
            try:
                # If only one pipeline associated with sample, find default section associated with it.
                if len(sample_pipelines) == 1:
                    default = valid_pipeline_sections.get(default=True).section
                # If multiple pipelines associated with sample, use custom mode function to
                # check if there is a mode and if so return default section associated with it.
                elif mode(sample_pipelines):
                    default = valid_pipeline_sections.get(
                        pipeline=mode(sample_pipelines), default=True).section
                # If multiple pipelines associated with sample, but no mode (e.g. each pipeline has been associated to sample an
                # equal number of times), return default section associated with the pipeline of the most recent run.
                else:
                    latest_pipeline = Run.objects.filter(
                        samplesheet__in=sample.samplesheets.all()).order_by('-completed_at')[0].pipeline_version.pipeline
                    default = valid_pipeline_sections.get(
                        pipeline=latest_pipeline, default=True).section
                sample.section = default
                sample.save()
            except PipelineSection.DoesNotExist:
                # If no default section for sample's pipeline, leave it blank.
                pass

    def __str__(self):
        return self.lab_no

    class Meta:
        indexes = [
            models.Index(fields=['lab_no'])
        ]


@receiver(post_save, sender=Sample)
def set_sample_section(sender, instance, *args, **kwargs):
    Sample.SetSampleSection(instance)


# noinspection PyAbstractClass
class ExcelReport(PipelineOutputFileModel):
    """Excel report for a patient, can relate directly to sample."""
    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE
    )


class SamplesheetSample(BaseModel):
    samplesheet = models.ForeignKey(
        Samplesheet,
        on_delete=models.PROTECT,
        related_name='samplesheet'
    )
    sample = models.ForeignKey(
        Sample,
        on_delete=models.PROTECT,
        related_name='sample'
    )
    sample_identifier = models.CharField(max_length=50)
    index = models.CharField(max_length=50)
    index2 = models.CharField(max_length=50, null=True, blank=True)
    gene_key = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.samplesheet} {self.sample_identifier}"


class SampleBAM(BaseModel):
    """
    Representation of info of a particular sample being present in a BAM file
    """
    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE
    )
    bam = models.ForeignKey(
        BAM,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.sample.lab_no} BAM: {self.bam.path.split('/')[-1]}"


class SampleVCF(BaseModel):
    """
    Representation of info of a particular sample being present in a VCF file
    """
    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE
    )
    vcf = models.ForeignKey(
        VCF,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.sample.lab_no} VCF: {self.vcf.path.split('/')[-1]}"


class Variant(BaseModel):
    """
    Representation of a change in genomic sequence irregardless of transcript,
    patient, effect, etc.
    """
    ref = models.TextField()
    alt = models.TextField()
    chrom = models.CharField(max_length=2)
    pos = models.IntegerField()

    genome_build = models.ForeignKey(
        GenomeBuild,
        on_delete=models.PROTECT
    )
    alt_build = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.chrom}:{self.pos}{self.ref}>{self.alt}"

    class Meta:
        unique_together = ['chrom', 'pos', 'ref', 'alt', 'genome_build']
        indexes = [
            models.Index(fields=['chrom', 'pos']),
        ]


class SampleVariant(BaseModel):
    """
    Representation of a particular variant in a particular sample.
    """
    sample = models.ForeignKey(
        Sample,
        on_delete=models.PROTECT,
    )
    variant = models.ForeignKey(
        Variant,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return f"{self.sample.lab_no} {str(self.variant)}"

    class Meta:
        unique_together = ['sample', 'variant']


class VariantReport(BaseModel):
    """
    Representation of a variant being reported in a VCF file, eg from a pipeline
    """
    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE,
    )
    vcf = models.ForeignKey(
        VCF,
        on_delete=models.CASCADE
    )
    # also store essential VCF info
    qual = models.IntegerField(null=True)
    filter_pass = models.BooleanField(null=True)
    depth = models.IntegerField()

    def __str__(self):
        # coords = self.variant.variantcoordinate_set
        # variant_coordinates = f"({', '.join(list(map(str, coords)))})"
        return f"{self.variant} record: {self.vcf.path}"


class VariantReportInfo(BaseModel):
    """
    Representation of a INFO column value from a VCF variant record
    """
    variant_report = models.ForeignKey(
        VariantReport,
        on_delete=models.CASCADE
    )
    tag = models.CharField(max_length=50)
    description = models.TextField()
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.variant_report} INFO: {self.tag}={self.value}"


class VariantReportFilter(BaseModel):
    """
    Representation of a FILTER tag from a VCF when variant has not passed
    """
    variant_report = models.ForeignKey(
        VariantReport,
        on_delete=models.CASCADE
    )
    tag = models.CharField(max_length=50)
    description = models.TextField()
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.variant_report} FILTER: {self.tag}={self.value}"


class Gene(BaseModel):
    hgnc_id = models.CharField(max_length=255, unique=True)
    hgnc_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.hgnc_name} (HGNC:{self.hgnc_id})"


class GeneAlias(BaseModel):
    name = models.CharField(max_length=255)
    gene = models.ForeignKey(
        Gene,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.name} ({self.gene.hgnc_name}, HGNC:{self.gene.hgnc_id})"


class Transcript(BaseModel):
    gene = models.ForeignKey(
        Gene,
        on_delete=models.PROTECT
    )
    refseq_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    canonical = models.BooleanField()

    def __str__(self):
        return f"{self.refseq_id} ({self.gene})"


class TranscriptVariant(BaseModel):
    """
    Representation of a particular variant within a particular transcript

    Includes information about the presence of the variant within that tx, ie.
    the HGVS nomenclature.
    """
    transcript = models.ForeignKey(
        Transcript,
        on_delete=models.PROTECT
    )
    variant = models.ForeignKey(
        Variant,
        on_delete=models.PROTECT
    )
    hgvs_c = models.TextField()
    hgvs_p = models.TextField()

    def __str__(self):
        return self.hgvs_c

    class Meta:
        unique_together = ['transcript', 'variant']
        indexes = [
            models.Index(fields=['transcript', 'variant'])
        ]


class SampleTranscriptVariant(BaseModel):
    """
    A particular SampleVariant (ie sample having a variant) in a particular TX

    Includes information specific to the patient, eg. effect, and whether the
    transcript is the selected one for analysis in this particular patient.
    """
    transcript = models.ForeignKey(
        Transcript,
        on_delete=models.PROTECT
    )
    sample_variant = models.ForeignKey(
        SampleVariant,
        on_delete=models.PROTECT
    )

    selected = models.BooleanField()
    pinned = models.BooleanField(default=False)

    consequence = models.CharField(max_length=255)
    impact = models.CharField(max_length=255)

    def get_short_hgvs(self):
        tv = TranscriptVariant.objects.get(
            variant=self.sample_variant.variant, transcript=self.transcript)
        long_hgvs = [i.partition(':')[2]
                     for i in [tv.hgvs_c, tv.hgvs_p]]
        short_hgvs = {
            'hgvs_c': long_hgvs[0],
            'hgvs_p': long_hgvs[1],
        }
        return short_hgvs

    def get_long_hgvs(self):
        tv = TranscriptVariant.objects.get(
            variant=self.sample_variant.variant, transcript=self.transcript)
        return {'hgvs_c': tv.hgvs_c, 'hgvs_p': tv.hgvs_p}

    def get_variant_report(self, run):
        vcf = self.sample_variant.sample.vcfs.get(run=run)
        variant = self.sample_variant.variant
        return VariantReport.objects.get(vcf=vcf, variant=variant)

    def __str__(self):
        return f"{self.sample_variant} {self.transcript}"

    class Meta:
        unique_together = ['transcript', 'sample_variant']
        indexes = [
            models.Index(fields=['transcript', 'sample_variant'])
        ]


class Exon(BaseModel):
    """
    An exon, multiple of which comprise a transcript.
    """
    number = models.CharField(max_length=4)
    transcript = models.ForeignKey(
        Transcript,
        on_delete=models.CASCADE,
    )
    strand = models.CharField(max_length=1, null=True)
    chrom = models.CharField(max_length=2, null=True)
    start_pos = models.IntegerField(null=True)
    end_pos = models.IntegerField(null=True)

    genome_build = models.ForeignKey(
        GenomeBuild,
        on_delete=models.PROTECT
    )
    alt_build = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.transcript} exon {self.number}"

    class Meta:
        unique_together = ['transcript', 'number']
        indexes = [
            models.Index(fields=['chrom', 'start_pos'])
        ]


class CoverageInfo(BaseModel):
    """Coverage report for a gene or exon."""
    cov_10x = models.IntegerField(null=True)
    cov_20x = models.IntegerField(null=True)
    cov_30x = models.IntegerField(null=True)
    cov_40x = models.IntegerField(null=True)
    cov_50x = models.IntegerField(null=True)
    cov_100x = models.IntegerField(null=True)
    cov_min = models.IntegerField(null=True)
    cov_max = models.IntegerField(null=True)
    cov_mean = models.FloatField(null=True)
    cov_region = models.IntegerField(null=True)
    pct_10x = models.IntegerField(null=True)
    pct_20x = models.IntegerField(null=True)
    pct_30x = models.IntegerField(null=True)
    pct_40x = models.IntegerField(null=True)
    pct_50x = models.IntegerField(null=True)
    pct_100x = models.IntegerField(null=True)

    def get_percentages(self):
        pct_attributes = [attr for attr in dir(self) if attr.startswith('pct')]
        pct_attribute_values = map(lambda x: getattr(self, x), pct_attributes)
        return list(pct_attribute_values)

    class Meta:
        abstract = True


class ExonReport(CoverageInfo):
    excel_report = models.ForeignKey(
        ExcelReport,
        on_delete=models.CASCADE,
    )
    exon = models.ForeignKey(
        Exon,
        on_delete=models.CASCADE,
    )
    tag = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f"{self.exon}_{self.tag} report: {self.excel_report}"

    class Meta:
        unique_together = ['excel_report', 'exon']


class GeneReport(CoverageInfo):
    excel_report = models.ForeignKey(
        ExcelReport,
        on_delete=models.CASCADE,
    )
    gene = models.ForeignKey(
        Gene,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.gene} report: {self.excel_report}"

    class Meta:
        unique_together = ['excel_report', 'gene']
