from django.db import models

from db.utils.model_utils import BaseModel
from db.utils.model_utils import PipelineOutputFileModel


class Pipeline(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


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
    output_dir = models.CharField(max_length=255)
    fastq_dir = models.CharField(max_length=255)
    interop_dir = models.CharField(max_length=255)
    pipeline_version = models.ForeignKey(
        PipelineVersion,
        on_delete=models.PROTECT,
        related_name='pipeline_version'
    )

    def __str__(self):
        return f"{self.worksheet}"


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


class Samplesheet(BaseModel):
    path = models.CharField(max_length=255)
    run = models.ForeignKey(
        Run,
        on_delete=models.PROTECT,
        related_name='run'
    )

    def __str__(self):
        return f"SampleSheet: {self.run}"


class Sample(BaseModel):
    sample_id = models.CharField(max_length=50)
    lab_no = models.CharField(max_length=50)
    index = models.CharField(max_length=50)
    index2 = models.CharField(max_length=50)
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
        return f"{self.samplesheet.run} {self.lab_no}"


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
