import random
from tqdm import tqdm
import numpy as np
import factory
import datetime
from factory.django import DjangoModelFactory
from factory import fuzzy

from db.models import BAM, CoverageInfo, ExcelReport, Exon, ExonReport, Gene, GeneAlias, GeneReport, GenomeBuild, Patient, Pipeline, PipelineVersion, Run, Sample, SampleBAM, SampleTranscriptVariant, SampleVCF, SampleVariant, Samplesheet, SamplesheetSample, Section, Transcript, TranscriptVariant, VCF, Variant, VariantReport, VariantReportFilter, VariantReportInfo

########################
### Section creation###
########################
SECTIONS = ['Cancer', 'Rare disease']


class SectionFactory(DjangoModelFactory):
    class Meta:
        model = Section

    name = factory.Sequence(lambda n: SECTIONS[n])


########################
### Pipeline creation###
########################
PIPELINES = ['TSMP', 'TSO', 'TST170', 'test']


class PipelineFactory(DjangoModelFactory):
    class Meta:
        model = Pipeline

    name = factory.Sequence(lambda n: PIPELINES[n])


class PipelineVersionFactory(DjangoModelFactory):
    class Meta:
        model = PipelineVersion
        django_get_or_create = ('version', 'pipeline')

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


class ExonFactory(DjangoModelFactory):
    class Meta:
        model = Exon
        django_get_or_create = ('transcript', 'number')

    number = factory.LazyAttribute(lambda exon: int(
        exon.transcript.exon_set.count()) + 1)

    strand = factory.Faker(
        'random_element', elements=('f', 'r'))
    chrom = factory.LazyFunction(
        lambda: "{:d}".format(random.randint(1, 22)))
    start_pos = factory.Faker('numerify', text='%!!!!!!')
    end_pos = factory.LazyAttribute(lambda exon: int(exon.start_pos) + 1000)

    genome_build = fuzzy.FuzzyChoice(GenomeBuild.objects.all())


class TranscriptFactory(DjangoModelFactory):
    class Meta:
        model = Transcript
        django_get_or_create = ('refseq_id',)

    refseq_id = factory.LazyFunction(
        lambda: f"NM_{random.randint(1,9999):06d}.{random.randint(1,9)}")

    name = factory.LazyAttribute(lambda transcript: "transcript-{:04d}".format(int(
        transcript.gene.transcript_set.count()) + 1))

    canonical = False

    exons = factory.RelatedFactoryList(
        ExonFactory,
        factory_related_name='transcript',
        size=lambda: random.randint(1, 5))


class GeneAliasFactory(DjangoModelFactory):
    class Meta:
        model = GeneAlias

    name = factory.LazyAttribute(
        lambda alias: f"{alias.gene.hgnc_name} (alias 1)")


class GeneFactory(DjangoModelFactory):
    class Meta:
        model = Gene
        django_get_or_create = ('hgnc_id',)

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
        django_get_or_create = ('excel_report', 'gene')


class ExonReportFactory(DjangoModelFactory):
    class Meta:
        model = ExonReport
        django_get_or_create = ('excel_report', 'exon')


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
        django_get_or_create = ('path',)

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
            'random_element', elements=(1, 1, 1, 1, 1, 1, 1, 2, 2, 2)),
        checked=True)


class PatientFactory(DjangoModelFactory):
    class Meta:
        model = Patient

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class SampleFactory(DjangoModelFactory):
    class Meta:
        model = Sample
        django_get_or_create = ('lab_no',)

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
        django_get_or_create = ('chrom', 'pos', 'ref', 'alt', 'genome_build')

    ref = factory.Faker('random_element', elements=('A', 'C', 'G', 'T'))
    alt = factory.LazyAttribute(lambda alt: random.choice(
        [i for i in ['A', 'C', 'G', 'T'] if i not in alt.ref]))

    chrom = factory.LazyFunction(
        lambda: "{:d}".format(random.randint(1, 22)))
    pos = factory.Faker('numerify', text='%!!!!!!')
    genome_build = fuzzy.FuzzyChoice(GenomeBuild.objects.all())


class SampleVariantFactory(DjangoModelFactory):
    class Meta:
        model = SampleVariant
        django_get_or_create = ('sample', 'variant')

    sample = factory.SubFactory(SampleFactory)
    variant = factory.SubFactory(VariantFactory)


