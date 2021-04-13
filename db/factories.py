import random
from tqdm import tqdm
import numpy as np
import factory
import datetime
from factory.django import DjangoModelFactory
from factory import fuzzy

from db.models import CoverageInfo, ExcelReport, Exon, ExonReport, ExonSequence, Gene, GeneAlias, GeneReport, GenomeBuild, GenomicCoordinate, Pipeline, PipelineVersion, Run, Sample, SampleTranscriptVariant, SampleVCF, SampleVariant, Samplesheet, SamplesheetSample, Sequence, Transcript, TranscriptVariant, VCF, Variant, VariantCoordinate

########################
### Pipeline creation###
########################
PIPELINES = ['TSMP', 'TSO', 'TST170']


class PipelineFactory(DjangoModelFactory):
    class Meta:
        model = Pipeline

    name = factory.Sequence(lambda n: PIPELINES[n])


class PipelineVersionFactory(DjangoModelFactory):
    class Meta:
        model = PipelineVersion

    version = 1
    pipeline = factory.SubFactory(PipelineFactory)


#######################
### Biology creation###
#######################
BUILDS = ['GRCh37', 'GRCh38']


class GenomeBuildFactory(DjangoModelFactory):
    class Meta:
        model = GenomeBuild

    name = factory.Sequence(lambda n: BUILDS[n])
    path = factory.Faker('file_path')


class GenomicCoordinateFactory(DjangoModelFactory):
    class Meta:
        model = GenomicCoordinate

    chrom = factory.LazyFunction(
        lambda: "chr{:d}".format(random.randint(1, 22)))
    pos = factory.Faker('numerify', text='%!!!!!!')
    genome_build = fuzzy.FuzzyChoice(GenomeBuild.objects.all())


class SequenceFactory(DjangoModelFactory):
    class Meta:
        model = Sequence

    start_coord = factory.SubFactory(GenomicCoordinateFactory)
    end_coord = factory.SubFactory(
        GenomicCoordinateFactory, chrom=factory.SelfAttribute('..start_coord.chrom'), pos=factory.LazyAttribute(lambda coord: int(
            coord.factory_parent.start_coord.pos) + 1000), genome_build=factory.SelfAttribute('..start_coord.genome_build'))
    sequence = factory.Faker(
        'lexify', text='?????????????????????????????????????????????????????????????????????????????', letters='ACGT')


class ExonFactory(DjangoModelFactory):
    class Meta:
        model = Exon

    number = factory.LazyAttribute(lambda exon: int(
        exon.transcript.exon_set.count()) + 1)


class ExonSequenceFactory(DjangoModelFactory):
    class Meta:
        model = ExonSequence

    exon = factory.SubFactory(ExonFactory)
    # Ensure the sequence of each exon has the same genomebuild and chromosome value as its related transcript
    sequence = factory.SubFactory(SequenceFactory,
                                  start_coord=factory.SubFactory(GenomicCoordinateFactory,
                                                                 chrom=factory.LazyAttribute(
                                                                     lambda coord: coord.factory_parent.factory_parent.exon.transcript.sequence.start_coord.chrom),
                                                                 genome_build=factory.LazyAttribute(lambda coord: coord.factory_parent.factory_parent.exon.transcript.sequence.start_coord.genome_build)))


class ExonWithSequence(ExonFactory):
    sequence1 = factory.RelatedFactory(
        ExonSequenceFactory,
        factory_related_name='exon'
    )


class TranscriptFactory(DjangoModelFactory):
    class Meta:
        model = Transcript

    name = factory.LazyAttribute(lambda transcript: "transcript-{:04d}".format(int(
        transcript.gene.transcript_set.count()) + 1))

    # name = factory.Sequence(lambda n: 'transcript-%04d' % n)

    canonical = False

    exons = factory.RelatedFactoryList(
        ExonWithSequence,
        factory_related_name='transcript',
        size=lambda: random.randint(1, 5))

    sequence = factory.SubFactory(SequenceFactory)


class GeneAliasFactory(DjangoModelFactory):
    class Meta:
        model = GeneAlias

    name = factory.LazyAttribute(
        lambda alias: f"{alias.gene.hgnc_name} (alias 1)")


