from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from django.template.defaultfilters import slugify

from db.utils.model_utils import BaseModel
from db.utils.model_utils import PipelineOutputFileModel


class Pipeline(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Samplesheet(BaseModel):
    path = models.CharField(max_length=255)

    latest_run = models.ForeignKey(
        'Run', blank=True, null=True, on_delete=models.PROTECT, related_name='latest')

    def __str__(self):
        return f"{self.path}"


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

    def __str__(self):
        return f"{self.pipeline} {self.version}"


class Run(BaseModel):
    worksheet = models.CharField(max_length=255)
    command_line_usage = models.CharField(max_length=255)
    completed_at = models.DateTimeField()
    samplesheet = models.ForeignKey(
        Samplesheet,
        on_delete=models.PROTECT,
        related_name='runs'
    )
    output_dir = models.CharField(max_length=255)
    fastq_dir = models.CharField(max_length=255)
    interop_dir = models.CharField(max_length=255)
    pipeline_version = models.ForeignKey(
        PipelineVersion,
        on_delete=models.PROTECT,
        related_name='pipeline_version'
    )

    # Choice field for run QC status
    class Status(models.IntegerChoices):
        PENDING = 0
        PASS = 1
        FAIL = 2

    qc_status = models.IntegerField(
        choices=Status.choices,
        default=0,
    )

    # Method to retrieve all samples associated with a run
    def get_samples(self):
        return SamplesheetSample.objects.filter(samplesheet__runs__id=self.id)

    def __str__(self):
        return f"{self.worksheet}"


@receiver(post_save, sender=Run)
def set_latest_run(sender, instance, *args, **kwargs):
    # Ensure latest run is always set to the most recently completed run associated with a given samplesheet.
    instance.samplesheet.latest_run = Run.objects.filter(
        samplesheet=instance.samplesheet).order_by('-completed_at')[0]
    instance.samplesheet.save()


class BAM(PipelineOutputFileModel):
    pass


class VCF(PipelineOutputFileModel):
    pass


class GenomeBuild(BaseModel):
    name = models.CharField(max_length=255)
    path = models.TextField()
    url = models.URLField()


class GenomicCoordinate(BaseModel):
    chrom = models.CharField(max_length=2)
    pos = models.IntegerField()
    genome_build = models.ForeignKey(
        GenomeBuild,
        on_delete=models.PROTECT
    )


class Sequence(BaseModel):
    strand = models.CharField(max_length=1)
    start_coord = models.ForeignKey(
        GenomicCoordinate,
        on_delete=models.PROTECT,
        related_name='sequence_starts'
    )
    end_coord = models.ForeignKey(
        GenomicCoordinate,
        on_delete=models.PROTECT,
        related_name='sequence_ends'
    )
    sequence = models.TextField(null=True, blank=True)


class Patient(BaseModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)


class Sample(BaseModel):
    slug = models.SlugField(max_length=50, unique=True)
    lab_no = models.CharField(max_length=50)
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


def __str__(self):
    # return f"{self.samplesheet.run} {self.lab_no}"

    # All samplesheets for this sample shown with comma seperating them.
    # Original version caused an error as it assumed one samplesheet per sample.
    return f"{', '.join([samplesheet.run.worksheet for samplesheet in self.samplesheets.all()])} {self.lab_no}"


# Automatically populate empty slug field with sample_id before save.
@receiver(pre_save, sender=Sample)
def set_sample_slug(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.lab_no)


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
    index2 = models.CharField(max_length=50)
    gene_key = models.CharField(max_length=50)


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


class Variant(BaseModel):
    """
    Representation of a change in genomic sequence irregardless of build,
    transcript, patient, effect, etc.
    """
    ref = models.CharField(max_length=255)
    alt = models.CharField(max_length=255)


class VariantCoordinate(BaseModel):
    """
    Linking a particular variant to a particular coordinate in a genome build.
    """
    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE,
    )
    coordinate = models.ForeignKey(
        GenomicCoordinate,
        on_delete=models.PROTECT
    )


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
    qual = models.IntegerField()
    filter_pass = models.BooleanField(null=True)
    depth = models.IntegerField()


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


class Gene(BaseModel):
    hgnc_id = models.CharField(max_length=255)
    hgnc_name = models.CharField(max_length=255)


class GeneAlias(BaseModel):
    name = models.CharField(max_length=255)
    gene = models.ForeignKey(
        Gene,
        on_delete=models.CASCADE
    )


class Transcript(BaseModel):
    gene = models.ForeignKey(
        Gene,
        on_delete=models.PROTECT
    )
    refseq_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    canonical = models.BooleanField()
    sequence = models.ForeignKey(
        Sequence,
        on_delete=models.PROTECT
    )


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
    hgvs_g = models.TextField()


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
    effect = models.CharField(max_length=255)


class Exon(BaseModel):
    """
    An exon, multiple of which comprise a transcript.
    """
    number = models.CharField(max_length=4)
    transcript = models.ForeignKey(
        Transcript,
        on_delete=models.CASCADE,
    )
    sequence = models.ManyToManyField(
        Sequence,
        through="ExonSequence"
    )


class ExonSequence(BaseModel):
    """
    Through table to enable multiple builds of an exon sequence to be stored
    """
    exon = models.ForeignKey(
        Exon,
        on_delete=models.CASCADE
    )
    sequence = models.ForeignKey(
        Sequence,
        on_delete=models.PROTECT
    )


class CoverageInfo(BaseModel):
    """Coverage report for a gene or exon."""
    cov_10x = models.IntegerField()
    cov_20x = models.IntegerField()
    cov_30x = models.IntegerField()
    cov_40x = models.IntegerField()
    cov_50x = models.IntegerField()
    cov_100x = models.IntegerField()
    cov_min = models.IntegerField()
    cov_max = models.IntegerField()
    cov_mean = models.FloatField()
    cov_region = models.IntegerField()
    pct_10x = models.IntegerField()
    pct_20x = models.IntegerField()
    pct_30x = models.IntegerField()
    pct_40x = models.IntegerField()
    pct_50x = models.IntegerField()
    pct_100x = models.IntegerField()


class ExonReport(BaseModel):
    excel_report = models.ForeignKey(
        ExcelReport,
        on_delete=models.CASCADE,
    )
    exon = models.ForeignKey(
        Exon,
        on_delete=models.CASCADE,
    )
    coverage_info = models.ForeignKey(
        CoverageInfo,
        on_delete=models.PROTECT
    )


class GeneReport(BaseModel):
    excel_report = models.ForeignKey(
        ExcelReport,
        on_delete=models.CASCADE,
    )
    gene = models.ForeignKey(
        Gene,
        on_delete=models.CASCADE,
    )
    coverage_info = models.ForeignKey(
        CoverageInfo,
        on_delete=models.PROTECT
    )
