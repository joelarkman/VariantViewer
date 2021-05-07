import random
from tqdm import tqdm
import numpy as np
import factory
import datetime
from factory.django import DjangoModelFactory
from factory import fuzzy

from db.models import BAM, CoverageInfo, ExcelReport, Exon, ExonReport, ExonSequence, Gene, GeneAlias, GeneReport, GenomeBuild, GenomicCoordinate, Patient, Pipeline, PipelineVersion, Run, Sample, SampleBAM, SampleTranscriptVariant, SampleVCF, SampleVariant, Samplesheet, SamplesheetSample, Sequence, Transcript, TranscriptVariant, VCF, Variant, VariantCoordinate, VariantReport, VariantReportFilter, VariantReportInfo

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
        lambda: "{:d}".format(random.randint(1, 22)))
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

    refseq_id = factory.LazyFunction(
        lambda: f"NM_{random.randint(1,9999):06d}.{random.randint(1,9)}")

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
        size=lambda: random.randint(2, 4))

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


class BAMFactory(DjangoModelFactory):
    class Meta:
        model = BAM


class SampleBAMFactory(DjangoModelFactory):
    class Meta:
        model = SampleBAM

    bam = factory.SubFactory(BAMFactory)


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


class PatientFactory(DjangoModelFactory):
    class Meta:
        model = Patient

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class SampleFactory(DjangoModelFactory):
    class Meta:
        model = Sample

    patient = factory.SubFactory(PatientFactory)
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

    hgvs_c = factory.LazyAttribute(
        lambda transcriptvariant: f"{transcriptvariant.transcript.refseq_id}:c.{random.randint(100,1500)}{transcriptvariant.variant.ref}>{transcriptvariant.variant.alt}")
    hgvs_p = factory.LazyFunction(
        lambda: f"NP_{random.randint(1,9999):06d}.{random.randint(1,9)}:p.{f'{random.randint(0,999)}'.join(map(str, random.sample(['A','B','C','D','E','F','G','H','I','K','L','M','N','P','Q','R','S','T','U','V','W','Y'],2)))}")
    hgvs_g = factory.LazyAttribute(
        lambda transcriptvariant: f"NG_{random.randint(1,9999):06d}.{random.randint(1,9)}:g.{transcriptvariant.variant.variantcoordinate_set.last().coordinate.pos}{transcriptvariant.variant.ref}>{transcriptvariant.variant.alt}")


class SampleTranscriptVariantFactory(DjangoModelFactory):
    class Meta:
        model = SampleTranscriptVariant

    sample_variant = factory.SubFactory(SampleVariantFactory)


class VariantReportFactory(DjangoModelFactory):
    class Meta:
        model = VariantReport

    qual = factory.Faker('random_number', digits=2)
    filter_pass = factory.Faker('boolean', chance_of_getting_true=75)
    depth = factory.Faker('random_number', digits=2)


class VariantReportInfoFactory(DjangoModelFactory):
    class Meta:
        model = VariantReportInfo


class VariantReportFilterFactory(DjangoModelFactory):
    class Meta:
        model = VariantReportFilter

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

        # Create a bam and link it with currently iterated sample.
        samplebam = SampleBAMFactory(sample=sample,
                                     bam__run=latest_run)

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
                        SampleTranscriptVariantFactory(
                            sample_variant__sample=sample,
                            sample_variant__variant=variantcoordinate.variant,
                            transcript=transcript,
                            selected=True)
                    else:
                        SampleTranscriptVariantFactory(
                            sample_variant__sample=sample,
                            sample_variant__variant=variantcoordinate.variant,
                            transcript=transcript,
                            selected=False)

                    # Create a transcriptvariant
                    transcriptvariant = TranscriptVariantFactory(
                        transcript=transcript, variant=variantcoordinate.variant)

                    variantreport = VariantReportFactory(vcf=samplevcf.vcf,
                                                         variant=variantcoordinate.variant)

                    VariantReportInfoFactory(variant_report=variantreport,
                                             tag='DP',
                                             description='Total read depth at position',
                                             value=variantreport.depth)

                    VariantReportInfoFactory(variant_report=variantreport,
                                             tag='VAF',
                                             description='Variant allele frequency',
                                             value=random.choice([factory.Faker('randomize_nb_elements', number=50), factory.Faker('randomize_nb_elements', number=100)]))

                    VariantReportInfoFactory(variant_report=variantreport,
                                             tag='TCF',
                                             description='Total forward strand coverage at this locus',
                                             value=factory.Faker('random_number', digits=3))

                    VariantReportInfoFactory(variant_report=variantreport,
                                             tag='TCR',
                                             description='Total reverse strand coverage at this locus',
                                             value=factory.Faker('random_number', digits=3))

                    VariantReportInfoFactory(variant_report=variantreport,
                                             tag='NF',
                                             description='Total number of forward reads containing this variant',
                                             value=factory.Faker('random_number', digits=3))

                    VariantReportInfoFactory(variant_report=variantreport,
                                             tag='NR',
                                             description='Total number of reverse reads containing this variant',
                                             value=factory.Faker('random_number', digits=3))

                    VariantReportInfoFactory(variant_report=variantreport,
                                             tag='example_item1',
                                             description='First example of an extra info field that has a text value',
                                             value=factory.Faker('word'))

                    VariantReportInfoFactory(variant_report=variantreport,
                                             tag='example_item2',
                                             description='Second example of an extra info field that has a text value',
                                             value=factory.Faker('word'))

                    # for info in range(random.randint(10, 25)):
                    #     VariantReportInfoFactory(variant_report=variantreport,
                    #                              tag=factory.Faker(
                    #                                  'word'),
                    #                              description=factory.Faker(
                    #                                  'words', nb=8),
                    #                              value=random.choice([factory.Faker('random_number', digits=3), factory.Faker(
                    #                                  'word')]))


def create_samplesheets(n):
    for i in tqdm(range(n), desc="samplesheets"):
        create_samplesheet()