class TranscriptVariantFactory(DjangoModelFactory):
    class Meta:
        model = TranscriptVariant
        django_get_or_create = ('transcript', 'variant')

    hgvs_c = factory.LazyAttribute(
        lambda transcriptvariant: f"{transcriptvariant.transcript.refseq_id}:c.{random.randint(100,1500)}{transcriptvariant.variant.ref}>{transcriptvariant.variant.alt}")
    hgvs_p = factory.LazyFunction(
        lambda: f"NP_{random.randint(1,9999):06d}.{random.randint(1,9)}:p.{f'{random.randint(0,999)}'.join(map(str, random.sample(['A','B','C','D','E','F','G','H','I','K','L','M','N','P','Q','R','S','T','U','V','W','Y'],2)))}")
    # hgvs_g = factory.LazyAttribute(
    #     lambda transcriptvariant: f"NG_{random.randint(1,9999):06d}.{random.randint(1,9)}:g.{transcriptvariant.variant.variantcoordinate_set.last().coordinate.pos}{transcriptvariant.variant.ref}>{transcriptvariant.variant.alt}")


class SampleTranscriptVariantFactory(DjangoModelFactory):
    class Meta:
        model = SampleTranscriptVariant
        django_get_or_create = ('transcript', 'sample_variant')

    sample_variant = factory.SubFactory(SampleVariantFactory)
    impact = factory.Faker('random_element', elements=(
        'HIGH', 'MODERATE', 'LOW', 'MODIFIER'))
    consequence = factory.Faker('random_element', elements=(
        'missense_variant', 'stop_gained', 'frameshift_variant', 'splice_acceptor_variant', 'splice_donor_variant', 'synonymous_variant'))


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


def create_sections():
    creating = True
    while creating:
        try:
            SectionFactory.create().save()
        except Exception:
            creating = False


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


def create_variants():
    for gene in tqdm(Gene.objects.all(), 'variants in genes'):
        for transcript in Transcript.objects.filter(
                gene=gene):
            for variant in range(10):
                # variantcoordinate = VariantCoordinateFactory(coordinate__chrom=transcript.sequence.start_coord.chrom,
                #                                              coordinate__genome_build=transcript.sequence.start_coord.genome_build,
                #                                              coordinate__pos=random.randint(transcript.sequence.start_coord.pos, transcript.sequence.end_coord.pos))

                variant = VariantFactory()

                # Create a transcriptvariant
                transcriptvariant = TranscriptVariantFactory(
                    transcript=transcript, variant=variant)


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
        # Manually trigger post save after runs have been created.
        sample.save()

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
            try:
                exons = Transcript.objects.get(
                    gene=gene, canonical=True).exon_set.all()
            except:
                continue

            for exon in exons:
                exonreport = ExonReportFactory(excel_report=excelreport, exon=exon,
                                               coverage_info=CoverageInfoFactory())

            # Create a random number of variants for each transcript of each analysed gene.
            all_transcripts = Transcript.objects.filter(
                gene=gene)
            for transcript in all_transcripts:
                for variant in range(random.randint(0, 3)):

                    # # Create a variant with a coordiante that falls within current transctipt (same chrom, build and position overlapping sequence)
                    # variantcoordinate = VariantCoordinateFactory(coordinate__chrom=transcript.sequence.start_coord.chrom,
                    #                                              coordinate__genome_build=transcript.sequence.start_coord.genome_build,
                    #                                              coordinate__pos=random.randint(transcript.sequence.start_coord.pos, transcript.sequence.end_coord.pos))

                    # variant = Variant.objects.filter(
                    #     transcriptvariant__transcript=transcript).order_by('?').first()

                    variant = Variant.objects.filter(transcriptvariant__transcript=transcript).exclude(
                        id__in=SampleTranscriptVariant.objects.filter(
                            sample_variant__sample=sample).values_list('sample_variant__variant', flat=True)).order_by('?').first()

                    sample_variant = SampleVariantFactory(
                        sample=sample,
                        variant=variant)

                    if transcript.canonical:
                        SampleTranscriptVariantFactory(
                            sample_variant=sample_variant,
                            transcript=transcript,
                            selected=True)
                    else:
                        SampleTranscriptVariantFactory(
                            sample_variant=sample_variant,
                            transcript=transcript,
                            selected=False)

                    variantreport = VariantReportFactory(vcf=samplevcf.vcf,
                                                         variant=variant)

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


def create_initial_data():
    create_sections()
    create_pipelines()
    create_genome_builds()
    create_genes(100)


def create_samples():
    create_variants()
    create_samplesheets(15)
