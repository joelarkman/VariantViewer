import factory
import datetime
from factory.django import DjangoModelFactory
from factory import fuzzy

from db.models import Pipeline, PipelineVersion, Run, Sample, Samplesheet, SamplesheetSample

PIPELINES = ['TSMP', 'TSO']


class PipelineFactory(DjangoModelFactory):
    class Meta:
        model = Pipeline

    name = factory.Sequence(lambda n: PIPELINES[n])


# Generate these first
class PipelineVersionFactory(DjangoModelFactory):
    class Meta:
        model = PipelineVersion

    version = 1
    pipeline = factory.SubFactory(PipelineFactory)


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

    run = factory.SubFactory(RunFactory)


class SampleFactory(DjangoModelFactory):
    class Meta:
        model = Sample

    sample_id = factory.Sequence(lambda n: 'sample-%04d' % n)

    lab_no = factory.Faker('bothify', text='?######', letters='GSD')


class SamplesheetSampleFactory(DjangoModelFactory):
    class Meta:
        model = SamplesheetSample

    samplesheet = factory.SubFactory(SamplesheetFactory)
    sample = factory.SubFactory(SampleFactory)


class SamplesheetWith4Samples(SamplesheetFactory):
    samples = factory.RelatedFactoryList(
        SamplesheetSampleFactory,
        factory_related_name='samplesheet',
        size=4,
    )