class GeneFactory(DjangoModelFactory):
    class Meta:
        model = Gene

    # ensembl_id = factory.LazyFunction(
    #     lambda: "ENSG{:11d}".format(random.randint(1, 10000000)))

    hgnc_name = factory.Faker('bothify', text='????!!',
                              letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    hgnc_id = factory.LazyFunction(
        lambda: "HGNC:{:d}".format(random.randint(1, 10000)))

    transcripts = factory.RelatedFactoryList(
        TranscriptFactory,
        factory_related_name='gene',
        size=lambda: random.randint(1, 3))

    canonical = factory.RelatedFactory(
        TranscriptFactory,
        factory_related_name='gene',
        canonical=True)

    alias = factory.RelatedFactory(
        GeneAliasFactory,
        factory_related_name='gene')

#############################################
### Sample / Samplesheet / Run generation ###
#############################################


class ExcelReportFactory(DjangoModelFactory):
    class Meta:
        model = ExcelReport

    # filename = factory.Faker('file_name', extension='xlsx', category='text')
    # path = factory.Faker('file_path', extension='xlsx', category='text')


class GeneReportFactory(DjangoModelFactory):
    class Meta:
        model = GeneReport


class ExonReportFactory(DjangoModelFactory):
    class Meta:
        model = ExonReport


class VCFFactory(DjangoModelFactory):
    class Meta:
        model = VCF


class SampleVCFFactory(DjangoModelFactory):
    class Meta:
        model = SampleVCF

    vcf = factory.SubFactory(VCFFactory)


class CoverageInfoFactory(DjangoModelFactory):
    class Meta:
        model = CoverageInfo

    cov_10x = factory.Faker('random_int', min=25000, max=50000)
    cov_20x = factory.Faker('random_int', min=20000, max=45000)
    cov_30x = factory.Faker('random_int', min=15000, max=40000)
    cov_40x = factory.Faker('random_int', min=10000, max=30000)
    cov_50x = factory.Faker('random_int', min=5000, max=20000)
    cov_100x = factory.Faker('random_int', min=0, max=15000)
    cov_min = factory.LazyAttribute(
        lambda cov_min: min([cov_min.cov_10x, cov_min.cov_20x, cov_min.cov_30x, cov_min.cov_40x, cov_min.cov_50x, cov_min.cov_100x]))
    cov_max = factory.LazyAttribute(
        lambda cov_max: max([cov_max.cov_10x, cov_max.cov_20x, cov_max.cov_30x, cov_max.cov_40x, cov_max.cov_50x, cov_max.cov_100x]))
    cov_mean = factory.LazyAttribute(
        lambda cov_mean: np.mean([cov_mean.cov_10x, cov_mean.cov_20x, cov_mean.cov_30x, cov_mean.cov_40x, cov_mean.cov_50x, cov_mean.cov_100x]))

    cov_region = factory.Faker('random_int', min=0, max=15000)
    pct_10x = factory.Faker('random_int', min=60, max=100)
    pct_20x = factory.Faker('random_int', min=60, max=100)
    pct_30x = factory.Faker('random_int', min=60, max=100)
    pct_40x = factory.Faker('random_int', min=60, max=100)
    pct_50x = factory.Faker('random_int', min=60, max=100)
    pct_100x = factory.Faker('random_int', min=60, max=100)


class RunFactory(DjangoModelFactory):
    class Meta:
        model = Run

    worksheet = factory.Faker('bothify', text='????-######')

    completed_at = factory.Faker(
        'date_between_dates',
        date_start=datetime.date(2020, 1, 1),
        date_end=datetime.date(2020, 12, 31),
    )

    pipeline_version = fuzzy.FuzzyChoice(PipelineVersion.objects.all())


class SamplesheetFactory(DjangoModelFactory):
    class Meta:
        model = Samplesheet

    path = factory.Faker('file_path')

    # run1 = factory.RelatedFactory(
    #     RunFactory,
    #     factory_related_name='samplesheet',
    #     qc_status=1
    # )

    # if factory.Faker('boolean', chance_of_getting_true=25):
    #     run2 = factory.RelatedFactory(
    #         RunFactory,
    #         factory_related_name='samplesheet',
    #         qc_status=2,
    #         completed_at=factory.Faker(
    #             'date_between_dates',
    #             date_start=datetime.date(2019, 1, 1),
    #             date_end=datetime.date(2019, 12, 31),
    #         )
    #     )

    runs = factory.RelatedFactoryList(
        RunFactory,
        factory_related_name='samplesheet',
        size=lambda: random.randint(1, 2),
        qc_status=factory.Faker(
            'random_element', elements=(0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2)))


class SampleFactory(DjangoModelFactory):
    class Meta:
        model = Sample

    lab_no = factory.Faker('bothify', text='?######', letters='GSD')


class SamplesheetSampleFactory(DjangoModelFactory):
    class Meta:
        model = SamplesheetSample

    samplesheet = factory.SubFactory(SamplesheetFactory)
    sample = factory.SubFactory(SampleFactory)
    sample_identifier = factory.Sequence(lambda n: 'sample-%04d' % n)
    gene_key = factory.Sequence(lambda n: 'genekey-%04d' % n)


class SamplesheetWith4Samples(SamplesheetFactory):
    samples = factory.RelatedFactoryList(
        SamplesheetSampleFactory,
        factory_related_name='samplesheet',
        size=4,
    )

################
### Variants ###
################


class VariantFactory(DjangoModelFactory):
    class Meta:
        model = Variant

    ref = factory.Faker('random_element', elements=('A', 'C', 'G', 'T'))
    alt = factory.LazyAttribute(lambda alt: random.choice(
        [i for i in ['A', 'C', 'G', 'T'] if i not in alt.ref]))


class VariantCoordinateFactory(DjangoModelFactory):
    class Meta:
        model = VariantCoordinate

    variant = factory.SubFactory(VariantFactory)
    coordinate = factory.SubFactory(GenomicCoordinateFactory)


class SampleVariantFactory(DjangoModelFactory):
    class Meta:
        model = SampleVariant


class TranscriptVariantFactory(DjangoModelFactory):
    class Meta:
        model = TranscriptVariant


class SampleTranscriptVariantFactory(DjangoModelFactory):
    class Meta:
        model = SampleTranscriptVariant

    sample_variant = factory.SubFactory(SampleVariantFactory)

############################
### Generation Functions ###
############################


def create_pipelines():
    creating = True
    while creating:
        try:
            PipelineVersionFactory.create().save()
        except Exception:
            creating = False


def create_genome_builds():
    creating = True
    while creating:
        try:
            GenomeBuildFactory.create().save()
        except Exception:
            creating = False


def create_genes(n):
    for i in tqdm(range(n), desc="genes"):
        GeneFactory()


def create_samplesheet():
    # Create a samplesheet with four samples on it, generate between 1-3 runs for this samplesheet.
    samplesheet = SamplesheetWith4Samples()

    # Store latest run of samplesheet
    latest_run = samplesheet.latest_run

    # Store identity of samples on samplesheet
    samples = samplesheet.sample_set.all()

    # Randomely select a set of genes to use for this samplesheet e.g. to generate coverage reports and variants
    subset_genes = Gene.objects.order_by('?')[:30]

    # For each sample on samplesheet
    for sample in tqdm(samples, desc='samples'):
        # Create an excel report
        excelreport = ExcelReportFactory(run=latest_run, sample=sample)

        # Create a vcf and link it with currently iterated sample.
        samplevcf = SampleVCFFactory(sample=sample,
                                     vcf__run=latest_run)

        print(samplevcf)
        print(samplevcf.vcf)

        # Create genereport for each gene analysised
        for gene in subset_genes:
            genereport = GeneReportFactory(excel_report=excelreport, gene=gene,
                                           coverage_info=CoverageInfoFactory())

            # Create exonreport for each exon of the canonical transcript of each gene analyised.
            exons = Transcript.objects.get(
                gene=gene, canonical=True).exon_set.all()

            for exon in exons:
                exonreport = ExonReportFactory(excel_report=excelreport, exon=exon,
                                               coverage_info=CoverageInfoFactory())

            # Create a random number of variants for each transcript of each analysed gene.
            all_transcripts = Transcript.objects.filter(
                gene=gene)
            for transcript in all_transcripts:
                for variant in range(random.randint(0, 3)):

                    # Create a variant with a coordiante that falls within current transctipt (same chrom, build and position overlapping sequence)
                    variantcoordinate = VariantCoordinateFactory(coordinate__chrom=transcript.sequence.start_coord.chrom,
                                                                 coordinate__genome_build=transcript.sequence.start_coord.genome_build,
                                                                 coordinate__pos=random.randint(transcript.sequence.start_coord.pos, transcript.sequence.end_coord.pos))

                    if transcript.canonical:
                        sampletranscriptvariant = SampleTranscriptVariantFactory(
                            sample_variant__sample=sample,
                            sample_variant__variant=variantcoordinate.variant,
                            transcript=transcript,
                            selected=True)
                    else:
                        sampletranscriptvariant = SampleTranscriptVariantFactory(
                            sample_variant__sample=sample,
                            sample_variant__variant=variantcoordinate.variant,
                            transcript=transcript,
                            selected=False)


def create_samplesheets(n):
    for i in tqdm(range(n), desc="samplesheets"):
        create_samplesheet()
