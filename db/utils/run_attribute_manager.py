import re

from sample_sheet import SampleSheet

from db.models import *
from db.utils.run_builder import RunBuilder
from db.utils.run_model import RunModel
from db.utils.run_model import ManyRunModel


class RunAttributeManager:
    def __init__(self, run: RunBuilder, model_type, instances, many=False):
        """
        Args:
            run (object): the RunBuilder for which this object holds data
            model_type:  the db table to which the held data corresponds
            instances: pre-existing db records for this model_type
        """
        self.run = run
        self.model_type = model_type
        self.instances = instances
        self.many=many
        # noinspection PyProtectedMember
        model_str = model_type._meta.verbose_name.replace(' ', '_')

        # create a delegate function for parsing the correct data for type
        get_model_attrs = getattr(self, model_str)

        # create a dictionary of data values from the model
        # model used purely for field validation, we need a dict for later
        if not many:
            model_attrs = get_model_attrs().__dict__
            # model instances have a dict value '_state', remove to instantiate
            model_attrs.pop('_state')
            run_model = RunModel(model_type, model_attrs, instances)
        else:
            model_attrs_list = [model.__dict__ for model in get_model_attrs()]
            map(lambda x: x.pop('_state'), model_attrs_list)
            run_model = ManyRunModel(model_type, model_attrs_list, instances)

        self.run_model = run_model

    def get_related_instance(self, model_type, many=False):
        """Fetch the run's nascent instance(s) of given model type"""
        attribute_manager = self.run.attribute_managers[model_type]
        if not many:
            return attribute_manager.run_model.entry
        else:
            return attribute_manager.run_model.entry_list()

    def get_all_instances(self, model_type):
        """Fetch all current instances of a given model type"""
        attribute_manager = self.run.attribute_managers[model_type]
        return attribute_manager.instances

    def get_pipeline(self):
        return Pipeline(
            name=self.run.pipeline
        )

    def get_pipeline_version(self):
        # TODO: add checks for updated/updates at the end of MCA
        return PipelineVersion(
            version=self.run.version,
            pipeline=self.get_related_instance(Pipeline),
        )

    def get_samplesheet(self):
        # TODO: resolve latest_run issue
        return Samplesheet(
            path=self.run.samplesheet
        )

    def get_run(self):
        return Run(
            worksheet=self.run.worksheet,
            command_line_usage=self.run.commandline_usage,
            completed_at=self.run.completed_at,
            output_dir=self.run.output_dir,
            fastq_dir=self.run.fastq_dir,
            interop_dir=self.run.interop_dir,
            pipeline_version=self.get_related_instance(PipelineVersion)
        )


    def get_sample(self):
        """Since there are many samples per run, we must return a list"""
        samplesheet_file = self.run.samplesheet
        samplesheet = SampleSheet(samplesheet_file)

        # compile a regex search string for lab number
        lab_no_pattern = re.compile(r'D\d{2}\.\d{5}')

        samples = []
        for sample in samplesheet.samples:
            # ignore negative controls
            if "Neg" in sample['Sample_Name']: continue
            lab_no = lab_no_pattern.search(sample['Sample_Name'])
            samples.append(
                Sample(
                    lab_no=lab_no,
                    slug=slugify(lab_no)
                )
            )

        return samples

    def get_samplesheet_sample(self):
        pass

    def get_bam(self):
        pass

    def get_sample_bam(self):
        pass

    def get_vcf(self):
        pass

    def get_sample_vcf(self):
        pass

    def get_variant(self):
        pass

    def get_sample_variant(self):
        pass

    def get_gene(self):
        pass

    def get_transcript(self):
        pass

    def get_exon(self):
        pass

    def get_coverage_info(self):
        pass

    def get_exon_report(self):
        pass

    def get_gene_report(self):
        pass

    def get_genome_build(self):
        pass

    def get_genomic_coordinate(self):
        pass

    def get_sequence(self):
        pass

    def get_exon_sequence(self):
        pass

    def get_variant_coordinate(self):
        pass

    def get_transcript_variant(self):
        pass

    def get_sample_transcript_variant(self):
        pass

    def get_variant_report(self):
        pass

    def get_variant_report_info(self):
        pass